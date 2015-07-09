# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
"""
Generate TMS sequences for JTAG TAP state machine transitions

Note:
State names are taken from the SVF file specification.
This keeps things simple when processing SVF files.

"""
#-----------------------------------------------------------------------------

state_machine = {
    'RESET': ('IDLE','RESET'),
    'IDLE': ('IDLE','DRSELECT'),
    'DRSELECT': ('DRCAPTURE','IRSELECT'),
    'DRCAPTURE': ('DRSHIFT','DREXIT1'),
    'DRSHIFT': ('DRSHIFT','DREXIT1'),
    'DREXIT1': ('DRPAUSE','DRUPDATE'),
    'DRPAUSE': ('DRPAUSE','DREXIT2'),
    'DREXIT2': ('DRSHIFT','DRUPDATE'),
    'DRUPDATE': ('IDLE','DRSELECT'),
    'IRSELECT': ('IRCAPTURE','RESET'),
    'IRCAPTURE': ('IRSHIFT','IREXIT1'),
    'IRSHIFT': ('IRSHIFT','IREXIT1'),
    'IREXIT1': ('IRPAUSE','IRUPDATE'),
    'IRPAUSE': ('IRPAUSE','IREXIT2'),
    'IREXIT2': ('IRSHIFT','IRUPDATE'),
    'IRUPDATE': ('IDLE','DRSELECT'),
}

def search(path, current, dst):
    """return the shortest state path linking src and dst states"""
    # are we done?
    if current == dst:
        return path
    # get the two outgoing states
    (state0, state1) = state_machine[current]
    # search paths with state0
    if state0 in path:
        # looping - not the shortest path
        path0 = None
    else:
        path0 = list(path)
        path0.append(state0)
        path0 = search(path0, state0, dst)
    # search paths with state1
    if state1 in path:
        # looping - not the shortest path
        path1 = None
    else:
        path1 = list(path)
        path1.append(state1)
        path1 = search(path1, state1, dst)
    # return the shortest path
    if path0 is None:
        return path1
    if path1 is None:
        return path0
    return path0 if len(path0) < len(path1) else path1

def tms(path, current):
    """return a tms bit tuple from the current state along the path"""
    s = []
    for state in path:
        s.append(state_machine[current].index(state))
        current = state
    return tuple(s)

#-----------------------------------------------------------------------------

class tap(object):
    """JTAG TAP State Machine"""

    def __init__(self):
        """build and cache all state transitions for fast lookup"""
        self.cache = {}
        states = state_machine.keys()
        for src in states:
            for dst in states:
                path = search([], src, dst)
                self.cache['%s->%s' % (src, dst)] = tms(path, src)
        # any state to RESET
        self.cache['*->RESET'] = (1,1,1,1,1)

    def tms(self, src, dst):
        return self.cache['%s->%s' % (src, dst)]

#-----------------------------------------------------------------------------
