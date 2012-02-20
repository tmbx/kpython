"""
Class with a custom parameters checker (when they are used as __optional__ parameters)

All options must be specified as option=value... see the test at the end of file.
"""

class OptionNotSet(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)

class BadOption(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)


class Options(object):
    def store_options(self, options):
        """
        Store options in a private attribute for later processing
        """

        if not self.__dict__.has_key("_options"):
            self._options = options
            self._used_options = []


    def is_option_set(self, option_name):
        """
        Check if option was set or not.
        """

        return (self._options.has_key(option_name))        


    def get_option(self, option_name, **options):
        """
        Get an option - or raise if required is True - or raise
        possible options: default_value, required

        By default, options are not required and have 'None' as the default value
        """

        required = False
        if options.has_key("required"):
            required = options["required"]
        default_value = None
        if options.has_key("default_value"):
            default_value = options["default_value"]
              
        if self.is_option_set(option_name):
            self._used_options.append(option_name)
            return self._options[option_name]
        if required:
            raise OptionNotSet(option_name)
        return default_value
            

    def check_unused_options(self):
        for option in self._options.keys():
            if not option in self._used_options:
                raise BadOption(option)


if __name__ == "__main__":
    # non-exhaustive testing
    class OptionsDemo(Options):
        def __init__(self, **options):
            self.store_options(options)

            print "x value: " + str(self.get_option("x", default_value=5))

            print "y value: " + str(self.get_option("y", required=True))

            self.check_unused_options()


    print "Test 1"
    c = OptionsDemo(y="y is a great letter.")
    print 

    print "Test 2"
    c = OptionsDemo(x="x is a great letter.", y="y is a great letter.")
    print


    print "Test 3"
    try:
        c = OptionsDemo()
        print "ERROR: got no exception but should have."
    except OptionNotSet, e:
        print "Got exception OptionNotSet for the required option '%s', which is correct." % ( str(e) )
    print


    print "Test 4"
    try:
        c = OptionsDemo(y="y is a great letter.", bad_option=3)
        print "ERROR: got no exception but should have."
    except BadOption, e:
        print "Got exception BadOption for the option '%s', which is correct." % ( str(e) )


