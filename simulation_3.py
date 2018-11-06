'''
Original Author: Mike Wittie
Created on 12 Oct, 2016

Assignment Authors: Kyle J Brekke, Hugh O'Neill
Modified on 5 Nov, 2018
'''

import network_3 as network
import link_3 as link
import threading
from time import sleep

## Configuration parameters
router_queue_size = 0  # 0 denotes an unlimited queue size
simulation_time = 6  # Gives the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = []  # Keeps track of objects for easy termination

    ## Create network nodes
    # Create client nodes
    client1 = network.Host(1)
    client2 = network.Host(2)
    # Appends clients to the object list
    object_L.append(client1)
    object_L.append(client2)
    # Create server nodes
    server1 = network.Host(3)
    server2 = network.Host(4)
    # Appends clients to the object list
    object_L.append(server1)
    object_L.append(server2)

    # Routers are given a name; in_count is the number of in interfaces, out_count is the number of out interfaces,
    # Max queue size 0 means they have unlimited packet capacity, tables are used for routing.
    table_a = {('00001', '00003'): 0, ('00001', '00004'): 0,
               ('00002', '00003'): 1, ('00002', '00004'): 1}
    router_a = network.Router(name='A', in_count=2, out_count=2, max_queue_size=router_queue_size, table=table_a)
    table_b = {('00001', '00003'): 0, ('00001', '00004'): 0,
               ('00002', '00003'): 0, ('00002', '00004'): 0}
    router_b = network.Router(name='B', in_count=1, out_count=1, max_queue_size=router_queue_size, table=table_b)
    table_c = {('00001', '00003'): 0, ('00001', '00004'): 0,
               ('00002', '00003'): 0, ('00002', '00004'): 0}
    router_c = network.Router(name='C', in_count=1, out_count=1, max_queue_size=router_queue_size, table=table_c)
    table_d = {('00001', '00003'): 0, ('00001', '00004'): 1,
               ('00002', '00003'): 0, ('00002', '00004'): 1}
    router_d = network.Router(name='D', in_count=2, out_count=2, max_queue_size=router_queue_size, table=table_d)
    # Appends the routers to the object list
    object_L.append(router_a)
    object_L.append(router_b)
    object_L.append(router_c)
    object_L.append(router_d)

    # Create and append a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    # Links between clients 1 and 2 to router A
    link_layer.add_link(link.Link(client1, 0, router_a, 0, 60))
    link_layer.add_link(link.Link(client2, 0, router_a, 1, 60))
    # Links between router A and routers B and C
    link_layer.add_link(link.Link(router_a, 0, router_b, 0, 60))
    link_layer.add_link(link.Link(router_a, 1, router_c, 0, 60))
    # Link from router B to router D
    link_layer.add_link(link.Link(router_b, 0, router_d, 0, 60))
    # Link from router C to router D
    link_layer.add_link(link.Link(router_c, 0, router_d, 1, 60))
    # Links from router D to servers 1 and 2
    link_layer.add_link(link.Link(router_d, 0, server1, 0, 60))
    link_layer.add_link(link.Link(router_d, 1, server2, 0, 60))

    # Initialize all network nodes
    # Each object runs on a thread
    thread_L = [threading.Thread(name=client1.__str__(), target=client1.run),
                threading.Thread(name=client2.__str__(), target=client2.run),
                threading.Thread(name=server1.__str__(), target=server1.run),
                threading.Thread(name=server2.__str__(), target=server2.run),
                threading.Thread(name=router_a.__str__(), target=router_a.run),
                threading.Thread(name=router_b.__str__(), target=router_b.run),
                threading.Thread(name=router_c.__str__(), target=router_c.run),
                threading.Thread(name=router_d.__str__(), target=router_d.run),
                threading.Thread(name="Network", target=link_layer.run)]

    for t in thread_L:
        t.start()

    myData = "This is a sample String, which shall be sent from a client, across multiple linked routers, to a server."

    # Send the sample data from a client to a server
    client1.udt_send(4, myData, 66, 0, 0)
    # client1.udt_send(3, myData, 36, 0, 0)
    # client2.udt_send(4, myData, 42, 0, 0)

    # Give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    # Terminate and join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")

