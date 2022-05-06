#!/usr/bin/python3
# The main code of the Simulator
from CloudDefrag.Model.Algorithm.HouILP import HouILP
from CloudDefrag.Model.Algorithm.RamyILP import RamyILP
from CloudDefrag.Model.Algorithm.Request import VMRequest, NewVMRequest, HostedVMRequest
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router, DummyVirtualMachine
from CloudDefrag.Model.Graph.Specs import Specs
import matplotlib.pyplot as plt
import networkx as nx


def main():
    # Create network
    net = PhysicalNetwork(name="Net1")
    s1 = Server(specs=Specs(cpu=5, memory=5, storage=500), node_name="s1", node_label="Server")
    s2 = Server(specs=Specs(cpu=5, memory=5, storage=500), node_name="s2", node_label="Server")
    w1 = Router(node_name="w1", node_label="Router", is_gateway=True)
    net.add_network_node(s1, name="s1", label="Server")
    net.add_network_node(s2, name="s2", label="Server")
    net.add_network_node(w1, name="w1", label="Router")
    net.add_network_edge(PhysicalLink(source=w1, target=s1, link_specs=LinkSpecs(bandwidth=100,
                                                                                 propagation_delay=1E-6)))
    net.add_network_edge(PhysicalLink(source=w1, target=s2, link_specs=LinkSpecs(bandwidth=100,

                                                                                 propagation_delay=1E-6)))
    # Create request 1
    vm0 = DummyVirtualMachine(gateway_router=w1, node_name=f"vm0_{VMRequest.get_new_request_id()}",
                              node_label="Dummy Virtual Machine", vm_revenue_coeff=2)
    vm1 = VirtualMachine(specs=Specs(cpu=2, memory=2, storage=200), node_name=f"vm1_{VMRequest.get_new_request_id()}",
                         node_label="Virtual Machine", vm_revenue_coeff=2)
    vm2 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name=f"vm2_{VMRequest.get_new_request_id()}",
                         node_label="Virtual Machine", vm_revenue_coeff=2)

    v_net1_nodes = [vm0, vm1, vm2]
    v_net1_edges = [VirtualLink(source=vm0, target=vm1, link_specs=LinkSpecs(bandwidth=100, propagation_delay=1E-6)),
                    VirtualLink(source=vm1, target=vm2, link_specs=LinkSpecs(bandwidth=100, propagation_delay=1E-6))]

    v_net1 = VirtualNetwork(name=f"Request{VMRequest.get_new_request_id()}", network_nodes=v_net1_nodes,
                            network_edges=v_net1_edges)

    request1 = NewVMRequest(v_net1, net)
    request1.e2e_delay = 10E-6

    # Create request 2
    vm0 = DummyVirtualMachine(gateway_router=w1, node_name=f"vm0_{VMRequest.get_new_request_id()}",
                              node_label="Dummy Virtual Machine", vm_revenue_coeff=2)
    vm1 = VirtualMachine(specs=Specs(cpu=2, memory=2, storage=200), node_name=f"vm1_{VMRequest.get_new_request_id()}",
                         node_label="Virtual Machine", vm_revenue_coeff=2)
    vm2 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name=f"vm2_{VMRequest.get_new_request_id()}",
                         node_label="Virtual Machine", vm_revenue_coeff=2)
    v_net1_nodes = [vm0, vm1, vm2]
    v_net1_edges = [VirtualLink(source=vm0, target=vm1, link_specs=LinkSpecs(bandwidth=100, propagation_delay=1E-6)),
                    VirtualLink(source=vm1, target=vm2, link_specs=LinkSpecs(bandwidth=100, propagation_delay=1E-6))]
    v_net1 = VirtualNetwork(name=f"Request{VMRequest.get_new_request_id()}", network_nodes=v_net1_nodes,
                            network_edges=v_net1_edges)

    s1.add_virtual_machine(vm1)
    s1.add_virtual_machine(vm2)
    v_net1_edges[0].add_hosting_physical_link(net.network_edges[0])

    request2 = HostedVMRequest(v_net1, net)
    request2.e2e_delay = 10E-6

    hosted_requests = [request2]
    new_requests = [request1]

    algo = RamyILP(net, new_requests, hosted_requests)
    algo.model.update()
    algo.solve(display_result=True)
    # algo.apply_result()

    options = {
        'node_color': 'orange',
        'node_size': 2000,
        'width': 5,
    }

    nx.draw(v_net1, with_labels=True, **options)
    plt.savefig("output/request1.png")

    # nx.draw(net, with_labels=True, **options)
    # plt.savefig("output/net.png")


if __name__ == '__main__':
    main()
