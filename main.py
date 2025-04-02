#!/usr/bin/env python3
"""
Main script for NetSim.
"""

import random
from optparse import OptionParser
from netsim.simulation import RandomGraph
from netsim.gui import NetSim
from dv import DVRouterNetwork
from ls import LSRouterNetwork
import tests.tests as tests


def main():
    parser = OptionParser()
    parser.add_option("-g", "--gui", action="store_true", dest="gui",
                      default=False, help="show GUI")
    parser.add_option("-n", "--numnodes", type="int", dest="numnodes",
                      default=12, help="number of nodes")
    parser.add_option("-a", "--algorithm", type="string", dest="algorithm",
                      default="dv", help="routing algorithm (dv or ls)")
    parser.add_option("-t", "--simtime", type="int", dest="simtime",
                      default=2000, help="simulation time")
    parser.add_option("-r", "--rand", action="store_true", dest="rand",
                      default=False, help="use randomly generated topology")
    # parser.add_option("-l", "--loss", type="float", dest="lossprob",
    #                   default=0.0, help="link packet loss probability")

    (opt, args) = parser.parse_args()

    if opt.rand:
        rg = RandomGraph(opt.numnodes)
        (NODES, LINKS) = rg.genGraph()
    else:
        # Deterministic test network:
        #   A---B   C---D
        #   |   | / | / |
        #   E   F---G---H
        NODES = (('A', 0, 0), ('B', 1, 0), ('C', 2, 0), ('D', 3, 0),
                 ('E', 0, 1), ('F', 1, 1), ('G', 2, 1), ('H', 3, 1))
        LINKS = (('A', 'B'), ('A', 'E'), ('B', 'F'), ('E', 'F'),
                 ('C', 'D'), ('C', 'F'), ('C', 'G'),
                 ('D', 'G'), ('D', 'H'), ('F', 'G'), ('G', 'H'))

    if opt.algorithm == "dv":
        RouterNetwork = DVRouterNetwork
    elif opt.algorithm == "ls":
        RouterNetwork = LSRouterNetwork
    else:
        print("Unknown algorithm:", opt.algorithm)
        return
    print("Using", RouterNetwork.__name__)

    if opt.gui:
        net = RouterNetwork(opt.simtime, NODES, LINKS, 0)
        sim = NetSim()
        sim.SetNetwork(net)
        sim.MainLoop()
    else:
        tests.verify_routes(RouterNetwork)


if __name__ == '__main__':
    main()
