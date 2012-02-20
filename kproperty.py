#!/usr/bin/env python

# Property classes
# - PropContainer(): contains properties
# - *Prop(): validated properties

# Technical note about properties storage:
# 
# Properties are class-based, not instance based... they are instantiated once
# at class parsing and not at every instantiation of classes that use them. So,
# they need to store data in the instance object in which they are used to be
# useful.
# 
# When using the python property() build-in function, properties do not care
# about the storage: they only use their getter, setter and deleter functions to
# handle that. A different function is used for every property in a class, and
# the object in which they store their value is specified in __get__, __set__
# and __delete__ calls.
#   ie:
#        class Foo(object):
#           name = property(_name_get)
#           addr = property(_addr_get)
#           def _name_get(self): return self._name
#           def _addr_get(self): return self._addr
#
# In this module, the Prop object does not need getter, setter and such
# functions. The cost is that those properties must be defined within a
# PropContainer compatible class.
#
# The PropContainer class, at instantiation, does:
#  - initialize class properties (first instantiation only), by:
#    - setting properties
#    - setting properties names, that will be used in exceptions for easier
#      debugging
#    - setting properties storage keys so they can differentiate between each
#      other when storing value in target object (Look at the Prop __get__, 
#      __set__ and __delete__ calls...)
#  - set properties values to either:
#    - a new instance of the defined model (if any)
#    - or
#    - the defined default value

import types, re, string
from kodict import odict

# Property set.
class PropSet(odict):
    pass

# Property model.
class PropModel(object):
    def __init__(self, cls=None, cls_args=[], cls_kwargs={}):
        self.cls = cls
        self.cls_args = cls_args
        self.cls_kwargs = cls_kwargs

    def instantiate(self):
        return self.cls(*self.cls_args, **self.cls_kwargs)

# Property container.
class PropContainer(object):

    # Initialized flag
    initialized = False

    # Property set
    prop_set = PropSet()

    # Usage:
    # prop_set = PropSet()
    # prop_set['name'] = StrProp(default='', doc='Name')
    # prop_set['name'] = StrProp(default='', doc='Address')

    def __init__(self):
        # Initialize properties (on the first instantiation ONLY).
        self._init_properties()

        # Set properties to their initial values.
        self._reset_properties_values()

    # Initialize properties (on the first instantiation ONLY).
    def _init_properties(self):
        if not self.__class__.initialized:
            for name, prop in self.prop_set.items():
                # Set property name.
                prop._set_name(name)

                # Add property in class attributes.
                setattr(self.__class__, name, prop)

            # Set the initialized flag to true.
            self.__class__.initialized = True

    # Set properties to their initial value.
    def _reset_properties_values(self):
         for obj in self.prop_set.values():
            obj.reset(self)

    # Give read access to properties with the [] syntax.
    def __getitem__(self, key):
        return self.prop_set[key].__get__(self)

    # Give write access to properties with the [] syntax.
    def __setitem__(self, key, value):
        self.prop_set[key].__set__(self, value)

# Property exceptions
class PropBadType(Exception):
    def __init__(self, name, value): 
        self.name = name
        self.value = value
    def __str__(self): 
        return "Property '%s': value '%s' has a bad type." % ( self.name, str(self.value) )

class PropBadInstance(Exception):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def __str__(self):
        return "Property '%s': value '%s' does not descend from a valid class." % ( self.name, str(self.value) )

class PropNullException(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self): 
        return "Property '%s': value is null but this is not permitted." % ( self.name )

