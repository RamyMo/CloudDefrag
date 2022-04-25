from abc import ABC

from CloudDefrag.Model.Graph.Specs import Specs


class VNFRequirement:
    def __init__(self, **kwargs) -> None:
        self._specs = kwargs["specs"] if "specs" in kwargs else None
        self._processing_delay = kwargs["processing_delay"] if "processing_delay" in kwargs else None

    @property
    def specs(self) -> Specs:
        return self._specs

    @specs.setter
    def specs(self, value: Specs):
        self._specs = value

    @property
    def processing_delay(self) -> float:
        return self._processing_delay

    @processing_delay.setter
    def processing_delay(self, value: float):
        self._processing_delay = value


class SCRequirement:
    def __init__(self, **kwargs) -> None:
        self._e2e_delay = kwargs["e2e_delay"] if "e2e_delay" in kwargs else None
        self._gateway_router = kwargs["gateway_router"] if "gateway_router" in kwargs else None

    @property
    def e2e_delay(self) -> float:
        return self._e2e_delay

    @e2e_delay.setter
    def e2e_delay(self, value: float):
        self._e2e_delay = value

    @property
    def gateway_router(self):
        return self._gateway_router

    @gateway_router.setter
    def gateway_router(self, value):
        self._gateway_router = value
