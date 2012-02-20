#!/usr/bin/env python

"""
Filtering module (well, "TransformAndValidate" would be a better term)
This module allows transforming and validating values with lists of filters.
Every filter can decide wheither to continue to the next filter or not.

Filters must:
    - accept a single <value> parameter
    - return a FilterResult instance
"""

# kpython lib
import logging
import kbase
import kodict
import koptions

log = logging.getLogger(__name__)

class ValidationException(object):
    def __init__(self, message=None, string_id=None, **options):
        # store custom message
        self.message = message

        # custom message id
        self.string_id = string_id

        # store options
        self._options = options

        # store options as read-only attributes too
        for k, v in self._options.items():
            self.__dict__[k] = v

    # render all attributes read-only, except "message" and "_options"
    def __setattr__(self, name, value):
        if name == "message" or name == "string_id" or name == "_options":
            self.__dict__[name] = value
        else:
            raise AttributeError, name

    def __str__(self):
        if self.message:
            # custom message set.. fill it with call-time parameters
            return self.fill_message(self.message)
        else:
            # return a string containing a class name and all init options
            s = "<" + self.__class__.__name__
            for key, value in self._options.items():
                s += " " + str(key) + "='" +  str(value) + "'"
            s += ">"
            return s

    # message must be like: "String was '%(length)i' characters long but the maximum allowable is '%(max_length)i' characters."
    # variables will be replaced with call-time parameters
    def fill_message(self, message):
        return message % self._options

    # Returns the class name
    def classname(self):
        return self.__class__.__name__

class ValidationNoneValueException(ValidationException):
    pass

class ValidationNotPositiveNumberException(ValidationException):
     pass

class FilterResult(kbase.DefinedAttributesStore):
    """
    Filter result
    Attributes:
        value(any type): new value set after going through a filter
        validation_exceptions(list): list of ValidationException (sub-)classes
        continue_filtering(boolean): continue or stop filtering

    This class derives from DefinedAttributesStore: it allows basic parameters validation
    """

    def __init__(self, value=None, validation_exceptions=None, continue_filtering=None):
        # Default parameters
        # Had problem using validation_exceptions=None, continue_filtering=None
        # (older values re-assigned instead of the default value...)
        if validation_exceptions == None: validation_exceptions = []
        if continue_filtering == None: continue_filtering = True

        # super!
        super(FilterResult, self).__init__()

        # parameter definitions for basic validation
        self._attr_any_type_definitions += [ "value" ]
        self._attr_type_definitions[list] += [ "validation_exceptions" ]
        self._attr_type_definitions[bool] += [ "continue_filtering" ]

        self.value = value
        self.validation_exceptions = validation_exceptions
        self.continue_filtering = continue_filtering

    def __str__(self):
        return "<FilterResult value='%s' type='%s' validation_exceptions='%s' continue_filtering='%s'>" %  \
            ( str(self.value), type(self.value), str(self.validation_exceptions), str(self.continue_filtering) )


def run_filters(value, filter_callables, raise_on_exception=False):
    """
    Run a list of filters on a given value
    Paramameters:
        value(any type): value to filter (can be of any type, including null)
        filter_callables(list): list of filter functions or class methods (callables)
    Returns:
        FilterResult object
    """

    fresult = FilterResult(value=value)

    log.debug( 
        "run_filters: filters='%s', input_value='%s', type='%s'" % ( filter_callables, str(value), type(value) ))

    i = 0
    for filter_callable in filter_callables:
        i += 1

        # Raise on invalid filter.
        if not callable(filter_callable):
            raise Exception("run_filters: filter_loop=%i: not a callable: '%s'" % ( i, str(filter_callable) ) )

        # Filter.
        tmp_fresult = filter_callable(fresult.value)
        log.debug("run_filter: loop=%i, filter_result='%s'" % ( i, str(tmp_fresult) ))
        fresult.value = tmp_fresult.value
        fresult.validation_exceptions += tmp_fresult.validation_exceptions
        fresult.continue_filtering = tmp_fresult.continue_filtering
        log.debug("run_filter: loop=%i, resulting_filter_result='%s'" % ( i, str(fresult) ))
 
        # Stop filtering if last validator said so
        if not fresult.continue_filtering:
            break

    log.debug("run_filter: filter_result='%s'" % ( str(fresult) ))

    return fresult



def filter_not_none(value):
    """
    Check that value is not none
    """

    in_value = value

    log.debug("filter_not_none: input_value='%s'" % ( str(value) ) )

    fresult = FilterResult(value=value)

    if value == None:
        fresult.continue_filtering = False
        fresult.validation_exceptions.append(ValidationNoneValueException())

    log.debug("filter_not_none: input_value='%s', output_value='%s'" % ( str(in_value), str(value) ))

    return fresult


def filter_booleanize(value):
    """
    Filter - booleanize value - except if value is None
    """

    in_value = value

    log.debug("filter_booleanize: input value='%s'" % ( str(value) ))

    if value == None:
        # no None-to-false conversion here! python normally handles None as False
        return FilterResult(value=None)

    if value:
        return FilterResult(value=True)

    log.debug("filter_booleanize: input value='%s', output value='%s'" % ( str(in_value), str(value) ))

    return FilterResult(value=False)


def filter_booleanize_none(value):
    """
    Filter - booleanize value - including if value is None
    """

    if value == None:
        value = False
    return filter_booleanize(value)

def filter_none_to_empty_str(value):
    """
    Filter - replace a None value with ""
    """

    in_value = value

    log.debug("filter_none_to_empty_str: input value='%s'" % ( str(value) ))

    if not value:
        value = ""

    log.debug("filter_none_to_empty_str: input value='%s', output value='%s'" % ( str(in_value), str(value) ))

    return FilterResult(value=value)

def filter_positive_number(value):
    try:
        value = long(value)
        if value < 0: return FilterResult(value=value, validation_exceptions=[ValidationNotPositiveNumberException()])
        return FilterResult(value=value)

    except Exception:
        return FilterResult(value=value, validation_exceptions=[ValidationNotPositiveNumberException()])

if __name__ == "__main__":
    fr = run_filters(0, [filter_booleanize])
    print str(fr)

    fr = run_filters(1, [filter_booleanize])
    print str(fr)

    fr = run_filters(True, [filter_booleanize])
    print str(fr)

    fr = run_filters(None, [filter_booleanize])
    print str(fr)


