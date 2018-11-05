
'''
Created on Oct 12, 2016
@author: mwittie
'''
import network_3 as network
import link_3 as link
import threading
from time import sleep

#Will need to add more interfaces, and routers, and stuff

##configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 6  # give the network sufficient time to transfer all packets before quitting, may need to increase

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    # create network nodes
    client1 = network.Host(1)
    client2 = network.Host(2)
    #Take client and append it to the object list
    object_L.append(client1)
    object_L.append(client2)

    server1 = network.Host(3)
    server2 = network.Host(4)
    object_L.append(server1)
    object_L.append(server2)

    #Routers are given a name, in_count is the number of in interfaces, out_count is the number of out interfaces,
    #Max queue size 0 means they are unlimited
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
    object_L.append(router_a)
    object_L.append(router_b)
    object_L.append(router_c)
    object_L.append(router_d)

    # create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    # link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu

    # links between clients 1 and 2 to router A
    link_layer.add_link(link.Link(client1, 0, router_a, 0, 50))
    link_layer.add_link(link.Link(client2, 0, router_a, 1, 50))
    # links between router A and routers B and C
    link_layer.add_link(link.Link(router_a, 0, router_b, 0, 30))
    link_layer.add_link(link.Link(router_a, 1, router_c, 0, 30))
    # link from router B to router D
    link_layer.add_link(link.Link(router_b, 0, router_d, 0, 30))
    # link from router C to router D
    link_layer.add_link(link.Link(router_c, 0, router_d, 1, 30))
    # links from router D to servers 1 and 2
    link_layer.add_link(link.Link(router_d, 0, server1, 0, 30))
    link_layer.add_link(link.Link(router_d, 1, server2, 0, 30))


    # start all the objects
    #Each node, and the link layer all together need threads
    thread_L = []
    thread_L.append(threading.Thread(name=client1.__str__(), target=client1.run))
    thread_L.append(threading.Thread(name=client2.__str__(), target=client2.run))

    thread_L.append(threading.Thread(name=server1.__str__(), target=server1.run))
    thread_L.append(threading.Thread(name=server2.__str__(), target=server2.run))

    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()

    # create some send events
    #Creates sample data and takes care of it
    #for i in range(3):
        ##First parameter is address, and server in this case has address 2
        #client.udt_send(2, 'Sample data %d' % i)

    #Hugh changing
    #myData = "pretty long data piece. This has over 100 characters to test the new for loop thin I made. It will work better"
    myData = "Short data piece, has have 35 chars"
    print(len(myData),"Is the length of my data string")

    #client.udt_send(2,myData)
    #0s are in order here: frag, offset, pid
    #Need to manually put in the id here; it will not increase on its own
    #Note in packet format it's: pid,frag,offset,dst_addr,payload
    client2.udt_send(4, myData, 66, 0, 0)

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
