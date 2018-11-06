'''
Original Author: Mike Wittie
Created on 12 Oct, 2016

Assignment Authors: Kyle J Brekke, Hugh O'Neill
Modified on 5 Nov, 2018
'''

import queue
import threading
import math  # Used for rounding


## Wrapper class for the queue of packets found in Routers and Hosts
class Interface:

    ## Constructor for the Interface class
    # @param maxsize - the maximum size of the queue which hold packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None

    ## Get packet from the queue
    # Returns nothing if the queue is empty
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ## Insert the packet into the queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until the queue has space, may throw a queue.Full exception if False
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implementation of a network layer packet
class NetworkPacket:

    ## Encoding lengths for packets
    # Address length of 5 allows for 9999 unique hosts to exist at any given time
    dst_addr_S_length = 5  # Length of the destination address
    src_addr_S_length = 5  # Length of the source address
    frag_len = 1  # Fragmentation is only a single digit, as there are only two states, 0 and 1
    offset_len = 3
    pid_len = 2  # PID length of 2 allows for 99 simultaneous, unique packet identifiers
    header_len = pid_len + offset_len + frag_len + dst_addr_S_length + src_addr_S_length  # Total header length

    ## Constructor for the NetworkPacket length
    # @param src_addr - Address of the host which sent the packet
    # @param dst_addr - Address of the host receiving the packet
    # @param data_S - The content of the packet
    # @param pid - Packet IDentifier, number used to determine fragments that come from the same packet
    # @param frag - Fragmentation state of the packet, the last packet of several fragments has a value of 0
    # @param offset - Used to reassemble packets from their fragments
    def __init__(self, src_addr, dst_addr, data_S, pid, frag=0, offset=0):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.frag = frag
        self.offset = offset
        self.pid = pid

    ## Called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## Converts a packet to a byte string for transmission over links
    # byte_S can be transmitted back into a packet object
    def to_byte_S(self):
        byte_S = str(self.pid).zfill(self.pid_len)
        byte_S += str(self.frag).zfill(self.frag_len)
        byte_S += str(self.offset).zfill(self.offset_len)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += self.data_S
        return byte_S  # Format: {00 0 000 0000 0000 [...Data...]}

    ## Extracts a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        pid = int(byte_S[0: self.pid_len])

        frag = int(byte_S[self.pid_len:self.pid_len + self.frag_len])

        offset = int(byte_S[self.pid_len + self.frag_len:
                            self.pid_len + self.frag_len + self.offset_len])

        dst_addr = int(byte_S[self.pid_len + self.frag_len + self.offset_len:
                                              self.pid_len + self.frag_len +
                                              self.offset_len + self.dst_addr_S_length])

        src_addr = int(byte_S[self.pid_len + self.frag_len + self.offset_len + self.dst_addr_S_length:
                                                      self.pid_len + self.frag_len + self.offset_len +
                                                      self.dst_addr_S_length + self.src_addr_S_length])

        data_S = byte_S[NetworkPacket.header_len:]
        return self(src_addr, dst_addr, data_S, pid, frag, offset)


