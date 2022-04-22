class Specs:
    def __init__(self, **kwargs) -> None:
        self._cpu = kwargs["cpu"] if "cpu" in kwargs else None
        self._memory = kwargs["memory"] if "memory" in kwargs else None
        self.storage = kwargs["storage"] if "storage" in kwargs else None

    @property
    def cpu(self) -> int:
        return self._cpu

    @cpu.setter
    def cpu(self, value: int):
        self._cpu = value

    @cpu.deleter
    def cpu(self):
        del self._cpu

    @property
    def memory(self) -> int:
        return self._memory

    @memory.setter
    def memory(self, value: int):
        self._memory = value

    @memory.deleter
    def memory(self):
        del self._memory

    @property
    def storage(self) -> int:
        return self._storage

    @storage.setter
    def storage(self, value: int):
        self._storage = value

    @storage.deleter
    def storage(self):
        del self._storage
