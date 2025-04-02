#!/usr/bin/env python3
"""
GUI module for NetSim using wxPython.
"""

import sys
import time
import wx


def net2screen(loc, transform):
    return (int(transform[1][0] + loc[0] * transform[0]),
            int(transform[1][1] + loc[1] * transform[0]))


def screen2net(loc, transform):
    return (float(loc[0] - transform[1][0]) / transform[0],
            float(loc[1] - transform[1][1]) / transform[0])


def draw_node(dc, transform, node):
    """Draw a single node (square + label)."""
    nsize = int(transform[0] / 16)
    loc = net2screen(node.location, transform)

    # Node square
    dc.SetPen(wx.Pen('black', 1, wx.SOLID))
    dc.SetBrush(wx.Brush(node.properties.get('color', 'black')))
    dc.DrawRectangle(loc[0] - nsize, loc[1] - nsize,
                     2 * nsize + 1, 2 * nsize + 1)

    # Label
    label = str(node.address)
    dc.SetTextForeground('light grey')
    dc.SetFont(wx.Font(max(4, nsize * 2), wx.FONTFAMILY_SWISS,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    dc.DrawText(label, int(loc[0] + nsize + 2), int(loc[1] + nsize + 2))

    # Optionally draw something for the first packet in the transmit queue
    if node.transmit_queue:
        draw_packet(dc, transform, node.transmit_queue[0],
                    loc[0] - 2*nsize, loc[1] - 2*nsize)


def draw_link(dc, transform, link):
    """Draw a link (line + cost + possibly broken 'X')."""
    nsize = int(transform[0] / 16)
    n1 = net2screen(link.end1.location, transform)
    n2 = net2screen(link.end2.location, transform)

    # Link line
    dc.SetPen(wx.Pen('black', 1, wx.SOLID))
    dc.SetBrush(wx.TRANSPARENT_BRUSH)
    dc.DrawLine(n1[0], n1[1], n2[0], n2[1])

    # Link cost label
    dc.SetTextForeground('light grey')
    dc.SetFont(wx.Font(max(4, nsize * 2), wx.FONTFAMILY_SWISS,
                       wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
    midx = (n1[0] + n2[0]) / 2
    midy = (n1[1] + n2[1]) / 2
    dc.DrawText(link.costrepr, int(midx), int(midy))

    # Broken link "X"
    if link.broken:
        dc.SetPen(wx.Pen('red', 3, wx.SOLID))
        offset = 0.1 * transform[0]
        dc.DrawLine(int(midx - offset), int(midy - offset),
                    int(midx + offset), int(midy + offset))
        dc.DrawLine(int(midx + offset), int(midy - offset),
                    int(midx - offset), int(midy + offset))

    # If there's a packet in the queue, draw it
    if link.q21:
        draw_packet_on_link(dc, transform, link.q21[0], n1, n2)
    if link.q12:
        draw_packet_on_link(dc, transform, link.q12[0], n2, n1)


def draw_packet(dc, transform, packet, px, py):
    """Draw a packet as a small circle."""
    c = packet.properties.get('color', 'blue')
    dc.SetPen(wx.Pen(c, 1, wx.SOLID))
    dc.SetBrush(wx.Brush(c))
    radius = int(transform[0] / 16)
    dc.DrawCircle(int(px), int(py), radius)


def draw_packet_on_link(dc, transform, packet, n1, n2):
    """Position the packet on the link between n1 and n2."""
    px = n1[0] + int(0.2 * (n2[0] - n1[0]))
    py = n1[1] + int(0.2 * (n2[1] - n1[1]))
    draw_packet(dc, transform, packet, px, py)


class NetPanel(wx.Panel):
    def __init__(self, parent, statusbar):
        super().__init__(parent, -1, wx.DefaultPosition, (10, 10))
        self.SetBackgroundColour('white')
        self.SetMinSize((100, 100))
        self.statusbar = statusbar
        self.network = None
        self.setupBuffer = False
        self.redraw = False
        self.playmode = False
        self.lastplaytime = 0
        self.transform = (2, (0, 0))
        self.SetupBuffer()
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftClick)

    def SetupBuffer(self):
        size = self.GetClientSize()
        self.buffer = wx.Bitmap(size.width, size.height)
        self.setupBuffer = False
        self.redraw = True

    def OnSize(self, event):
        self.setupBuffer = True

    def OnClick(self, event, which):
        pos = screen2net(event.GetPosition(), self.transform)
        if self.network.click(pos, which):
            self.redraw = True

    def OnLeftClick(self, event):
        self.OnClick(event, 'left')

    def OnMotion(self, event):
        pos = screen2net(event.GetPosition(), self.transform)
        self.network.status(self.statusbar, pos)

    def OnIdle(self, event):
        if self.setupBuffer:
            self.SetupBuffer()
        if self.redraw:
            self.DrawNetwork()
            self.Refresh(False)
            self.redraw = False
            self.network.status(self.statusbar, (-10, -10))
        if self.playmode:
            self.redraw = True
            curtime = time.perf_counter()
            if curtime - self.lastplaytime > self.network.playstep:
                if self.network.simtime > self.network.time:
                    self.network.step(1)
                    self.lastplaytime = curtime
                else:
                    self.playmode = False
            event.RequestMore()

    def OnPaint(self, event):
        wx.BufferedPaintDC(self, self.buffer)

    def OnReset(self, event):
        self.network.reset()
        self.network.status(self.statusbar, (-10, -10))
        self.redraw = True

    def OnStep(self, event):
        button = event.GetEventObject().GetLabel()
        arg = button[button.find(' '):]
        count = (self.network.simtime -
                 self.network.time) if arg == ' all' else int(arg)
        self.network.step(count=count)
        self.network.status(self.statusbar, (-10, -10))
        self.redraw = True

    def OnPlay(self, event):
        self.playmode = True

    def OnPause(self, event):
        self.playmode = False

    def OnNNodes(self, event):
        nnodes = event.GetEventObject().GetValue()
        self.network.set_nodes(nnodes)
        self.redraw = True

    def OnExit(self, event):
        self.network.status(self.statusbar, (-10, -10))
        self.redraw = True
        sys.exit(1)

    def DrawNetwork(self):
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        size = self.GetClientSize()
        netsize = (self.network.max_x + 1, self.network.max_y + 1)
        grid = min(size[0] / netsize[0], size[1] / netsize[1])
        xoffset = (size[0] - (netsize[0] - 1) * grid) / 2
        yoffset = (size[1] - (netsize[1] - 1) * grid) / 2
        self.transform = (grid, (xoffset, yoffset))

        # Draw each link
        for link in self.network.links:
            draw_link(dc, self.transform, link)

        # Draw each node
        for node in self.network.nlist:
            draw_node(dc, self.transform, node)

    def SetNetwork(self, network):
        self.network = network
        self.network.reset()
        self.redraw = True


class NetFrame(wx.Frame):
    def __init__(self, parent=None, id=-1, size=(1000, 500),
                 pos=wx.DefaultPosition, title='NetSim'):
        super().__init__(parent, id, title, pos, size)
        self.SetBackgroundColour('white')
        statusbar = self.CreateStatusBar()
        self.netpanel = NetPanel(self, statusbar)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add(self.netpanel, 1, flag=wx.EXPAND)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, 0, flag=wx.EXPAND)

        # Create buttons
        def create_button(label, handler):
            btn = wx.Button(self, -1, label)
            btn.SetForegroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT))
            btn.SetBackgroundColour(
                wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            self.Bind(wx.EVT_BUTTON, handler, btn)
            hsizer.Add(btn, 1)

        create_button('Reset', self.netpanel.OnReset)
        create_button('Step 1', self.netpanel.OnStep)
        create_button('Step 10', self.netpanel.OnStep)
        create_button('Step 100', self.netpanel.OnStep)
        create_button('Step all', self.netpanel.OnStep)
        create_button('Play', self.netpanel.OnPlay)
        create_button('Pause', self.netpanel.OnPause)
        create_button('Exit', self.netpanel.OnExit)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(vsizer, 1, flag=wx.EXPAND)
        self.SetSizer(mainSizer)

    def SetNetwork(self, network):
        self.netpanel.SetNetwork(network)


class NetSim(wx.App):
    def OnInit(self):
        self.frame = NetFrame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

    def SetNetwork(self, network):
        self.frame.SetNetwork(network)
