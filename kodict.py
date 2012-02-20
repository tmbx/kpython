"""
Ordered dict
might not be fully compatible with dict yet
"""

class odict(dict):
    def __init__(self, data=None):
        self._keys = []
        dict.__init__(self)

        if data:
            # we were provided a regular dict
            if isinstance(data, dict):
                self.append_from_dict(data)

            # we were provided a tuple list
            elif type(data) == list:
                self.append_from_plist(data)

            # we were provided invalid input
            else:
                raise Exception("expected a dict or a tuple list")

    def append_from_dict(self, dict):
        map(self.__setitem__, dict.keys(), dict.values())

    def append_from_plist(self, plist):
        for pair in plist:
            if len(pair) != 2:
                raise Exception("invalid pairs list")
        for (k, v) in plist:
            self.__setitem__(k, v)

    def __delitem__(self, key):
        if not key in self._keys:
            raise KeyError, key
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        if key not in self._keys:
            self._keys.append(key)

    def clear(self):
        dict.clear(self)
        self._keys = []

    def copy(self):
        return odict(self.plist())

    def items(self):
        return zip(self._keys, self.values())

    def keys(self):
        return list(self._keys) # return a copy of the list

    def values(self):
        return map(self.get, self._keys)

    def plist(self):
        p = []
        for k, v in self.items():
            p.append( (k, v) )
        return p

    def __str__(self):
        s = "{"
        l = len(self._keys)
        for k, v in self.items():
            l -= 1
            strkey = str(k)
            if isinstance(k, basestring): strkey = "'"+strkey+"'"
            strval = str(v)
            if isinstance(v, basestring): strval = "'"+strval+"'"
            s += strkey + ":" + strval
            if l > 0: s += ", "
        s += "}"
        return s

# non-exhaustive tests
if __name__ == "__main__":
    # create an ordered dict
    # initial values are passed using a regular dict, so they might be ordered randomly
    t = odict({"a" : "aa 1", "z" : "zz 1", "g" : "gg 1"}) # creates ordered dict, but can't order the initial dictionnary
    print t._keys
    print str(t) + "\n\n"
    
    # add values... they should be ordered from now on
    t["y"] = "yy 2"
    t["e"] = "ee 2"
    t["k"] = "kk 2"
    t["z"] = "zz 2"
    print t._keys
    print str(t) + "\n\n"

    # make a copy
    y = t.copy()
    print str(t) + "\n"
    print str(y) + "\n\n"

    # change value in t.. y should not be affected
    t["gfgdfgdfg"] = "kgskfg;ldfg"
    print str(t) + "\n"
    print str(y) + "\n\n"

    # clear t
    t.clear()
    print t

    # repopulate t
    t["t"] = "t 1"
    t["g"] = "gg 1"
    t["z"] = "zz 1"
    print t


