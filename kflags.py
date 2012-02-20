import re

# This class represents a flags store.
#
# Example usage:
#
#   class CarFlags(Flags):
#       HATCH_BACK = 1<<1
#       AIR_BAGS = 1<<2
#       RADIO_CD = 1<<3
#
#   cf = CarFlags(CarFlags.HATCH_BACK | CarFlags.AIR_BAGS)
#   print cf.hasFlags(CarFlags.AIR_BAGS)
#   print cf.hasFlags(CarFlags.RADIO_CD)
#   print cf.hasFlags(CarFlags.HATCH_BACK | CarFlags.AIR_BAGS)
#   print cf.hasFlags(CarFlags.HATCH_BACK | CarFlags.RADIO_CD)
#   print cf.setFlagsToStr()
#
class Flags:

    # Constructor
    def __init__(self, flags=0):
        self._flags = flags

    # Set flags.
    def setFlags(self, flags):
        self._flags = flags

    # Add flags.
    def addFlags(self, flags):
        self._flags = self._flags | flags

    # Remove flags. TODO
    #def remFlags(self, flags):
    #    self._flags = ???? 

    # Check if flag is set.
    def hasFlags(self, flags):
        if (self._flags & flags) == flags: return True
        return False

    # Return a dict containing all flags.
    # Only class attributes (not instance attributes) that match '^[A-Z0-9_]+$'
    #  are considered to be flags.
    def flags(self):
        d = {}
        for name, value in self.__class__.__dict__.items():
            if re.match('^[A-Z0-9_]+$', name):
                d[name] = value
        return d

    # Return a string with set flags.
    def setFlagsToStr(self):
        arr = []
        for name, value in self.flags().items():
            if self.hasFlags(value): arr.append(name)
        return " ".join(arr)


