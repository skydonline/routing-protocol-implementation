#!/usr/bin/env python3
"""
Simulation module for NetSim: network simulator for routing and transport protocols.
"""

import random
import math


def nearby(pt, end1, end2, distance):
    if end1[0] == end2[0]:
        if abs(pt[0] - end1[0]) > distance:
            return False
        y1 = min(end1[1], end2[1])
        y2 = max(end1[1], end2[1])
        return pt[1] >= y1 - distance and pt[1] <= y2 + distance
    elif end1[1] == end2[1]:
        if abs(pt[1] - end1[1]) > distance:
            return False
        x1 = min(end1[0], end2[0])
        x2 = max(end1[0], end2[0])
        return pt[0] >= x1 - distance and pt[0] <= x2 + distance
    else:
        slope1 = float(end1[1] - end2[1]) / (end1[0] - end2[0])
        intercept1 = float(end1[1]) - slope1 * end1[0]
        slope2 = -1 / slope1
        intercept2 = float(pt[1]) - slope2 * pt[0]
        xi = (intercept2 - intercept1) / (slope1 - slope2)
        if xi < min(end1[0], end2[0]) or xi > max(end1[0], end2[0]):
            return False
        dx = pt[0] - xi
        dy = pt[1] - (slope2 * xi + intercept2)
        return (dx * dx) + (dy * dy) <= distance * distance


class Node:
    def __init__(self, location, address=None):
        self.location = location
        self.address = address if address is not None else location
        self.links = []             # links that connect to this node
        self.packets = []           # packets to be processed this timestep
        self.transmit_queue = []    # packets to be transmitted
        self.receive_queue = []     # packets received
        self.properties = {}
        self.network = None         # will be set later
        self.nsize = 0              # for drawing

    def __repr__(self):
        return f'Node<{self.address}>'

    def reset(self):
        for l in self.links:
            l.reset()
        self.transmit_queue = []
        self.receive_queue = []
        self.queue_length_sum = 0
        self.queue_length_max = 0
        if hasattr(self, 'neighbors'):
            self.neighbors.clear()
        if hasattr(self, 'routes'):
            self.routes.clear()
            self.routes[self.address] = 'Self'
        self.properties.clear()

    def add_link(self, l):
        self.links.append(l)

    def add_packet(self, p):
        index = 0
        for pp in self.transmit_queue:
            if p.start < pp.start:
                self.transmit_queue.insert(index, p)
                break
            index += 1
        else:
            self.transmit_queue.append(p)

    def phase1(self):
        self.packets = [link.receive(self) for link in self.links]

    def phase2(self, time):
        for link_p in self.packets:
            if link_p is not None:
                self.process(link_p[1], link_p[0], time)
        self.packets = []
        self.transmit(time)
        pending = sum(link.queue_length(self) for link in self.links)
        self.queue_length_sum += pending
        self.queue_length_max = max(self.queue_length_max, pending)
        return pending + len(self.transmit_queue)

    def receive(self, p, link):
        self.receive_queue.append(p)

    def transmit(self, time):
        while self.transmit_queue and self.transmit_queue[0].start <= time:
            print(
                f"Transmitting packet {self.transmit_queue[0]} at node {self.address}")
            self.process(self.transmit_queue.pop(0), None, time)

    def forward(self, p):
        print(
            f"Forwarding packet from {self.address} destined for {p.destination}")
        link = random.choice(self.links)
        link.send(self, p)

    def process(self, p, link, time):
        if p.destination == self.address:
            p.finish = time
            self.receive(p, link)
        else:
            p.add_hop(self, time)
            self.forward(p)

    def nearby(self, pos):
        dx = self.location[0] - pos[0]
        dy = self.location[1] - pos[1]
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return self.status()
        elif self.transmit_queue:
            if (0.1 < abs(dx) < 0.2) and (0.1 < abs(dy) < 0.2):
                return 'Unsent ' + self.transmit_queue[0].status()
        return None

    def click(self, pos, which):
        dx = self.location[0] - pos[0]
        dy = self.location[1] - pos[1]
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            self.OnClick(which)
            return True
        return False

    def OnClick(self, which):
        pass

    def status(self):
        return self.__repr__()


