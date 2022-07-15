import csv
from typing import List

from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import PhysicalLink, LinkSpecs, VirtualLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, Router, DummyVirtualMachine, VirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs


class OutputParser:
    def __init__(self, net: PhysicalNetwork, hosted_requests: List[HostedVMRequest],
                 new_requests: List[NewVMRequest], **kwargs) -> None:

        # Parse Network Nodes and Connections
        self._net = net
        self.__assignments_file_name = "output/RequestsAssignment/Assignments.CSV"
        self.hosted_requests = hosted_requests
        self.new_requests = new_requests

    def parse_request_assignments(self):
        file_name = self.__assignments_file_name
        hosted_requests = self.hosted_requests
        new_requests = self.new_requests

        with open(file_name, "w") as file:
            field_names = ["Request ID", "Hosted or New", "Name", "VM or vLink?", "Source", "Target", "Host"]
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()

            for hosted_request in hosted_requests:
                request_id = hosted_request.request_id
                virtual_net = hosted_request.vm_net
                vms = virtual_net.get_vms()
                vlinks = virtual_net.get_links()
                if isinstance(hosted_request, HostedVMRequest):
                    hosted_or_new = "hosted"
                else:
                    hosted_or_new = "new"

                for vm in vms:
                    vm_or_vLink = "VM"
                    source = "NA"
                    target = "NA"
                    name = vm.node_name
                    if isinstance(vm, DummyVirtualMachine):
                        host = vm.gateway_router
                    else:
                        host = vm.host_server.node_name
                    writer.writerow({"Request ID": request_id, "Hosted or New": hosted_or_new, "Name": name,
                                     "VM or vLink?": vm_or_vLink, "Source": source, "Target": target, "Host": host})
                for vlink in vlinks:
                    vm_or_vLink = "vLink"
                    source = vlink.source.node_name
                    target = vlink.target.node_name
                    name = vlink.name
                    host = ""
                    for pl in vlink.hosting_physical_links:
                        host += pl.name
                        host += "\n"
                    writer.writerow({"Request ID": request_id, "Hosted or New": hosted_or_new, "Name": name,
                                     "VM or vLink?": vm_or_vLink, "Source": source, "Target": target, "Host": host})
            for new_request in new_requests:
                request_id = new_request.request_id
                virtual_net = new_request.vm_net
                vms = virtual_net.get_vms()
                vlinks = virtual_net.get_links()
                if isinstance(new_request, HostedVMRequest):
                    hosted_or_new = "hosted"
                else:
                    hosted_or_new = "new"

                for vm in vms:
                    vm_or_vLink = "VM"
                    source = "NA"
                    target = "NA"
                    name = vm.node_name
                    if isinstance(vm, DummyVirtualMachine):
                        host = vm.gateway_router
                    else:
                        host = vm.host_server.node_name
                    writer.writerow({"Request ID": request_id, "Hosted or New": hosted_or_new, "Name": name,
                                     "VM or vLink?": vm_or_vLink, "Source": source, "Target": target, "Host": host})
                for vlink in vlinks:
                    vm_or_vLink = "vLink"
                    source = vlink.source.node_name
                    target = vlink.target.node_name
                    name = vlink.name
                    host = ""
                    for pl in vlink.hosting_physical_links:
                        host += pl.name
                        host += "\n"
                    writer.writerow({"Request ID": request_id, "Hosted or New": hosted_or_new, "Name": name,
                                     "VM or vLink?": vm_or_vLink, "Source": source, "Target": target, "Host": host})

    def parse_net_snapshot(self, **kwargs):
        nodes_file_name = kwargs[
            "nodes_file_name"] if "nodes_file_name" in kwargs else "output/NetSnapShot/NetworkNodesSnapShot.csv"
        links_file_name = kwargs[
            "links_file_name"] if "links_file_name" in kwargs else "output/NetSnapShot/NetworkConnectionsSnapShot.csv"
        self.parse_net_nodes_snapshot(nodes_file_name)
        self.parse_net_links_snapshot(links_file_name)

    def parse_net_nodes_snapshot(self, file_name):
        with open(file_name, "w") as file:
            field_names = ["Name", "Label", "CPU core", "RAM GB", "Storage GB", "isGateway?", "Node Score"]
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()

            for node in self._net.nodes:
                if isinstance(node, Server):
                    node_score = node.node_score
                else:
                    node_score = 0
                name = node.node_name
                label = node.node_label
                CPU = 0
                RAM = 0
                DISK = 0
                isGateway = False
                if isinstance(node, Server):
                    specs = node.available_specs
                    CPU = specs.cpu
                    RAM = specs.memory
                    DISK = specs.storage
                elif isinstance(node, Router):
                    if node.is_gateway:
                        isGateway = True
                writer.writerow({"Name": name, "Label": label, "CPU core": CPU, "RAM GB": RAM, "Storage GB": DISK
                                    , "isGateway?": isGateway, "Node Score": node_score})
            writer.writerow({"Name": "Compute Index", "Label": self._net.compute_index, "CPU core": 0, "RAM GB": 0, "Storage GB": 0
                                , "isGateway?": 0, "Node Score": 0})
    def parse_net_links_snapshot(self, file_name):
        with open(file_name, "w") as file:
            field_names = ["Source", "Target", "B.W (Mbps)", "Propagation Delay (µs)", "Link Score"]
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()

            for link in self._net.network_edges:
                link_score = link.link_score
                source = link.source
                target = link.target
                linkspecs = link.link_specs
                bw = linkspecs.available_bandwidth
                prp_delay = linkspecs.propagation_delay
                writer.writerow({
                    "Source": source, "Target": target, "B.W (Mbps)": bw, "Propagation Delay (µs)": prp_delay,
                    "Link Score": link_score})
            writer.writerow({
                "Source": "Communication Index", "Target": self._net.communication_index, "B.W (Mbps)": 0, "Propagation Delay (µs)": 0,
                "Link Score": 0})