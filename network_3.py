'''
Created on Oct 12, 2016
@author: mwittie
'''
import queue
import threading
# Hugh importing math for rounding up
import math


# Needs to check somewhere if packet is longer than mtu, and divide it if it is
# Needs router class to take an extra parameter for the router table, and then maniuplate the forward function
# he suggests using the dictionary class

## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None

    ##get packet from the queue interface
    # Get packet from queue or get none if it's empty
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
    # You should be able to chance these no problem. Just don't change the order of them in the packet
    dst_addr_S_length = 5
    src_addr_S_length = 5
    frag_len = 1
    offset_len = 3
    pid_len = 2
    header_len = pid_len + offset_len + frag_len + dst_addr_S_length

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    # Hugh adding - id, frag flag, offset
    # New Network packet will look like this:
    # pid,frag,offset,dst_addr,payload
    # 00  0    000    00000    ...
    # 11 chars before payload
    def __init__(self, src_addr, dst_addr, data_S, pid, frag=0, offset=0):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.data_S = data_S

        # Need length here too? If so, just add it like the others, modify everything so it's unified
        self.frag = frag
        self.offset = offset
        self.pid = pid

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    # Can make and extract from byte string --- byte_S
    def to_byte_S(self):
        byte_S = str(self.pid).zfill(self.pid_len)
        byte_S += str(self.frag).zfill(self.frag_len)
        byte_S += str(self.offset).zfill(self.offset_len)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        pid = int(byte_S[0: self.pid_len])
        frag = int(byte_S[self.pid_len: self.pid_len + self.frag_len])
        offset = int(byte_S[self.pid_len + self.frag_len: self.pid_len + self.frag_len + self.offset_len])
        dst_addr = int(
            byte_S[self.pid_len + self.frag_len + self.offset_len:self.pid_len + self.frag_len + self.offset_len
                                                                  + self.dst_addr_S_length])
        src_addr = int(
            byte_S[self.pid_len + self.frag_len + self.offset_len:self.pid_len + self.frag_len + self.offset_len
                                                                  + self.dst_addr_S_length + self.src_addr_S_length])
        data_S = byte_S[NetworkPacket.header_len:]
        return self(src_addr, dst_addr, data_S, pid, frag, offset)


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
    # Can turn host into string for printing
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    # Take packet, and put it into the out interface. "that's it" he says

    def udt_send(self, dst_addr, data_S, pid, frag, offset):

        # Assumes mtu won't change during this. MTU for the payload length.
        mtu = self.out_intf_L[0].mtu - NetworkPacket.header_len

        print("Len of data is ", len(data_S), "and data is:", data_S)
        print()
        # print(mtu,"is mtu")

        ##Hugh adding - cut data up if it's longer than mtu
        for i in range(math.ceil(len(data_S) / mtu)):
            p = NetworkPacket(self.addr, dst_addr, data_S[mtu * i:mtu * (i + 1)], pid, frag, offset)
            self.out_intf_L[0].put(p.to_byte_S())  # send packets always enqueued successfully
            # print("Now sending this many chars:: ", len(data_S[mtu*i:mtu*(i+1)]))
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))

    # Getting a packet from an in interface, and then print it
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()

        if pkt_S is not None:
            # frag = int(str(p)[NetworkPacket.pid_len: NetworkPacket.pid_len + NetworkPacket.frag_len])
            payload = ""
            print()
            # print("Going through receive now")

            # current highest offset + data length
            max = 0
            # Used headers to check that we haven't gotten a duplicate
            # Format being [pid,offset]
            headers = []
            # Lower bound is the lowest offset we've put in so far. To start, let's make it an arbitrary high number
            lb = 9 * 10 * NetworkPacket.offset_len
            pid_len = NetworkPacket.pid_len
            frag_len = NetworkPacket.frag_len
            offset_len = NetworkPacket.offset_len
            dst_addr_S_length = NetworkPacket.dst_addr_S_length
            src_addr_S_length = NetworkPacket.src_addr_S_length
            # To store the final header
            header = ""

            # Will go through once if not fragmented
            # Right now, this will have to be changed if a packet is fragmented repeatedely
            # So that it checks the original packet length (or something), to ensure it's finished with everything
            # Because it might get a fragmented frag of 0, rather than the final one and end early
            # Right now, this should work for reordered packets as well
            while True:

                while (pkt_S is None):
                    # Get the next packet
                    pkt_S = self.in_intf_L[0].get()
                # print("Received in udt receive:", pkt_S)
                p = NetworkPacket.from_byte_S(pkt_S)

                # Stuff from the packet, unused stuff maybe can be used later if we need modifications
                pid = str(p)[: pid_len]
                frag = int(str(p)[pid_len: pid_len + frag_len])
                # print("frag is", frag,"packet is",p,"printed above is",int(str(p)[pid_len: pid_len + frag_len]))
                offset = int(str(p)[pid_len + frag_len: pid_len + frag_len + offset_len])
                dst_addr = str(p)[pid_len + frag_len + offset_len: pid_len + frag_len + offset_len + dst_addr_S_length]
                src_addr = str(p)[pid_len + frag_len + offset_len: pid_len + frag_len + offset_len
                                                                   + dst_addr_S_length + src_addr_S_length]
                data_S = str(p)[NetworkPacket.header_len:]

                # Going through the different cases of where to stick the payload
                # If we get a duplicate, then don't do anything
                if ((pid, offset) in headers):
                    # print("Duplicate, not adding to payload")
                    pass
                # If it comes after, stick it on the end
                elif (offset >= max):
                    payload = payload + data_S
                # If it comes before, stick it at the beginning
                elif (lb > offset):
                    payload = data_S + payload
                # If it's in the middle, stick it in the middle
                elif (lb < offset and offset < max):
                    payload = payload[:offset] + data_S + payload[offset:]
                else:
                    print("Data not added to payload. Something is wrong.")
                # print(payload,"is my payload")

                # print("In order: max,lb,offset",max,lb,offset)

                max = len(payload) + offset

                if (lb > offset):
                    lb = offset

                headers.append((pid, offset))

                if (frag == 0):
                    header = str(p)[:NetworkPacket.header_len]
                    break

                # After dealing with the packet, free up the variable for the next one
                pkt_S = None

            print('%s: received packet "%s%s" on the in interface' % (self, header, payload))
            # print("Received payload",payload)

    ## thread target for the host to keep receiving data
    # While true, call udt receive to see if there's anything new in the in interface, and that's it

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
    # List of in and out interfaces

    def __init__(self, name, in_count, out_count, max_queue_size):
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(in_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(out_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # Get packet from interface, and if it exists, parse it from string, then put packet to out interface with the same interface
    # So sending it from interface 0 to interface 0, for instance
    # To improve this, do a lookup in the router table
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:

                # get packet from interface i
                pkt_S = self.in_intf_L[i].get()

                # if packet exists make a forwarding decision

                if pkt_S is not None:
                    # print("Forwarding")
                    # print()

                    p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
                    pid_len = NetworkPacket.pid_len
                    frag_len = NetworkPacket.frag_len
                    offset_len = NetworkPacket.offset_len
                    dst_addr_S_length = NetworkPacket.dst_addr_S_length
                    src_addr_S_length = NetworkPacket.src_addr_S_length

                    # Stuff from the packet
                    pid = int(str(p)[:pid_len])
                    frag = str(p)[pid_len: pid_len + frag_len]
                    offset = int(str(p)[pid_len + frag_len: pid_len + frag_len + offset_len])
                    dst_addr = str(p)[pid_len + frag_len + offset_len: pid_len + frag_len + offset_len
                                                                       + dst_addr_S_length]
                    src_addr = str(p)[pid_len + frag_len + offset_len: pid_len + frag_len + offset_len
                                                                       + dst_addr_S_length + src_addr_S_length]
                    data_S = str(p)[NetworkPacket.header_len:]

                    ## Assumes mtu won't change during this indentation
                    ## Subtracts number
                    mtu = self.out_intf_L[0].mtu - NetworkPacket.header_len
                    # print("MTU IS ",mtu)

                    # Fragmenting now
                    if (math.ceil(len(data_S) / mtu) > 1):
                        # How many times we need to fragment
                        for j in range(math.ceil(len(data_S) / mtu)):
                            # Dealing with header
                            frag = 1
                            # If we're on the last one, put in frag as 0
                            if (j == int(len(data_S) / mtu)):
                                frag = 0

                            # print("J is ",j, "and range is",math.ceil(len(data_S) / mtu))

                            # print("Numerator: ",offset + len(data_S),"Denominator:",(math.ceil(len(data_S) / mtu)) * j)

                            # offset is where this packet is supposed to start reassembly, while avoiding division by 0
                            # offset is just previous offset sent in, with the mtu * how many times we've gone through
                            offset = offset + mtu * j

                            # print("offset is ",offset)

                            # Fragmenting                       data_S[mtu*i:mtu*(i+1)]
                            p = NetworkPacket(src_addr, dst_addr, data_S[mtu * j: mtu * (j + 1)], pid, frag, offset)
                            self.out_intf_L[0].put(p.to_byte_S())
                            # print("Now sending this many chars:: ", len(data_S[mtu*i:mtu*(i+1)]))
                            print('%s: sending packet "%s" on the out interface with mtu=%d' % (
                                self, p, self.out_intf_L[0].mtu))
                            self.out_intf_L[i].put(p.to_byte_S(), True)
                    #     print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                    #           % (self, p, i, i, self.out_intf_L[i].mtu))

                    # If not fragmenting
                    else:
                        p = NetworkPacket.from_byte_S(pkt_S)
                        self.out_intf_L[i].put(p.to_byte_S(), True)
                        # print('%s: forwarding packet "%s" from interface w/out fragmentation %d to %d with mtu %d' \
                        #      % (self, p, i, i, self.out_intf_L[i].mtu))



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
