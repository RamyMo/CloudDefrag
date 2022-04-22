from abc import ABC, abstractmethod


class LinkSpecs:

    def __init__(self, **kwargs) -> None:
        self._bandwidth = kwargs["bandwidth"] if "bandwidth" in kwargs else None
        self._propagation_delay = kwargs["propagation_delay"] if "propagation_delay" in kwargs else None

    @property
    def bandwidth(self) -> float:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value: float):
        self._bandwidth = value

    @property
    def propagation_delay(self) -> float:
        return self._propagation_delay

    @propagation_delay.setter
    def propagation_delay(self, value: float):
        self._propagation_delay = value


class Link(ABC):

    def __init__(self, **kwargs):
        self._link_specs = kwargs["link_specs"] if "link_specs" in kwargs else None
        self._source = kwargs["source"] if "source" in kwargs else None
        self._target = kwargs["target"] if "target" in kwargs else None

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


class PhysicalLink(Link):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hosted_virtual_links = kwargs["hosted_virtual_links"] if "hosted_virtual_links" in kwargs else []

    @property
    def hosted_virtual_links(self) -> list:
        return self._hosted_virtual_links

    @hosted_virtual_links.setter
    def hosted_virtual_links(self, value: list):
        self._hosted_virtual_links = value

    def add_virtual_link(self, value):
        self._hosted_virtual_links.append(value)

    def remove_virtual_link(self, value):
        self._hosted_virtual_links.remove(value)


class VirtualLink(Link):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hosting_physical_links = kwargs["hosting_physical_links"] if "hosting_physical_links" in kwargs else []

    def __str__(self) -> str:
        return str(self._source) + " => " + str(self._target)

    @property
    def hosting_physical_links(self):
        return self._hosting_physical_links

    @hosting_physical_links.setter
    def hosting_physical_links(self, value):
        self._hosting_physical_links = value

    def add_hosting_physical_link(self, value):
        self._hosting_physical_links.append(value)

    def remove_hosting_physical_link(self, value):
        self._hosting_physical_links.remove(value)
