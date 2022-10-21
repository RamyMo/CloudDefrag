import csv
from typing import List

from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import PhysicalLink, LinkSpecs, VirtualLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, Router, DummyVirtualMachine, VirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
from random import seed
from random import randint

class InputParser:
    def __init__(self, net: PhysicalNetwork, **kwargs) -> None:

        # Parse Network Nodes and Connections
        self._net = net
        self._network_nodes_file = kwargs["network_nodes_file"] if "network_nodes_file" in kwargs else \
            "input/01-NetworkNodes.csv"
        self._network_connections_file = kwargs["network_connections_file"] if "network_connections_file" in kwargs \
            else "input/02-NetworkConnections.csv"
        self.__parse_network_files()

        self._requests_nodes_file = kwargs["requests_nodes_file"] if "requests_nodes_file" in kwargs else \
            "input/Requests/Nodes.CSV"
        self._requests_links_file = kwargs["requests_links_file"] if "requests_links_file" in kwargs else \
            "input/Requests/Links.CSV"
        self._requests_e2e_file = kwargs["requests_e2e_file"] if "requests_e2e_file" in kwargs else \
            "input/Requests/E2E.CSV"
        self._new_requests_dist_file = kwargs["new_requests_dist_file"] if "new_requests_dist_file" in kwargs else \
            "input/NewRequests/RequestsDist.CSV"
        self._hosted_requests_dist_file = kwargs[
            "hosted_requests_dist_file"] if "hosted_requests_dist_file" in kwargs else \
            "input/HostedRequests/RequestsDist.CSV"
        self._new_requests = None
        self._hosted_requests = None

    def __parse_network_files(self):
        self.__parse_network_nodes()
        self.__parse_network_connections()

    def __parse_network_nodes(self):
        net = self._net
        network_nodes_file = self._network_nodes_file
        with open(network_nodes_file, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                name = row["Name"]
                label = row["Label"]
                type = row["Type"]
                cpu = int(row["CPU core"])
                memory = int(row["RAM GB"])
                storage = int(row["Storage GB"])
                is_gateway = bool(int(row["isGateway?"]))
                weight = int(row["Weight"])

                if type == "Server":
                    self.__parse_server(name, label, cpu, memory, storage, weight)
                elif type == "Router":
                    self.__parse_router(name, label, is_gateway)

    def __parse_server(self, name: str, label: str, cpu: int, memory: int, storage: int, weight: int):
        net = self._net
        s = Server(specs=Specs(cpu=cpu, memory=memory, storage=storage), node_name=name, node_label=label,
                   weight=weight)
        net.add_network_node(s, name=name, label=label, color="gold")

    def __parse_router(self, name: str, label: str, is_gateway: bool):
        net = self._net
        w = Router(node_name=name, node_label=label, is_gateway=is_gateway, weight=0)
        if is_gateway:
            net.add_network_node(w, name=name, label=label, color="lightskyblue")
        else:
            net.add_network_node(w, name=name, label=label, color="blue")

    def __parse_network_connections(self):
        net = self._net
        network_connections_file = self._network_connections_file
        net_dict = net.get_node_dict()
        with open(network_connections_file, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                weight = int(row["Weight"])
                source = row["Source"]
                target = row["Target"]
                bw = int(row["B.W (Mbps)"])
                prop_delay = float(row["Propagation Delay (µs)"]) * (10 ** -6)
                n1 = net_dict[source]
                n2 = net_dict[target]
                pl = net.add_network_edge(PhysicalLink(source=n1, target=n2, weight=weight,
                                                       link_specs=LinkSpecs(bandwidth=bw,
                                                                            propagation_delay=prop_delay)))

    def create_new_request(self, req_type: int, gateway_router: Router) -> NewVMRequest:
        net = self._net

        # Get Request VM Nodes
        vms = self.__get_request_nodes(req_type)

        # Get Request vLinks
        vlinks = self.__get_request_links(req_type, vms)

        # Get Request E2E delay
        e2e_delay = self.__get_req_e2e(req_type)

        # Create request net
        req_net = VirtualNetwork(name=f"Request{VMRequest.get_new_request_id()}", network_nodes=vms,
                                 network_edges=vlinks)
        new_request = NewVMRequest(req_net, net, gateway_router, request_type=req_type)
        new_request.e2e_delay = e2e_delay
        gateway_router.attach_request_to_gateway_router(new_request, req_type)

        return new_request

    def create_hosted_request(self, req_type: int, gateway_router: Router) -> HostedVMRequest:
        net = self._net

        # Get Request VM Nodes
        vms = self.__get_request_nodes(req_type)

        # Get Request vLinks
        vlinks = self.__get_request_links(req_type, vms)

        # Get Request E2E delay
        e2e_delay = self.__get_req_e2e(req_type)

        # Create request net
        req_net = VirtualNetwork(name=f"Request{VMRequest.get_new_request_id()}", network_nodes=vms,
                                 network_edges=vlinks)
        hosted_request = HostedVMRequest(req_net, net, gateway_router, request_type=req_type)
        hosted_request.e2e_delay = e2e_delay

        return hosted_request

    def __get_request_links(self, req_type: int, vms: List[VirtualMachine]) -> List[VirtualLink]:
        vlinks = []
        new_requests_links_file = self._requests_links_file
        with open(new_requests_links_file, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                if int(row["Type"]) == req_type:
                    source = int(row["Source"])
                    target = int(row["Target"])
                    prop_delay_req = float(row["Delay Req (µs)"])
                    bw_req = float(row["BW requirement (Mbps)"])
                    # TODO: Parse new vLink assign cost
                    # TODO: Parse hosted vLink migration cost
                    vlink = VirtualLink(source=vms[source], target=vms[target],
                                        link_specs=LinkSpecs(bandwidth=bw_req, propagation_delay=prop_delay_req))
                    vlinks.append(vlink)
                else:
                    continue
        return vlinks

    def __get_request_nodes(self, req_type: int) -> List[VirtualMachine]:
        vms = []
        new_requests_nodes_file = self._requests_nodes_file
        with open(new_requests_nodes_file, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                if int(row["Type"]) == req_type:
                    vm_index = int(row["VM Index"])
                    cpu = int(row["CPU"])
                    memory = int(row["Memory"])
                    storage = int(row["Storage"])
                    revenue_coeff = float(row["Revenue Coeff"])
                    migration_coeff = float(row["Migration Coeff"])
                    isDummy = not bool(vm_index)
                    if isDummy:
                        vm = DummyVirtualMachine(node_name=f"vnf{vm_index}_{VMRequest.get_new_request_id()}",
                                                 node_label="Dummy Virtual Machine", vm_revenue_coeff=revenue_coeff,
                                                 vm_migration_coeff=migration_coeff)
                        vms.append(vm)
                    else:
                        vm = VirtualMachine(specs=Specs(cpu=cpu, memory=memory, storage=storage),
                                            node_name=f"vnf{vm_index}_{VMRequest.get_new_request_id()}",
                                            node_label="Virtual Machine", vm_revenue_coeff=revenue_coeff,
                                            vm_migration_coeff=migration_coeff)
                        vms.append(vm)
                else:
                    continue
        return vms

    def __get_req_e2e(self, req_type: int) -> float:
        new_requests_e2e_file = self._requests_e2e_file
        e2e_delay = None
        with open(new_requests_e2e_file, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                if int(row["Type"]) == req_type:
                    e2e_delay = float(row["E2E Delay Req (µs)"]) * (10 ** -6)
                else:
                    continue
        return e2e_delay

    def get_all_new_requests(self) -> List[NewVMRequest]:
        new_requests_dist_file = self._new_requests_dist_file
        new_requests = []
        with open(new_requests_dist_file, "r") as file:
            csv_file = csv.DictReader(file)
            net = self._net
            for row in csv_file:
                gateway_name = row["Gateway"]
                if gateway_name not in net.get_node_dict().keys(): continue
                gateway_router = net.get_node_dict()[gateway_name]
                num_of_type1 = int(row["Type 1"])
                num_of_type2 = int(row["Type 2"])
                num_of_type3 = int(row["Type 3"])
                for i in range(num_of_type1):
                    new_requests.append(self.create_new_request(1, gateway_router))
                for i in range(num_of_type2):
                    new_requests.append(self.create_new_request(2, gateway_router))
                for i in range(num_of_type3):
                    new_requests.append(self.create_new_request(3, gateway_router))
        self._new_requests = new_requests
        return new_requests

    def get_random_new_requests_from_gateway(self, gateway_name, **kwargs):
        seed_number = kwargs["seed_number"] if "seed_number" in kwargs else None
        print_dist = False
        new_requests = []
        net = self._net
        # seed random number generator
        if seed_number is not None:
            seed(seed_number)
        if gateway_name not in net.get_node_dict().keys():
            print("Wrong Gateway!")
            return
        gateway_router = net.get_node_dict()[gateway_name]
        num_of_type1 = randint(0, 9)
        num_of_type2 = randint(0, 9)
        num_of_type3 = randint(0, 9)
        if print_dist:
            print(f"Req. Dist at {gateway_name}: ({num_of_type1}, {num_of_type2}, {num_of_type3})")
        for i in range(num_of_type1):
            new_requests.append(self.create_new_request(1, gateway_router))
        for i in range(num_of_type2):
            new_requests.append(self.create_new_request(2, gateway_router))
        for i in range(num_of_type3):
            new_requests.append(self.create_new_request(3, gateway_router))

        req_dist = [num_of_type1, num_of_type2, num_of_type3]
        return new_requests, req_dist

    def get_all_hosted_requests(self) -> List[HostedVMRequest]:
        hosted_requests_dist_file = self._hosted_requests_dist_file
        hosted_requests = []
        with open(hosted_requests_dist_file, "r") as file:
            csv_file = csv.DictReader(file)
            net = self._net
            for row in csv_file:
                gateway_name = row["Gateway"]
                if gateway_name not in net.get_node_dict().keys(): continue
                gateway_router = net.get_node_dict()[gateway_name]
                num_of_type1 = int(row["Type 1"])
                num_of_type2 = int(row["Type 2"])
                num_of_type3 = int(row["Type 3"])
                for i in range(num_of_type1):
                    hosted_requests.append(self.create_hosted_request(1, gateway_router))
                for i in range(num_of_type2):
                    hosted_requests.append(self.create_hosted_request(2, gateway_router))
                for i in range(num_of_type3):
                    hosted_requests.append(self.create_hosted_request(3, gateway_router))
        self._hosted_requests = hosted_requests
        return hosted_requests

    def assign_hosted_requests(self):
        hosted_requests = self._hosted_requests
        net = self._net
        net_node_dict = net.get_node_dict()
        net_link_dict = net.get_links_dict_full_with_reverse_names()
        for req in hosted_requests:
            gateway_router_name = req.gateway_router.node_name
            vms = req.vm_net.get_vms()
            vlinks = req.hosted_vlinks_dict
            if gateway_router_name == "w2":
                if req.request_type == 1:
                    file_name = "input/HostedRequests/Assignments/Type1/Type1_w2_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 2:
                    file_name = "input/HostedRequests/Assignments/Type2/Type2_w2_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 3:
                    file_name = "input/HostedRequests/Assignments/Type3/Type3_w2_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
            elif gateway_router_name == "w3":
                if req.request_type == 1:
                    file_name = "input/HostedRequests/Assignments/Type1/Type1_w3_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 2:
                    file_name = "input/HostedRequests/Assignments/Type2/Type2_w3_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 3:
                    file_name = "input/HostedRequests/Assignments/Type3/Type3_w3_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
            elif gateway_router_name == "w4":
                if req.request_type == 1:
                    file_name = "input/HostedRequests/Assignments/Type1/Type1_w4_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 2:
                    file_name = "input/HostedRequests/Assignments/Type2/Type2_w4_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 3:
                    file_name = "input/HostedRequests/Assignments/Type3/Type3_w4_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
            elif gateway_router_name == "w5":
                if req.request_type == 1:
                    file_name = "input/HostedRequests/Assignments/Type1/Type1_w5_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 2:
                    file_name = "input/HostedRequests/Assignments/Type2/Type2_w5_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()
                if req.request_type == 3:
                    file_name = "input/HostedRequests/Assignments/Type3/Type3_w5_1.CSV"
                    self.__parse_request_assignment(file_name, net_link_dict, net_node_dict, vlinks, vms)
                    req.update_dicts()

    def __parse_request_assignment(self, file_name, net_link_dict, net_node_dict, vlinks, vms):
        with open(file_name, "r") as file:
            csv_file = csv.DictReader(file)
            for row in csv_file:
                if row["VM or vLink?"] == "VM":
                    index = int(row["Index"])
                    host = row["Host"]
                    current_vm = vms[index]
                    current_host = net_node_dict[host]
                    if index == 0:
                        continue
                    else:
                        current_host.add_virtual_machine(current_vm)

                if row["VM or vLink?"] == "vLink":
                    source_vm_index = int(row["Source"])
                    target_vm_index = int(row["Target"])
                    hosts = row["Host"].split("\n")
                    if hosts[0] == "NA":
                        continue
                    source_vm = vms[source_vm_index]
                    target_vm = vms[target_vm_index]
                    current_vlink = vlinks[f"({source_vm.node_name},{target_vm.node_name})"]
                    for pLink in hosts:
                        current_plink = net_link_dict[pLink]
                        current_vlink.add_hosting_physical_link(current_plink)
