import math
from abc import ABC, abstractmethod

from CloudDefrag.Logging.Logger import Logger


class LinkSpecs:

    def __init__(self, **kwargs) -> None:
        self._bandwidth = kwargs["bandwidth"] if "bandwidth" in kwargs else None
        self._propagation_delay = kwargs["propagation_delay"] if "propagation_delay" in kwargs else None
        self._available_bandwidth = self._bandwidth
        self._used_bandwidth = 0

    def __str__(self) -> str:
        return f"BW = {self._bandwidth}, Prop. Delay = {self._propagation_delay}"

    @property
    def bandwidth(self) -> float:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value: float):
        self._bandwidth = value

    @property
    def available_bandwidth(self):
        return self._available_bandwidth

    @property
    def used_bandwidth(self):
        return self._used_bandwidth

    @property
    def propagation_delay(self) -> float:
        return self._propagation_delay

    @propagation_delay.setter
    def propagation_delay(self, value: float):
        self._propagation_delay = value

    def increase_propagation_delay_by(self, added_delay):
        # Propagation Delay (µs)
        self.propagation_delay += added_delay
        return self.propagation_delay

    def increase_used_bandwidth_by(self, bw):
        self._used_bandwidth += bw
        self._available_bandwidth -= bw

    def decrease_used_bandwidth_by(self, bw):
        self._used_bandwidth -= bw
        self._available_bandwidth += bw

    def increase_bandwidth_by(self, bw):
        self._bandwidth += bw
        self._available_bandwidth = self._bandwidth

    def decrease_bandwidth_by(self, bw):
        self._bandwidth -= bw
        self._available_bandwidth = self._bandwidth

class Link(ABC):

    def __init__(self, **kwargs):
        self._link_specs = kwargs["link_specs"] if "link_specs" in kwargs else None
        self._source = kwargs["source"] if "source" in kwargs else None
        self._target = kwargs["target"] if "target" in kwargs else None
        self._weight = kwargs["weight"] if "weight" in kwargs else None
        self._weight = kwargs["link_score"] if "link_score" in kwargs else None
        self._is_selected_for_feas_repair = False  # True if the link is selected by feas repair method
        self._link_repair_specs = LinkSpecs(bandwidth=0, propagation_delay=0)
    def __str__(self) -> str:
        return f"Link {self._source} to {self._target}"

    @property
    def weight(self):
        return self._weight

    @property
    def link_score(self):
        used_bw = self.link_specs.used_bandwidth
        total_bw = self.link_specs.bandwidth
        score = math.ceil(used_bw * 100 / total_bw)
        return score

    # Name of the links as ("source", "target")
    @property
    def name(self):
        return f"({self._source},{self._target})"

    # Name of the links as ("target", "source")
    @property
    def reverse_name(self):
        return f"({self._target},{self._source})"

    @property
    def name_tuple(self):
        name_as_tuple = (self._source.node_name, self._target.node_name)
        return name_as_tuple

    @property
    def link_specs(self) -> LinkSpecs:
        return self._link_specs

    @link_specs.setter
    def link_specs(self, value: LinkSpecs):
        self._link_specs = value

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        self._source = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def is_selected_for_feas_repair(self):
        return self._is_selected_for_feas_repair

    @is_selected_for_feas_repair.setter
    def is_selected_for_feas_repair(self, value):
        self._is_selected_for_feas_repair = value

    @property
    def link_repair_specs(self):
        return self._link_repair_specs

    @link_repair_specs.setter
    def link_repair_specs(self, value):
        self._link_repair_specs = value


