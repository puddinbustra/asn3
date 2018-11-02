
'''
Created on Oct 12, 2016
@author: mwittie
'''
import queue
import threading
#Hugh importing math for rounding up
import math

#Needs to check somewhere if packet is longer than mtu, and divide it if it is
#Needs router class to take an extra parameter for the router table, and then maniuplate the forward function
#he suggests using the dictionary class

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None

    ##get packet from the queue interface
    #Get packet from queue or get none if it's empty
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implements a network layer packet (different from the RDT packet
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    dst_addr_S_length = 5
    pid = 0
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    #Hugh adding - id, frag flag, offset
    def __init__(self, dst_addr, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        #Need length here too?
        self.fragFlag = 0
        self.offset = 0
        #pid will count through 19, just so it has an end bound, and then it will reset to 0
        self.pid = NetworkPacket.pid
        if NetworkPacket.pid == 20:
            NetworkPacket.pid = 0
        else:
            NetworkPacket.pid += 1

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    #Can make and extract from byte string --- byte_S
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0: NetworkPacket.dst_addr_S_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length:]
        return self(dst_addr, data_S)


## Implements a network host for receiving and transmitting data
class Host:

    ##@param addr: address of this node represented as an integer
    #
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False  # for thread termination

    ## called when printing the object
    #Can turn host into string for printing
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    #Take packet, and put it into the out interface. "that's it" he says

    def udt_send(self, dst_addr, data_S):

        #Assumes mtu won't change during this
        mtu = self.out_intf_L[0].mtu-dst_addr_S_length

        print("Len of data is ",len(data_S), "and data is:",data_S)
        print()

        ##Hugh adding - cut data up if it's longer than mtu
        for i in range(math.ceil(len(data_S)/mtu)):
            p = NetworkPacket(dst_addr, data_S[mtu*i:mtu*(i+1)])
            self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
            #print("Now sending this many chars:: ", len(data_S[mtu*i:mtu*(i+1)]))
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))

    #Getting a packet from an in interface, and then print it
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            print('%s: received packet "%s" on the in interface' % (self, pkt_S))

    ## thread target for the host to keep receiving data
    #While true, call udt receive to see if there's anything new in the in interface, and that's it

    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router described in class
class Router:

    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces
    # @param max_queue_size: max queue length (passed to Interface)
    #List of in and out interfaces

    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    #Get packet from interfae, and if it exists, parse it from string, then put packet to out interface with the same interface
    #So sending it from interface 0 to interface 0, for instance
    #To improve this, do a lookup in the router table
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:

                # get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                # if packet exists make a forwarding decision
                #print(len(pkt_S),"Is packet len")

                if pkt_S is not None:
                    print("Forwarding")
                    ###Hugh altering
                    ##Go through each packet (adding 20 bytes for udt header, maybe 20 for tcp to just first), and segment it
                    #for j in range(packetLen // self.out_intf_L[0].mtu):
                    #    pass


                    p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                    print("Hugh is printing the packet now: ",p)
                    print("Trying to print a piece of the packet: ",str(p)[dst_addr_S_length:])

                    #Address and payload from the packet
                    #Note that that if the address length changes, these numbers will have to change to fit that
                    dst_addr, data_S = str(p)[:dst_addr_S_length], str(p)[dst_addr_S_length:]

                    ## Assumes mtu won't change during this indentation
                    ## Subtracts number
                    mtu = self.out_intf_L[0].mtu
                    #print("MTU IS ",mtu)

                    #print("Len of data is ", len(data_S), "and data is:", data_S)
                    #NEXT - add id, frag flag, and offset to all the packets (fragmented or not)

                    #Hugh adding - cut data up if it's longer than mtu
                    for j in range(math.ceil(len(data_S) / mtu)):
                        p = NetworkPacket(dst_addr, data_S[mtu * j:mtu * (j + 1)])
                        self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
                        # print("Now sending this many chars:: ", len(data_S[mtu*i:mtu*(i+1)]))
                        print('%s: sending packet "%s" on the out interface with mtu=%d' % (
                        self, p, self.out_intf_L[0].mtu))
                        self.out_intf_L[i].put(p.to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                              % (self, p, i, i, self.out_intf_L[i].mtu))


            # HERE you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is also i
            # Will be replacing this code with something better - "not dumb"

            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass

    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return
