#!/usr/bin/env python

"""
On steroid value classes
Includes type checking, validation and filtering of values
"""

# import modules from kpython lib
import kdebug # need to import this way - see kdebug
import koptions
import kfilter


class ValidationTypeException(kfilter.ValidationException):
    pass

class ValidationStringTooLongException(kfilter.ValidationException):
    pass

class ValidationStringTooShortException(kfilter.ValidationException):
    pass

class ValidationIntTooHighException(kfilter.ValidationException):
    pass

class ValidationIntTooLowException(kfilter.ValidationException):
    pass

class KValue(koptions.Options):
    """
    Basic value class
    must use new classes type to be able to use super in sub-classes (KValue(object) instead of KValue)
    """

    ## override and super me ##
    def __init__(self, **options):
        # store options if not already stored by a sub-class
        self.store_options(options)

        # public 
        self.raw_value = None # value without modifications
        self.validation_exceptions = [] # list of validation exceptions
        
        # internal
        self._allow_none = self.get_option("allow_none", default_value=False)
        self._pre_filter_callables = self.get_option("pre_filter_callables")
        self._post_filter_callables = self.get_option("post_filter_callables")
        self._raise_on_exception = self.get_option("raise_on_exception", default_value=False)

        # all the black magic appends here
        self.set_value(self.get_option("value"))

        # check that there are no unused options
        self.check_unused_options()

    def get_valid(self):
        # return wheither data is valid or not
        if len(self.validation_exceptions) == 0:
            return True
        return False
    valid = property(get_valid)

    def get_value(self):
        # output debug info
        kdebug.debug(3, "_get_value: value='%s'" % ( str(self._value) ), "kvalues" )

        # return current value
        return self._value
    def set_value(self, value):
        # output debug info
        kdebug.debug(3, "_set_value: value='%s'" % ( str(value) ), "kvalues" )

        # Unmodified value
        self.raw_value = value
        self.validation_exceptions = []

        # Make filters list
        filters = []

        if self._pre_filter_callables:
            # Custom pre-filters
            filters += self._pre_filter_callables

        if self._allow_none == True and value == None:
            # None value allowed... value is None... bypass other filters
            pass

        else:
            if self._allow_none == False:
                # None value not allowed... use a special filter for that
                filters += [kfilter.filter_not_none]

            # Class filter
            filters += [self.filter]

            if self._post_filter_callables:
                # Custom post-filters
                filters += self._post_filter_callables

        kdebug.debug(4, "_set_value: filters='%s'" % ( str(filters) ), "kvalues" )

        # Run filters
        kdebug.debug(4, "_set_value: calling run_filters", "kvalues" )
        fresult = kfilter.run_filters(value, filters)       
        kdebug.debug(4, "_set_value: filter_result='%s'" % ( str(fresult) ), "kvalues" )

        # raise the first exception if exceptions and raise_on_exception
        if self._raise_on_exception != False:
            if len(fresult.validation_exceptions):
                raise fresult.validation_exceptions[0]

        # Final value assignment
        self._value = fresult.value
        self.validation_exceptions = list(fresult.validation_exceptions) # TEST - make a copy instead of assigning
    value = property(get_value)

    def __str__(self):
        return "<class %s value='%s' valid='%s' validation_exceptions='%s'>" % \
            ( self.__class__.__name__, self.value, str(self.valid), self.validation_exceptions )

    ## override me ##
    def filter(self, value):
        # do nothing. return the unaltered value
        return kfilter.FilterResult(value=value)


class KBoolValue(KValue):
    """
    Boolean value
    """

    def __init__(self, **options):
        super(KBoolValue, self).__init__(**options)

    # override
    def filter(self, value):
        # Convert other types to boolean (except None.. which bypasses filters)
        # Could provide a custom pre-filter if None has to be converted
        return kfilter.filter_booleanize(value)


class KIntValue(KValue):
    """
    Int value
    """

    def __init__(self, **options):
        # store options if not already stored by a sub-class
        self.store_options(options)

        # internal
        self._min_value = self.get_option("min_value")
        self._max_value = self.get_option("max_value")

        # super!
        super(KIntValue, self).__init__(**options)


    def filter(self, value):
        kdebug.debug(1, 
            "KIntValue.filter: value='%s', type='%s'" % ( str(value), type(value) ),
            "kvalues" )

        fresult = kfilter.FilterResult(value=value)

        if type(value) != int:
            fresult.validation_exceptions.append(ValidationTypeException(expected_type=str(int), type=str(type(value))))
        else:
            if self._min_value and int(value) < int(self._min_value):
                fresult.validation_exceptions.append(ValidationIntTooLowException(min_value=self._min_value, value=value))
            if self._max_value and int(value) > int(self._max_value):
                fresult.validation_exceptions.append(ValidationIntTooHighException(max_value=self._max_value, value=value))

        kdebug.debug(2,
            "KIntValue.filter: filter_result='%s'" % ( str(fresult) ),
            "kvalues" )
                
        return fresult