class Link:
    def __init__(self, n1, n2):
        self.end1 = n1
        self.end2 = n2
        self.q12 = []
        self.q21 = []
        self.cost = 1
        self.costrepr = str(self.cost)
        self.network = None
        n1.add_link(self)
        n2.add_link(self)
        self.broken = False

    def __repr__(self):
        return f'link({self.end1}<-->{self.end2}) ({self.cost:.1f})'

    def reset(self):
        self.q12 = []
        self.q21 = []

    def queue_length(self, n):
        if n == self.end1:
            return len(self.q12)
        elif n == self.end2:
            return len(self.q21)
        else:
            raise Exception('Node not part of this link.')

    def receive(self, n):
        if n == self.end1:
            return (self, self.q21.pop(0)) if self.q21 else None
        elif n == self.end2:
            return (self, self.q12.pop(0)) if self.q12 else None
        else:
            raise Exception('Node not part of this link.')

    def send(self, n, p):
        if self.broken:
            return
        if n == self.end1:
            self.q12.append(p)
        elif n == self.end2:
            self.q21.append(p)
        else:
            raise Exception('Node not part of this link.')

    def nearby(self, pos):
        msg = None
        if self.q21:
            msg = self.q21[0].nearby(
                pos, self.end1.location, self.end2.location)
        if msg is None and self.q12:
            msg = self.q12[0].nearby(
                pos, self.end2.location, self.end1.location)
        return msg

    def click(self, pos, which):
        if nearby(pos, self.end1.location, self.end2.location, 0.1):
            self.broken = not self.broken
            if self.broken:
                self.reset()
            return True
        return False


class CostLink(Link):
    def __init__(self, n1, n2):
        super().__init__(n1, n2)
        loc1 = n1.location
        loc2 = n2.location
        dx2 = (loc1[0] - loc2[0]) ** 2
        dy2 = (loc1[1] - loc2[1]) ** 2
        self.cost = math.sqrt(dx2 + dy2)
        if int(self.cost) == self.cost:
            self.costrepr = str(self.cost)
        else:
            self.costrepr = "sqrt(" + str(dx2 + dy2) + ")"

    def set_cost(self, cost):
        self.cost = cost


class LossyCostLink(CostLink):
    def __init__(self, n1, n2, lossprob):
        super().__init__(n1, n2)
        self.lossprob = lossprob
        self.linkloss = 0

    def send(self, n, p):
        if random.random() > self.lossprob:
            super().send(n, p)
        else:
            self.linkloss += 1


class Packet:
    def __init__(self, src, dest, type, start, **props):
        self.source = src
        self.destination = dest
        self.type = type
        self.start = start
        self.finish = None
        self.route = []
        self.network = None
        self.properties = props.copy()

    def __repr__(self):
        return f'Packet<{self.source} to {self.destination}> type {self.type}'

    def add_hop(self, n, time):
        self.route.append((n, time))

    def nearby(self, pos, n1, n2):
        px = n1[0] + 0.2 * (n2[0] - n1[0])
        py = n1[1] + 0.2 * (n2[1] - n1[1])
        dx = px - pos[0]
        dy = py - pos[1]
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            return self.status()
        return None

    def status(self):
        return self.__repr__()


class Network:
    def __init__(self, simtime):
        self.nodes = {}
        self.addresses = {}
        self.nlist = []
        self.links = []
        self.time = 0
        self.pending = 0
        self.packets = []
        self.npackets = 0
        self.max_x = 0
        self.max_y = 0
        self.simtime = simtime
        self.playstep = 1.0
        self.numnodes = 0

    def make_node(self, loc, address=None):
        return Node(loc, address=address)

    def add_node(self, x, y, address=None):
        n = self.find_node(x, y)
        if n is None:
            n = self.make_node((x, y), address=address)
            n.network = self
            if address is not None:
                self.addresses[address] = n
            self.nlist.append(n)
            ynodes = self.nodes.get(x, {})
            ynodes[y] = n
            self.nodes[x] = ynodes
            self.max_x = max(self.max_x, x)
            self.max_y = max(self.max_y, y)
        return n

    def set_nodes(self, n):
        self.numnodes = n

    def find_node(self, x, y):
        ynodes = self.nodes.get(x)
        return ynodes.get(y) if ynodes else None

    def map_node(self, f, default=0):
        result = []
        for row in range(self.max_y + 1):
            for col in range(self.max_x + 1):
                node = self.find_node(row, col)
                result.append(f(node) if node else default)
        return result

    def make_link(self, n1, n2):
        return Link(n1, n2)

    def add_link(self, x1, y1, x2, y2):
        n1 = self.find_node(x1, y1)
        n2 = self.find_node(x2, y2)
        if n1 and n2:
            link = self.make_link(n1, n2)
            link.network = self
            self.links.append(link)

    def make_packet(self, src, dest, type, start, **props):
        p = Packet(src, dest, type, start, **props)
        p.network = self
        self.packets.append(p)
        self.npackets += 1
        return p

    def duplicate_packet(self, old):
        return self.make_packet(old.source, old.destination, old.type, self.time,
                                **old.properties)

    def manhattan_distance(self, n1, n2):
        dx = n1[0] - n2[0]
        dy = n1[1] - n2[1]
        return abs(dx) + abs(dy)

    def reset(self):
        for n in self.nlist:
            n.reset()
        self.time = 0
        self.pending = 0
        self.packets = []
        self.npackets = 0
        self.pending = 1

    def step(self, count=1):
        stop_time = self.time + count
        while self.time < stop_time:
            for n in self.nlist:
                n.phase1()
            self.pending = sum(n.phase2(self.time) for n in self.nlist)
            self.time += 1
        return self.pending

    def click(self, pos, which):
        for node in self.nlist:
            if node.click(pos, which):
                return True
        for link in self.links:
            if link.click(pos, which):
                return True
        return False

    def status(self, statusbar, pos):
        msg = ''
        for node in self.nlist:
            msg = node.nearby(pos)
            if msg:
                break
        else:
            for link in self.links:
                msg = link.nearby(pos)
                if msg:
                    break
        statusbar.SetFieldsCount(4)
        statusbar.SetStatusWidths([80, 80, 80, -1])
        statusbar.SetStatusText(f'Time: {self.time}', 0)
        statusbar.SetStatusText(f'Pending: {self.pending}', 1)
        statusbar.SetStatusText(f'Total: {self.npackets}', 2)
        statusbar.SetStatusText(f'Status: {msg}', 3)