## Implements a network host for receiving and transmitting data
class Host:

    ## Constructor for the Host class
    # @param addr: address of this node represented as an integer; May or may not be iterative
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False  # Terminates the host if True

    ## Called when printing the object
    # Can be used to print the Host as human-readable
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## Creates a packet and queues it for transmission
    # @param dst_addr - The destination address for the packet
    # @param data_S - The data being transmitted to the network layer
    # @param pid - The created packet's identifying value
    # @param frag - Used to determine if the packet is a fragment of a larger packet, defaults to 0 (NOT)
    # @param offset - used to reassemble a packet from multiple fragments
    def udt_send(self, dst_addr, data_S, pid, frag, offset):

        # Assumes the Host's MTU will not change during execution
        mtu = self.out_intf_L[0].mtu - NetworkPacket.header_len

        print("Len of data is ", len(data_S), "and data is:", data_S)

        # Determine if the packet is longer than the Host's MTU, if so: segment it
        for i in range(math.ceil(len(data_S) / mtu)):
            p = NetworkPacket(self.addr, dst_addr, data_S[mtu * i:mtu * (i + 1)], pid, frag, offset)
            self.out_intf_L[0].put(p.to_byte_S())
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, p, self.out_intf_L[0].mtu))

    ## Receives a packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()

        if pkt_S is not None:
            payload = ""

            # Current offset + data_length
            max_len = 0

            # List of headers used to check that a duplicate has not been acquired
            headers = []

            # Lower bound, or the lowest current offset used
            lb = 9 * 10 * NetworkPacket.offset_len
            pid_len = NetworkPacket.pid_len
            frag_len = NetworkPacket.frag_len
            offset_len = NetworkPacket.offset_len

            # Iterates until packet is no longer fragmented, will run once if un-fragmented
            while True:

                while (pkt_S is None):
                    # Get the next packet
                    pkt_S = self.in_intf_L[0].get()

                p = NetworkPacket.from_byte_S(pkt_S)  # Decode the acquired packet

                # Acquire header information from the packet
                pid = str(p)[: pid_len]
                frag = int(str(p)[pid_len: pid_len + frag_len])
                offset = int(str(p)[pid_len + frag_len: pid_len + frag_len + offset_len])
                data_S = str(p)[NetworkPacket.header_len:]

                # Determine where to place the acquired data
                # Ignore duplicate packets
                if (pid, offset) in headers:
                    pass
                # Place at the end of the final payload
                elif offset >= max_len:
                    payload = payload + data_S
                # Place at the beginning of the final payload
                elif lb > offset:
                    payload = data_S + payload
                # Place in the middle of the final payload
                elif lb < offset < max_len:
                    payload = payload[:offset] + data_S + payload[offset:]
                # If the data cannot be placed
                else:
                    print("Data not added to payload. Something is wrong.")

                max_len = len(payload) + offset

                if lb > offset:
                    lb = offset

                headers.append((pid, offset))

                # Packet is either un-fragmented, or the final piece of a fragmented packet; either way, end the loop
                if frag == 0:
                    header = str(p)[:NetworkPacket.header_len]
                    break

                # Prepare to receive the next packet after handling the current packet
                pkt_S = None

            print('%s: received packet "%s%s" on the in interface' % (self, header, payload))

    ## Thread target for the host to keep receiving data
    # While true, call udt receive to see if there iss anything new in the 'in' interface
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # Receive data arriving to the in interface
            self.udt_receive()
            # Terminate
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router described in class
class Router:

    ## Constructor for the Router class
    # @param name - Human-readable identifier used for debugging
    # @param in_count - Number of input interfaces used by the Router
    # @param out_count - Number of output interfaces used by the Router
    # @param max_queue_size - The number of packets an interface can hold before denying new receptions
    # @param table - Routing table used by the Router to determine where a given packet should be sent
    def __init__(self, name, in_count, out_count, max_queue_size, table):
        self.stop = False  # Terminates the Router if True
        self.name = name
        # Generate lists of input and output inerfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(in_count)]  # Input
        self.out_intf_L = [Interface(max_queue_size) for _ in range(out_count)]  # Output
        self.table = table

    ## Called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## Look through the content of incoming interfaces and forward any arriving packets to their
    # appropriate interfaces, based on the routing table.
    def forward(self):
        # Search for a packet across all of the Router's input interfaces
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                # Acquire the next available packet, if it exists
                pkt_S = self.in_intf_L[i].get()

                # Begin forwarding if the packet exists
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S)  # Begin parsing the packet
                    pid_len = NetworkPacket.pid_len
                    frag_len = NetworkPacket.frag_len
                    offset_len = NetworkPacket.offset_len
                    dst_addr_S_length = NetworkPacket.dst_addr_S_length
                    src_addr_S_length = NetworkPacket.src_addr_S_length

                    # Extract information from the packet
                    pid = int(str(p)[:pid_len])
                    offset = int(str(p)[pid_len + frag_len: pid_len + frag_len + offset_len])
                    dst_addr = str(p)[pid_len + frag_len + offset_len: pid_len + frag_len + offset_len
                                              + dst_addr_S_length]
                    src_addr = str(p)[pid_len + frag_len + offset_len + dst_addr_S_length: pid_len + frag_len
                                              + offset_len + dst_addr_S_length + src_addr_S_length]
                    data_S = str(p)[NetworkPacket.header_len:]

                    # Determine the output interface based on the source and destination addresses
                    out_interface = self.table[(src_addr, dst_addr)]

                    # Assumes the Router's MTU will not change during execution
                    mtu = self.out_intf_L[0].mtu - NetworkPacket.header_len

                    # Segment the packet if it is longer than the Router's MTU
                    if math.ceil(len(data_S) / mtu) > 1:
                        # Fragments the packet as until all packets are less than the MTU
                        for j in range(math.ceil(len(data_S) / mtu)):
                            # Segmented packets have a frag value of 1, unless they are the final packet
                            frag = 1
                            if j == int(len(data_S) / mtu):
                                frag = 0

                            # Offset determines where the packet is placed during reassembly
                            offset = offset + mtu * j

                            p = NetworkPacket(src_addr, dst_addr, data_S[mtu * j: mtu * (j + 1)], pid, frag, offset)
                            self.out_intf_L[out_interface].put(p.to_byte_S(), True)

                    # Simply resend the packet if it does not require segmentation
                    else:
                        p = NetworkPacket.from_byte_S(pkt_S)
                        self.out_intf_L[out_interface].put(p.to_byte_S(), True)

            except queue.Full:
                print('%s: packet lost on interface %d' % (self, i))
                pass

    ## Thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return
