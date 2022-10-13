class Specs:
    def __init__(self, **kwargs) -> None:
        self._cpu = kwargs["cpu"] if "cpu" in kwargs else None
        self._memory = kwargs["memory"] if "memory" in kwargs else None
        self.storage = kwargs["storage"] if "storage" in kwargs else None

    def __str__(self) -> str:
        return f"[{self.specs.cpu}, {self.specs.memory}, {self.specs.storage}]"

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

    def increase_specs_by(self, extra_specs):
        self.cpu += extra_specs.cpu
        self.memory += extra_specs.memory
        self.storage += extra_specs.storage

    def decrease_specs_by(self, decreased_specs):
        self.cpu -= decreased_specs.cpu
        self.memory -= decreased_specs.memory
        self.storage -= decreased_specs.storage

    def increase_cpu_by(self, extra_cpu):
        self.cpu += extra_cpu

    def decrease_cpu_by(self, decreased_cpu):
        self.cpu -= decreased_cpu

    def increase_memory_by(self, extra_memory):
        self.memory += extra_memory

    def decrease_memory_by(self, decreased_memory):
        self.memory -= decreased_memory

    def increase_storage_by(self, extra_storage):
        self.storage += extra_storage

    def decrease_storage_by(self, decreased_storage):
        self.storage -= decreased_storage