class GridNetwork(Network):
    def __init__(self, nrows, ncols):
        super().__init__(simtime=0)
        grid_node_names = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot',
                           'golf', 'hotel', 'india', 'juliet', 'kilo', 'lima', 'mike',
                           'november', 'oscar', 'papa', 'quebec', 'romeo', 'sierra',
                           'tango', 'uniform', 'victor', 'whiskey', 'xray', 'yankee',
                           'zulu']
        for r in range(nrows):
            for c in range(ncols):
                index = r * ncols + c
                addr = grid_node_names[index % len(grid_node_names)]
                if index >= len(grid_node_names):
                    addr += str(index // len(grid_node_names))
                self.add_node(r, c, address=addr)
        for r in range(nrows):
            for c in range(ncols):
                if c > 0:
                    self.add_link(r, c, r, c - 1)
            for c in range(ncols):
                if r > 0:
                    self.add_link(r, c, r - 1, c)


class RandomGraph:
    def __init__(self, numnodes=8):
        self.numnodes = max(5, min(numnodes, 26))
        self.names = ['A', 'B', 'C', 'D', 'E',
                      'F', 'G', 'H', 'I', 'J',
                      'K', 'L', 'M', 'N', 'O',
                      'P', 'Q', 'R', 'S', 'T',
                      'U', 'V', 'W', 'X', 'Y', 'Z']
        self.maxRows = math.ceil(math.sqrt(self.numnodes))
        self.maxCols = math.ceil(math.sqrt(self.numnodes))

    def getCoord(self, i):
        x = i % self.maxCols
        y = i // self.maxCols
        return (x, y)

    def getIndex(self, x, y):
        if x < 0 or y < 0 or x >= self.maxCols or y >= self.maxRows:
            return -1
        ind = y * self.maxCols + x
        return ind if ind < self.numnodes else -1

    def getAllNgbrs(self, i):
        (x, y) = self.getCoord(i)
        ngbrs = []
        for nx in [x - 1, x, x + 1]:
            for ny in [y - 1, y, y + 1]:
                if not (nx == x and ny == y):
                    ind = self.getIndex(nx, ny)
                    if ind >= 0:
                        ngbrs.append(ind)
        return ngbrs

    def checkLinkExists(self, links, a, b):
        for (c, d) in links:
            if (a == c and b == d) or (a == d and b == c):
                return True
        return False

    def genGraph(self):
        NODES = []
        LINKS = []
        for i in range(self.numnodes):
            (x, y) = self.getCoord(i)
            name = self.names[i]
            NODES.append((name, x, y))
        for i in range(self.numnodes):
            ngbrs = self.getAllNgbrs(i)
            outdeg = int(random.random() * len(ngbrs)) + 1
            sampleNgbrs = random.sample(ngbrs, outdeg)
            for n1 in sampleNgbrs:
                n = int(n1)
                if not self.checkLinkExists(LINKS, self.names[i], self.names[n]):
                    LINKS.append((self.names[i], self.names[n]))
        return (NODES, LINKS)