class PhysicalLink(Link):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hosted_virtual_links = kwargs["hosted_virtual_links"] if "hosted_virtual_links" in kwargs else []
        self._weight = kwargs["weight"] if "weight" in kwargs else 0.0
        self._link_cost_coefficient = kwargs["link_cost_coefficient"] if "link_cost_coefficient" in kwargs else 1.0
        self._bw_constrs = None
        Logger.log.info(f"Created a Physical Link from {self.source} to {self.target}")

    @property
    def bw_constrs(self):
        return self._bw_constrs

    @bw_constrs.setter
    def bw_constrs(self, value):
        self._bw_constrs = value

    @property
    def hosted_virtual_links(self) -> list:
        return self._hosted_virtual_links

    @property
    def weight(self) -> float:
        return self._weight

    @weight.setter
    def weight(self, value: float):
        self._weight = value

    @property
    def link_cost_coefficient(self):
        return self._link_cost_coefficient

    @link_cost_coefficient.setter
    def link_cost_coefficient(self, value):
        self._link_cost_coefficient = value

    def add_virtual_link(self, vLink: Link):
        virtual_link_bw = vLink.link_specs.bandwidth
        virtual_link_prob_delay = vLink.link_specs.propagation_delay
        if vLink in self.hosted_virtual_links:
            Logger.log.warning(f"Virtual Link {vLink.name} was already added to Physical Link {self.name} before.")
            return
        else:
            # Physical Link can host
            if self.link_specs.bandwidth >= virtual_link_bw and self.link_specs.propagation_delay <= \
                    virtual_link_prob_delay:
                self._hosted_virtual_links.append(vLink)
                self.link_specs.increase_used_bandwidth_by(virtual_link_bw)
                Logger.log.info(f"Virtual Link {vLink.name} is added to Physical Link {self.name}")

                Logger.log.info(f"Available resources at Physical Link {self.name}: B.W = {self.link_specs.available_bandwidth}"
                                f" MBs, Prop. Delay = {self.link_specs.propagation_delay} s")
                return
            # Physical Link cannot host
            elif self.link_specs.bandwidth < virtual_link_bw:
                Logger.log.warning(f"Virtual Link {vLink.name} can't be added to Physical Link {self.name}. "
                                   f"Not enough BW")
            else:
                Logger.log.warning(f"Virtual Link {vLink.name} can't be added to Physical Link {self.name} "
                                   f"because of Propagation Delay")

    def remove_virtual_link(self, vLink):
        virtual_link_bw = vLink.link_specs.bandwidth
        if vLink in self.hosted_virtual_links:
            self._hosted_virtual_links.remove(vLink)
            self.link_specs.decrease_used_bandwidth_by(virtual_link_bw)
            Logger.log.info(f"Virtual Link {vLink.name} is removed from Physical Link {self.name}.")
            Logger.log.info(f"Available resources at Physical Link {self.name}: B.W = {self.link_specs.bandwidth}"
                            f" MBs, Prop. Delay = {self.link_specs.propagation_delay} s")
        else:
            Logger.log.warning(f"Virtual Link {vLink.name} is not hosted by Physical Link {self.name}.")


class VirtualLink(Link):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hosting_physical_links = kwargs["hosting_physical_links"] if "hosting_physical_links" in kwargs else []
        self._vlink_migration_coeff = kwargs["vlink_migration_coeff"] if "vlink_migration_coeff" in kwargs else 10.0
        self._vlink_revenue_coeff = kwargs["vlink_revenue_coeff"] if "vlink_revenue_coeff" in kwargs else 1.0
        self._prop_delay_req_constr = None
        Logger.log.info(f"Created a Virtual Link from {self.source} to {self.target}")

    @property
    def prop_delay_req_constr(self):
        return self._prop_delay_req_constr

    @prop_delay_req_constr.setter
    def prop_delay_req_constr(self, value):
        self._prop_delay_req_constr = value

    @property
    def vlink_migration_coeff(self: float):
        return self._vlink_migration_coeff

    @vlink_migration_coeff.setter
    def vlink_migration_coeff(self, value: float):
        self._vlink_migration_coeff = value

    @property
    def vlink_revenue_coeff(self):
        return self._vlink_revenue_coeff

    @vlink_revenue_coeff.setter
    def vlink_revenue_coeff(self, value):
        self._vlink_revenue_coeff = value

    @property
    def hosting_physical_links(self):
        return self._hosting_physical_links

    def add_hosting_physical_link(self, physical_link: PhysicalLink):
        avail_bw = physical_link.link_specs.available_bandwidth
        req_bw = self.link_specs.bandwidth
        avail_prop_delay = physical_link.link_specs.propagation_delay
        req_prop_delay = self.link_specs.propagation_delay
        if physical_link in self.hosting_physical_links:
            Logger.log.warning(f"Physical Link {physical_link.name} already hosts Virtual Link {self.name}.")
            return
        else:
            # Physical Link can host
            if avail_bw >= req_bw and avail_prop_delay <= req_prop_delay:
                self._hosting_physical_links.append(physical_link)
                physical_link.add_virtual_link(self)
                return
            # Physical Link cannot host
            elif avail_bw < req_bw:
                Logger.log.warning(f"Virtual Link {self.name} can't be added to Physical Link {physical_link.name}. "
                                   f"Not enough BW")
            else:
                Logger.log.warning(f"Virtual Link {self.name} can't be added to Physical Link {physical_link.name} "
                                   f"because of Propagation Delay")

    def remove_hosting_physical_link(self, physical_link: PhysicalLink):
        if physical_link in self.hosting_physical_links:
            self._hosting_physical_links.remove(physical_link)
            physical_link.remove_virtual_link(self)
        else:
            Logger.log.warning(f"Virtual Link {self.name} is not hosted by Physical Link {physical_link.name}.")