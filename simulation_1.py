
'''
Created on Oct 12, 2016
@author: mwittie
'''
import network_1
import link_1
import threading
from time import sleep

#Will need to add more interfaces, and routers, and stuff

##configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 1  # give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    # create network nodes
    client = network.Host(1)
    #Take client and append it to the object list
    object_L.append(client)
    server = network.Host(2)
    object_L.append(server)
    #This router a is given a name, interface count is the number of in and out interfaces (these go together,
    #Max queue size, 0 means they are unlimited
    router_a = network.Router(name='A', intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)

    # create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    # link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
    #These are between client, and router, then router and server,
    #Out interface first, in interface is second
    #So for this first line, client out interface 0, to router interface in 0
    link_layer.add_link(link.Link(client, 0, router_a, 0, 50))
    link_layer.add_link(link.Link(router_a, 0, server, 0, 50))

    # start all the objects
    #Each node, and the link layer all together need threads
    thread_L = []
    thread_L.append(threading.Thread(name=client.__str__(), target=client.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()

    # create some send events
    #Creates sample data and takes care of it
    for i in range(3):
        #First parameter is address, and server in this case has address 2
        client.udt_send(2, 'Sample data %d' % i)

    # give the network sufficient time to transfer all packets before quitting
    #This is to help deal with packet buildup. As this becomes longer, we may need to increase this to more seconds
    #So if it starts ending early, maybe increase this simulation time
    sleep(simulation_time)

    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")

# writes to host periodically
