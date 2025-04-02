#!/usr/bin/env python3
"""
NetSim: network simulator for routing and transport protocols
"""

import sys
from netsim.router import Router, RouterNetwork

# Skeleton for link‑state routing


class LSRouter(Router):
    INFINITY = sys.maxsize

    def __init__(self, location, address=None):
        Router.__init__(self, location, address=address)
        # LSA: dictionary mapping node addresses to a list:
        # [seqnum, (nbr, cost), (nbr, cost), ...]
        self.LSA = {}
        self.LSA_seqnum = 0  # uniquely identify each LSA broadcast

    def make_ls_advertisement(self):
        # Return a list of all *active* (non‐broken) neighbors.
        # Only advertise links that are not broken.
        return [(self.peer(link), link.cost)
                for link in self.links if not link.broken]

    def send_lsa(self, time):
        self.LSA_seqnum += 1
        lsa_info = self.make_ls_advertisement()
        for link in self.links:
            p = self.network.make_packet(
                self.address,
                self.peer(link),
                'ADVERT',
                time,
                color='red',
                seqnum=self.LSA_seqnum,
                neighbors=lsa_info
            )
            link.send(self, p)

    def send_advertisement(self, time):
        self.send_lsa(time)
        self.clear_stale_lsa(time)

    def clear_stale_lsa(self, time):
        # Clear LSAs whose seqnum is older than (current - 1)
        for key in list(self.LSA.keys()):
            if self.LSA[key][0] < self.LSA_seqnum - 1:
                del self.LSA[key]

    def process_advertisement(self, p, link, time):
        # Process incoming LSA advertisement.
        seq = p.properties['seqnum']
        saved = self.LSA.get(p.source, (-1,))
        if seq > saved[0]:
            if p.properties['neighbors'] is not None:
                self.LSA[p.source] = [seq] + p.properties['neighbors']
            else:
                print(p.properties)
                print('Malformed LSA: No neighbor info in packet. Exiting...')
                sys.exit(1)
            # Rebroadcast the LSA to all neighbors.
            for link in self.links:
                link.send(self, self.network.duplicate_packet(p))

    def get_all_nodes(self):
        # Return a list of all node addresses known via LSAs.
        nodes = [self.address]
        for u in nodes:
            if self.LSA.get(u) is not None:
                lsa_info = self.LSA[u][1:]
                for (nbr, cost) in lsa_info:
                    if nbr not in nodes:
                        nodes.append(nbr)
        return nodes

    def run_dijkstra(self, nodes):
        # Build a graph from the LSAs.
        # For our own node, use our current advertisement.
        graph = {}
        graph[self.address] = self.make_ls_advertisement()
        for u in nodes:
            if u == self.address:
                continue
            # For other nodes, use the stored LSA if available.
            if u in self.LSA:
                graph[u] = self.LSA[u][1:]
            else:
                graph[u] = []  # no information; unreachable

        # Initialize distances.
        dist = {u: self.INFINITY for u in nodes}
        dist[self.address] = 0
        # next_hop[u] will be the first hop from self to u.
        next_hop = {}
        unvisited = set(nodes)
        while unvisited:
            u = min(unvisited, key=lambda x: dist[x])
            unvisited.remove(u)
            for (v, cost) in graph.get(u, []):
                alt = dist[u] + cost
                if alt < dist[v]:
                    dist[v] = alt
                    # If u is self, then next_hop is v; otherwise inherit.
                    if u == self.address:
                        next_hop[v] = v
                    else:
                        next_hop[v] = next_hop.get(u)
        # Save computed costs and set up our routing table.
        self.spcost = dist
        for v in nodes:
            if v == self.address:
                continue
            # Set the route based on the first hop.
            # If no route exists, store None.
            self.routes[v] = self.getlink(next_hop.get(
                v)) if next_hop.get(v) is not None else None

    def integrate(self, time):
        # Rebuild the routing table based on current LSAs.
        self.routes.clear()
        self.routes[self.address] = 'Self'
        # Our own LSA is always up to date.
        self.LSA[self.address] = [self.LSA_seqnum] + \
            self.make_ls_advertisement()
        nodes = self.get_all_nodes()
        self.spcost = {u: self.INFINITY for u in nodes}
        self.spcost[self.address] = 0
        self.run_dijkstra(nodes)

    def transmit(self, time):
        Router.transmit(self, time)
        # At half the ADVERT_INTERVAL, rebuild our routing table.
        if (time % self.ADVERT_INTERVAL) == self.ADVERT_INTERVAL / 2:
            self.integrate(time)

    def OnClick(self, which):
        if which == 'left':
            print(self)
            print('  LSA:')
            for key, value in self.LSA.items():
                print('    ', key, ': ', value)
        Router.OnClick(self, which)

# A network with nodes of type LSRouter.


class LSRouterNetwork(RouterNetwork):
    def make_node(self, loc, address=None):
        return LSRouter(loc, address=address)
