#!/usr/bin/env python3
"""
Router module for NetSim, includes Router and RouterNetwork.
"""

import random
from .simulation import Node, LossyCostLink, Network


class Router(Node):
    HELLO_INTERVAL = 10
    ADVERT_INTERVAL = 30

    def __init__(self, location, address=None):
        super().__init__(location, address=address)
        self.neighbors = {}
        self.routes = {}
        self.routes[self.address] = 'Self'
        self.spcost = {self.address: 0}
        self.hello_offset = random.randint(0, self.HELLO_INTERVAL - 1)
        self.ad_offset = random.randint(0, self.ADVERT_INTERVAL - 1)
        # For simplicity, you may override these:
        self.hello_offset = 0
        self.ad_offset = 0

    def reset(self):
        super().reset()
        self.neighbors = {}
        self.routes = {self.address: 'Self'}
        self.spcost = {self.address: 0}

    def getlink(self, nbhr):
        if self.address == nbhr:
            return None
        for l in self.links:
            if l.end2.address == nbhr or l.end1.address == nbhr:
                return l
        return None

    def peer(self, link):
        if link.end1.address == self.address:
            return link.end2.address
        if link.end2.address == self.address:
            return link.end1.address

    def forward(self, p):
        link = self.routes.get(p.destination)
        if link is None:
            print('No route for ', p, ' at node ', self)
        else:
            print('sending packet')
            link.send(self, p)

    def process(self, p, link, time):
        if p.type == 'HELLO':
            self.neighbors[link] = (time, p.source, link.cost)
        elif p.type == 'ADVERT':
            self.process_advertisement(p, link, time)
        else:
            super().process(p, link, time)

    def process_advertisement(self, p, link, time):
        # You can implement your route advertisement integration here.
        self.integrate(link, p.properties['ad'])

    def sendHello(self, time):
        for link in self.links:
            p = self.network.make_packet(self.address, self.peer(link),
                                         'HELLO', time, color='green')
            link.send(self, p)

    def clearStaleHello(self, time):
        old = time - 2 * self.HELLO_INTERVAL
        for link in list(self.neighbors.keys()):
            if self.neighbors[link][0] <= old:
                del self.neighbors[link]
                self.link_failed(link)

    def link_failed(self, link):
        pass

    def clear_routes(self, link):
        clear_list = [dest for dest, lnk in self.routes.items() if lnk == link]
        for dest in clear_list:
            print(self.address, ' clearing route to ', dest)
            del self.routes[dest]
            del self.spcost[dest]

    def transmit(self, time):
        if (time % self.HELLO_INTERVAL) == self.hello_offset:
            self.sendHello(time)
            self.clearStaleHello(time)
        if (time % self.ADVERT_INTERVAL) == self.ad_offset:
            self.send_advertisement(time)
        super().transmit(time)

    def OnClick(self, which):
        if which == 'left':
            print(self)
            print('  neighbors:', list(self.neighbors.values()))
            print('  routes:')
            for key, value in self.routes.items():
                print('    ', key, ': ', value,
                      f'pathcost {self.spcost[key]:.2f}')


class RouterNetwork(Network):
    def __init__(self, SIMTIME, NODES, LINKS, LOSSPROB):
        super().__init__(SIMTIME)
        self.lossprob = LOSSPROB
        for n, r, c in NODES:
            self.add_node(r, c, address=n)
        for a1, a2 in LINKS:
            n1 = self.addresses[a1]
            n2 = self.addresses[a2]
            self.add_link(n1.location[0], n1.location[1],
                          n2.location[0], n2.location[1])

    def make_node(self, loc, address=None):
        return Router(loc, address=address)

    def make_link(self, n1, n2):
        return LossyCostLink(n1, n2, self.lossprob)

    def reset(self):
        super().reset()
        src = random.choice(self.nlist)
        dest = random.choice(self.nlist)
        packet = self.make_packet(src.address, dest.address, 'DATA', 20)
        print(f"Created packet from {src.address} to {dest.address}")
        src.add_packet(packet)