class KStringValue(KValue):
    """
    String value
    """

    def __init__(self, **options):
        # store options if not already stored by a sub-class
        self.store_options(options)

        # internal
        self._min_length = self.get_option("min_length")
        self._max_length = self.get_option("max_length")

        # super!
        super(KStringValue, self).__init__(**options)

    def filter(self, value):
        kdebug.debug(1,
            "KStringValue.filter: value='%s', type='%s'" % ( str(value), type(value) ),
            "kvalues" )

        fresult = kfilter.FilterResult(value=value)

        if not isinstance(value, basestring):
            fresult.validation_exceptions.append(ValidationTypeException(expected_type=str(str), type=str(type(value))))
        else:
            if self._min_length and self._min_length and len(value) < self._min_length:
                fresult.validation_exceptions.append(ValidationStringTooShortException(min_length=self._min_length, length=len(value)))
            if self._max_length and self._max_length and len(value) > self._max_length:
                fresult.validation_exceptions.append(ValidationStringTooLongException(max_length=self._max_length, length=len(value)))

        kdebug.debug(2,
            "KStringValue.filter: filter_result='%s'" % ( str(fresult) ),
            "kvalues" )
        
        return fresult


class KStringListValue(KValue):
    """
    String list value
    """

    def __init__(self, **options):
        # super!
        super(KStringListValue, self).__init__(**options)

    def filter(self, value):
        kdebug.debug(1,
            "KStringListValue.filter: value='%s', type='%s'" % ( str(value), type(value) ),
            "kvalues" )

        fresult = kfilter.FilterResult(value=value)

        if type(value) != list:
            fresult.validation_exceptions.append(ValidationTypeException(expected_type="string list", type=str(type(value))))
        else:
            for s in value:
                if not isinstance(s, basestring):
                    fresult.validation_exceptions.append(ValidationTypeException(expected_type="string list", type=str(type(value))))
                    break

        kdebug.debug(2,
            "KStringListValue.filter: filter_result='%s'" % ( str(fresult) ),
            "kvalues" )
        
        return fresult


class KStringDictValue(KValue):
    """
    String dict value - dict that has only string keys and values
    """

    def __init__(self, **options):
        # super!
        super(KStringDictValue, self).__init__(**options)

    def filter(self, value):
        kdebug.debug(1,
            "KStringListValue.filter: value='%s', type='%s'" % ( str(value), type(value) ),
            "kvalues" )

        fresult = kfilter.FilterResult(value=value)

        if type(value) != dict:
            fresult.validation_exceptions.append(ValidationTypeException(expected_type="string dict", type=str(type(value))))
        else:
            for k, v in value.items():
                if not isinstance(type(k), basestring) or not isinstance(type(v), basestring):
                    fresult.validation_exceptions.append(ValidationTypeException(expected_type="string dict", type=str(type(value))))
                    break

        kdebug.debug(2,
            "KStringListValue.filter: filter_result='%s'" % ( str(fresult) ),
            "kvalues" )
        
        return fresult


if __name__ == "__main__":
    # non-exaustive tests

    #kdebug.enable_debug("kvalues")
    #kdebug.set_debug_level(9, "kvalues")
    #kdebug.set_debug_level(9, "kfilter")
    s = KValue(value=5, raise_on_exception=False)
    print str(s)
    print

    s = KIntValue(value=None, raise_on_exception=False)
    print str(s)
    print

    s = KStringValue(value=None, raise_on_exception=False)
    print str(s)
    print

    s = KStringValue(value=None, allow_none=False, raise_on_exception=False)
    print str(s)
    s.set_value("lalalala")
    print str(s)
    print

    s = KStringValue(value=5, raise_on_exception=False)
    print str(s)
    print

    s = KStringValue(value="lalalala", raise_on_exception=False)
    print str(s)
    print
    
    s = KStringValue(value="lala22", raise_on_exception=False)
    print str(s)
    print

    s = KStringValue(value="lala", max_length=3, min_length=5, raise_on_exception=False)
    print str(s)
    print

    s = KStringValue(value="lala", max_length=3, raise_on_exception=False)
    print str(s)
    print

    try:
        s = KStringValue(value=None, allow_none=False, raise_on_exception=True)
        print str(s)
        print "ERROR: should have failed."
    except Exception, e:
        print "Failed like expected: exception='%s'" % ( str(e) )
    print

