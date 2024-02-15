# -*- coding: utf-8 -*-
__author__ = 'Maciej Pikula, Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'maciej.pikula@nokia.com, grzegorz.latuszek@nokia.com'


import importlib

# ------------------------------------ public API


def create_instance_from_class_fullname(class_fullname, constructor_parameters):
    """
    Factory method that creates class instance object according to its definition given in parameters.

    :param class_fullname: full name of class in dotted notation like 'package1.module1.ClassName1'
    :param constructor_parameters: to be passed into instance constructor
    :return: instance of requested class
    """
    class_object = load_class_from_class_fullname(class_fullname)
    class_instance = create_class_instance(class_object, constructor_parameters)
    return class_instance


def load_class_from_class_fullname(class_fullname):
    """
    Factory method that loads class  object according to its fullname.

    :param class_fullname: full name of class in dotted notation like 'package1.module1.ClassName1'
    :return: requested class object
    """
    class_module_name, class_name = _split_to_module_and_class_name(class_fullname)
    class_object = _load_class(module_name=class_module_name, class_name=class_name)
    return class_object


def create_class_instance(class_object, constructor_params):
    """
    Factory method that creates class instance object according to its definition given in parameters.

    :param class_object: class object to be instantiated
    :param constructor_params: to be passed into instance constructor
    :return: instance of requested class
    """
    try:
        class_instance = class_object(**constructor_params)
        return class_instance
    except TypeError as err:
        raise TypeError(f"Creating '{class_object}' instance: {str(err)}") from err


# ------------------------------------ implementation


def _split_to_module_and_class_name(class_fullname):
    class_split = class_fullname.split('.')
    module_list = class_split[0:-1]
    module = '.'.join(module_list)
    class_name = class_split[-1]
    return module, class_name


def _load_class(module_name, class_name):
    module = _import_module(module_name)
    class_object = _import_class_from_module(module, class_name)
    return class_object


def _import_module(module_name):
    try:
        module_of_class = importlib.import_module(module_name)
        return module_of_class
    except ImportError as err:
        raise ImportError(f"Could not import '{module_name}' module ({str(err)}). Please make sure "
                          f"import path is correct.") from err


def _import_class_from_module(module, class_name):
    try:
        module_attribute = getattr(module, class_name)
        if isinstance(module_attribute, type):
            class_object = module_attribute
            return class_object
        else:
            raise TypeError(f"Module's '{module}' attribute '{class_name}' is not class (it is {type(module_attribute)}).")
    except AttributeError as ae:
        raise AttributeError(f"Module '{module}' has no attribute '{class_name}'") from ae
