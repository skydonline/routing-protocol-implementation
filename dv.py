#!/usr/bin/env python3
from netsim.router import Router, RouterNetwork

# Skeleton for distance vector routing


class DVRouter(Router):
    INFINITY = 32

    def send_advertisement(self, time):
        # Construct a DV advertisement and send it on all links.
        adv = self.make_dv_advertisement()
        for link in self.links:
            p = self.network.make_packet(
                self.address,
                self.peer(link),
                'ADVERT',
                time,
                color='red',
                ad=adv
            )
            link.send(self, p)

    # Make a distance vector protocol advertisement, which will be sent
    # by the caller along all the links
    def make_dv_advertisement(self):
        # Simply advertise our current known minimum costs to each destination.
        # (Our own cost is 0, and our spcost dictionary is maintained by updates.)
        return self.spcost.copy()

    def link_failed(self, link):
        # When a link fails, remove all routes that use that link.
        self.clear_routes(link)
        # Optionally, you could also advertise the change immediately.

    def process_advertisement(self, p, link, time):
        # Process the received advertisement by integrating the neighbor's DV.
        changed = self.integrate(link, p.properties['ad'])
        if changed:
            self.send_advertisement(time)

    def integrate(self, link, adv):
        """
        Integrate a neighbor's distance-vector advertisement.

        This method implements the Bellman-Ford update logic. It processes
        the received advertisement and updates the router's routing table
        dynamically.

        :param link: Link object through which the advertisement was received.
        :param adv: Dictionary of received destinations and costs.
        :return: Boolean indicating if any route was updated.

        Note:
        - You must update the following data structures:
          1. `self.spcost`: A dictionary mapping each destination to the current estimated path cost.
          2. `self.routes`: A dictionary mapping each destination to the outgoing `Link` object used as the next hop.
        - Return `True` if any changes are made to these structures; otherwise, return `False`.
        """
        changed = False

        for dest, adv_cost in adv.items():
            # Skip if destination is router itself
            if dest == self.address:
                continue

            # Calculate new cost to destination
            new_cost = link.cost + adv_cost
            if new_cost >= self.INFINITY:
                new_cost = self.INFINITY

            # Get current cost to destination
            current_cost = self.spcost.get(dest, self.INFINITY)

            # Check if current route to dest uses this link
            if self.routes.get(dest) == link:
                # Update cost or remove route if unreachable
                if new_cost != current_cost:
                    if new_cost == self.INFINITY:
                        self.spcost.pop(dest, None)
                        self.routes.pop(dest, None)
                    else:
                        self.spcost[dest] = new_cost
                    changed = True
            elif new_cost < current_cost:
                # Update to use new better route
                self.spcost[dest] = new_cost
                self.routes[dest] = link
                changed = True

        return changed

# A network with nodes of type DVRouter.


class DVRouterNetwork(RouterNetwork):
    # Nodes should be an instance of DVRouter.
    def make_node(self, loc, address=None):
        return DVRouter(loc, address=address)
