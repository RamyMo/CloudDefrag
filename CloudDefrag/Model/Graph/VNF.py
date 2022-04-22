from CloudDefrag.Model.Graph.Requirement import VNFRequirement


class VNF:

    def __init__(self, **kwargs):
        self._vnf_name = kwargs["vnf_name"] if "vnf_name" in kwargs else None
        self._vnf_requirement = kwargs["vnf_requirement"] if "vnf_requirement" in kwargs else None
        self._vnf_host = kwargs["vnf_host"] if "vnf_host" in kwargs else None

    def __str__(self) -> str:
        return self._vnf_name

    @property
    def vnf_name(self) -> str:
        return self._vnf_name

    @vnf_name.setter
    def vnf_name(self, value: str):
        self._vnf_name = value

    @property
    def vnf_requirement(self) -> VNFRequirement:
        return self._vnf_requirement

    @vnf_requirement.setter
    def vnf_requirement(self, value: VNFRequirement):
        self._vnf_requirement = value

    @property
    def vnf_host(self):
        return self._vnf_host

    @vnf_host.setter
    def vnf_host(self, value):
        self._vnf_host = value