class PropReadOnlyException(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "Property '%s': value is read-only." % ( self.name )

class PropValidatorException(Exception):
    def __init__(self, name, value, exception):
        self.name = name
        self.value = value
        self.exception = exception
    def __str__(self):
        return "Property '%s': value '%s' is not valid. Validator exception: '%s'." % \
            ( self.name, str(self.value), str(self.exception) )

class PropMinLengthException(Exception):
    def __init__(self, name, value, min_length):
        self.name = name
        self.value = value
        self.min_length = min_length
    def __str__(self): 
        return "Property '%s': value '%s' is too short. Minimum length is %i." % \
            ( self.name, str(self.value), self.min_length )

class PropMaxLengthException(Exception):
    def __init__(self, name, value, max_length):
        self.name = name 
        self.value = value
        self.max_length = max_length
    def __str__(self):
        return "Property '%s': value '%s' is too long. Maximum length is %i." % \
            ( self.name, str(self.value), self.max_length )

class PropRegexpException(Exception):
    def __init__(self, name, value, regexp):
        self.name = name
        self.value = value
        self.regexp = regexp
    def __str__(self):
        return "Property '%s': value '%s' does not match regexp '%s'." % \
            ( self.name, str(self.value), str(self.regexp) )

# Property class.
# Note: it must be used in a PropContainer compatible class... see the note at
# the top of this file.
class Prop(object):
    def __init__(self, doc="", null=True, read_only=False, default=None, model=None,
                 valid_types=None, valid_instances=None, validator=None):
        self.name = None                        # property name
        self._store_key = None                  # internal: store key
        self.doc = doc                          # documentation string
        self.null = null                        # flag: allow null value?
        self.read_only = read_only              # flag: read-only value
        self.default = default                  # default value
        self.model = model                      # model to use when the reset() method is called
                                                # (including when PropContainer class is instantiated)
        self.valid_types = valid_types          # list of types the value can be
        self.valid_instances = valid_instances  # list of base class the value can be an instance of
        self.validator = validator              # validator callable

        if self.model != None:
            # Validate model.
            try:
                getattr(model, 'instantiate')
            except AttributeError:
                raise Exception("Model must have an instantiate method.")

    # [Re-]set property to its initial state.
    def reset(self, obj):
        if self.model:
            # Set property value to a new instance of its model, if defined.
            instance = self.model.instantiate()
            self.__set__(obj, instance)

        else:
            # Set property value to its default value.
            self.__set__(obj, self.default)

    # Internal: set the property name and the store key that will be used
    # to store the property value in the target object.
    def _set_name(self, name):
        self.name = name
        self._store_key = "_prop_%s" % ( name )

    # Internal: check that a store key is set.
    def _store_key_check(self):
        if self._store_key == None:
            raise Exception("Property has no storage key set... you must use Prop() in a Property container.")

    # Get the property value. 
    def __get__(self, obj, objtype=None):
        self._store_key_check()
        if not obj.__dict__.has_key(self._store_key):
            if self.null: return None
            else: raise PropNullException(self.name)
        return obj.__dict__[self._store_key]

    # Set the property value.
    def __set__(self, obj, value):
        self._store_key_check()
        self._set_null_check(value)
        self._set_read_only_check(obj)
        self._set_types_check(value)
        self._set_instances_check(value)
        self._set_validator_check(value)
        if value != None and self.model and not isinstance(value, self.model.cls):
            # Value is not an instance of the model.

            # Reset property.
            self.reset(obj)

            try:
                # Try to get the import_data method.
                import_data_method = getattr(obj.__dict__[self._store_key], 'import_data')

            except AttributeError:
                # No import_data method... raise exception.
                raise PropBadInstance(self.name, value)

            # Import value.
            import_data_method(value)

        else:
            obj.__dict__[self._store_key] = value
 
    # Delete the property value.
    def __delete__(self, obj):
        self._store_key_check()
        self._set_null_check(None)
        self._set_read_only_check(obj)
        del obj.__dict__[self._store_key]

    # Check that the null constraint is respected.
    def _set_null_check(self, value):
        if (not self.null) and (value == None):
            raise PropNullException(self.name)

    # Check that the read-only constraint is respected.
    def _set_read_only_check(self, obj):
        if self.read_only:
            if obj.__dict__.has_key(self._store_key):
                raise PropReadOnlyException(self.name)

    # Check that the type of the value is at least one of the defined types list.
    def _set_types_check(self, value):
        if value != None:
            if self.valid_types != None and type(value) not in self.valid_types: raise PropBadType(self.name, value)

    # Check that the value is an instance of at least one of the defined instances list.
    def _set_instances_check(self, value):
        if value != None:
            if self.valid_instances != None:
                found = False
                for valid_instance in self.valid_instances:
                    if isinstance(value, valid_instance): found = True
                if not found: raise PropBadInstance(self.name, value)

    # Check that the custom validation function doesn't raise an exception.
    def _set_validator_check(self, value):
        if value != None:
            if self.validator != None:
                try:
                    self.validator(value)
                except Exception, e:
                    raise PropValidatorException(self.name, value, e)

# Integer property, which inherits from Prop class.
class IntProp(Prop):
    def __init__(self, convert_from_string=False, *args, **kwargs):
        self.convert_from_string = convert_from_string
        kwargs['valid_types'] = [int]
        Prop.__init__(self, *args, **kwargs)

    def __set__(self, obj, value):
        if self.convert_from_string and isinstance(value, basestring):
            # Try to convert the value to an integer before setting.
            try:
                value = string.atoi(value)
            except Exception, e:
                pass
        Prop.__set__(self, obj, value)

# Long property, which inherits from Prop class.
class LongProp(Prop):
    def __init__(self, convert_from_string=False, *args, **kwargs):
        self.convert_from_string = convert_from_string
        kwargs['valid_types'] = [int, long]
        Prop.__init__(self, *args, **kwargs)

    def __get__(self, obj, objtype=None):
        return long(Prop.__get__(self, obj, objtype))

    def __set__(self, obj, value):
        if self.convert_from_string and isinstance(value, basestring):
            # Try to convert the value to an integer before setting.
            try:
                value = string.atol(value)
            except Exception, e:
                pass
        Prop.__set__(self, obj, value)

# String property, which inherits from the Prop class.
class StrProp(Prop):
    def __init__(self, min_length=None, max_length=None, regexp=None, *args, **kwargs):
        # Forbit the valid_instances parameter.
        if kwargs.has_key('valid_instances'): 
            raise TypeError("__init__() got an unexpected keyword argument 'valid_instances'")

        # Hardcode the valid_instances parameter.
        kwargs['valid_instances'] = [basestring]

        # Super
        Prop.__init__(self, *args, **kwargs)

        # Store parameters which are specific to this class.
        self.min_length = min_length                # minimum length of the string
        self.max_length = max_length                # maximum length of the string
        self.regexp = regexp                        # regexp the string has to match

    # Set the property value.
    def __set__(self, obj, value):
        # Check that the value is a string.
        self._set_instances_check(value)

        # Check the constraints specific to this class.
        if self.min_length: 
            if len(value) < self.min_length: raise PropMinLengthException(self.name, value, self.min_length)
        if self.max_length:
            if len(value) > self.max_length: raise PropMaxLengthException(self.name, value, self.max_length)
        if self.regexp:
            if not re.match(self.regexp, value): raise PropRegexpException(self.name, value, self.regexp)

        # Super
        Prop.__set__(self, obj, value) 


# Non-exhaustive tests
if __name__ == "__main__":

    def test_properties():

        if 0:
            class C(object):
                def __init__(self, *args, **kwargs):
                    print "ARGS", args
                    print "KWARGS", kwargs

            model = PropModel(cls=C, cls_args=['1', '2', '3'], cls_kwargs={'a' : 1, 'c' : 3, 'b' : 2})
            c = model.instantiate()

        if 1:
            class B(PropContainer):
                prop_set = PropSet()
                prop_set['c'] = StrProp(default='c')
                prop_set['b'] = IntProp(default=2)
                prop_set['a'] = IntProp(default=1)

            class C(PropContainer):
                prop_set = PropSet()
                prop_set['a'] = IntProp(default=11)
                prop_set['b'] = IntProp(default=22)
                prop_set['c'] = StrProp(default='cc')

            b1 = B()
            b2 = B()
            c1 = C()
            c2 = C()
           
            print "PRINTING PROPSETS"
            print b1.prop_set
            print b2.prop_set
            print c1.prop_set
            print c2.prop_set

            print "PRINTING CLASS PROPSET DICTS"
            print b1.__class__.__dict__['prop_set']
            print b2.__class__.__dict__['prop_set']
            print c1.__class__.__dict__['prop_set']
            print c2.__class__.__dict__['prop_set']

            print "PRINTING ALL PROPERTIES"
            print "b1.a", b1.a
            print "b1.b", b1.b
            print "b1.c", b1.c
            print "b2.a", b2.a
            print "b2.b", b2.b
            print "b2.c", b2.c
            print "c1.a", c1.a
            print "c1.b", c1.b
            print "c1.c", c1.c
            print "c2.a", c2.a
            print "c2.b", c2.b
            print "c2.c", c2.c

            print "SETTING PROPERTIES"
            b1.a = 111
            b1.b = 222
            b1.c = 'ccc'
            b2.a = 1111
            b2.b = 2222
            b2.c = 'cccc'
            c1.a = 11111
            c1.b = 22222
            c1.c = 'ccccc'
            c2.a = 1111111
            c2.b = 2222222
            c2.c = 'ccccccc'

            print "PRINTING ALL PROPERTIES AGAIN"
            print "b1.a", b1.a
            print "b1.b", b1.b
            print "b1.c", b1.c
            print "b2.a", b2.a
            print "b2.b", b2.b
            print "b2.c", b2.c
            print "c1.a", c1.a
            print "c1.b", c1.b
            print "c1.c", c1.c
            print "c2.a", c2.a
            print "c2.b", c2.b
            print "c2.c", c2.c

    test_properties()

