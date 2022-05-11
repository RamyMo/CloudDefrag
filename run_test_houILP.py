#!/usr/bin/python3
# The main code of the Simulator
from CloudDefrag.Model.Algorithm.HouILP import HouILP
from CloudDefrag.Model.Algorithm.Request import VMRequest
from CloudDefrag.Model.Graph.Link import VirtualLink, LinkSpecs, PhysicalLink
from CloudDefrag.Model.Graph.Network import PhysicalNetwork, VirtualNetwork
from CloudDefrag.Model.Graph.Node import Server, VirtualMachine, Router
from CloudDefrag.Model.Graph.Specs import Specs
import matplotlib.pyplot as plt
import networkx as nx


def main():
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

    vm1 = VirtualMachine(specs=Specs(cpu=2, memory=2, storage=200), node_name="vm1", node_label="Virtual Machine",
                         vm_revenue_coeff=2)
    vm2 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name="vm2", node_label="Virtual Machine",
                         vm_revenue_coeff=2)
    vm3 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name="vm3", node_label="Virtual Machine",
                         vm_revenue_coeff=2)
    vm4 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name="vm4", node_label="Virtual Machine",
                         vm_revenue_coeff=2)
    vm5 = VirtualMachine(specs=Specs(cpu=4, memory=4, storage=400), node_name="vm5", node_label="Virtual Machine",
                         vm_revenue_coeff=2)
    vm6 = VirtualMachine(specs=Specs(cpu=1, memory=1, storage=100), node_name="vm6", node_label="Virtual Machine",
                         vm_revenue_coeff=2)

    v_net1 = VirtualNetwork(name="Request1", nodes=[w1, vm1, vm2])
    v_net1.add_network_edge(VirtualLink(source=w1, target=vm1, link_specs=LinkSpecs(bandwidth=100,
                                                                                    propagation_delay=1E-6)))
    v_net1.add_network_edge(VirtualLink(source=vm1, target=vm2, link_specs=LinkSpecs(bandwidth=100,
                                                                                     propagation_delay=1E-6)))

    request1 = VMRequest(v_net1, None)
    # vlink1 = VirtualLink(source=vm1, target=vm2, link_specs=LinkSpecs(bandwidth=100, propagation_delay=1E-3))
    # vm1.connect_to_vm(vm2, vlink1)
    # vm1.connect_to_vm(vm2, vlink1)

    s1.add_virtual_machine(vm1)
    s1.add_virtual_machine(vm2)
    s2.add_virtual_machine(vm3)
    s2.add_virtual_machine(vm4)

    vms = [vm1, vm2, vm3, vm4]
    requests = [vm5, vm6]

    # algo = HouILP(net, requests, hosted_vms=vms, model_name="dummy_example")
    # algo.solve(display_result=True)
    # algo.apply_result()

    options = {
        'node_color': 'orange',
        'node_size': 2000,
        'width': 5,
    }

    nx.draw(v_net1, with_labels=True, **options)
    plt.savefig("output/v_net1.png")


if __name__ == '__main__':
    main()