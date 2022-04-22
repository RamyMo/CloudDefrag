from CloudDefrag.Model.Graph.EnhancedGraph import EnhancedGraph
from CloudDefrag.Model.Graph.Link import VirtualLink
from CloudDefrag.Model.Graph.Requirement import SCRequirement
from CloudDefrag.Model.Graph.VNF import VNF


class ServiceChain(EnhancedGraph):

    def __init__(self, incoming_graph_data=None, **kwargs):
        super().__init__(incoming_graph_data, **kwargs)
        self._vnfs = kwargs["vnfs"] if "vnfs" in kwargs else []
        self._virtual_links = kwargs["virtual_links"] if "virtual_links" in kwargs else []
        self._service_chain_requirement = kwargs["service_chain_requirement"] if "service_chain_requirement" in kwargs \
            else None

    @property
    def vnfs(self):
        return self._vnfs

    def add_vnf(self, vnf: VNF, **kwargs) -> None:
        self._vnfs.append(vnf)
        self.add_node(vnf, **kwargs)

    @property
    def service_chain_requirement(self) -> SCRequirement:
        return self._service_chain_requirement

    @service_chain_requirement.setter
    def service_chain_requirement(self, value: SCRequirement):
        self._service_chain_requirement = value

    @property
    def virtual_links(self):
        return self._virtual_links

    @virtual_links.setter
    def virtual_links(self, value):
        self._virtual_links = value

    def add_virtual_link(self, virtual_link: VirtualLink, **kwargs):
        self._virtual_links.append(virtual_link)
        self.add_edge(virtual_link.source, virtual_link.target, object=virtual_link)
