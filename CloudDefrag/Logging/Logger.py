import logging

logging.basicConfig(filename="output/log.log",
                    format='%(asctime)s %(name)-30s %(levelname)-8s %(message)s',
                    filemode='w')


class Logger(logging.getLoggerClass()):
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    @classmethod
    def log_available_resources_info(cls, server):
        cls.log.info(f"Available resources at Server {server.node_name}:  [CPUs: {server.available_specs.cpu},"
                     f" Memory: {server.available_specs.memory}(GBs),"
                     f" Storage: {server.available_specs.storage}(GBs)]")

    @classmethod
    def log_available_resources_warning(cls, server):
        cls.log.warning(f"Available resources at Server {server.node_name}:  [CPUs: {server.available_specs.cpu},"
                        f" Memory: {server.available_specs.memory}(GBs),"
                        f" Storage: {server.available_specs.storage}(GBs)]")

    @classmethod
    def log_server_cannot_host_vm_resources_warning(cls, server, vm):
        Logger.log.warning(f"Can't Host: Server {server.node_name} [CPUs: {server.available_specs.cpu},"
                           f" Memory: {server.available_specs.memory}(GBs),"
                           f" Storage: {server.available_specs.storage}(GBs)] doesn't have enough resources to host "
                           f"Virtual Machine" f" {vm.node_name} Requires: [CPUs: {vm.specs.cpu},"
                           f" Memory: {vm.specs.memory}(GBs), Storage: {vm.specs.storage}(GBs)]")

    @classmethod
    def log_vm_resources_requirement_info(cls, vm):
        cls.log.info(f"Virtual Machine" f" {vm.node_name} Requires: [CPUs: {vm.specs.cpu},"
                     f" Memory: {vm.specs.memory}(GBs), Storage: {vm.specs.storage}(GBs)]")
