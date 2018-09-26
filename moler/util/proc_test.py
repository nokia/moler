# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import datetime
from functools import wraps
from types import FunctionType


def wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwrds):
        class_name = args[0].__class__.__name__
        method_name = method.__name__

        start_time = datetime.datetime.now()
        print("START Method: {}.{} -> {}".format(class_name, method_name, start_time))

        result = method(*args, **kwrds)

        stop_time = datetime.datetime.now()
        print("END Method: {}.{} -> {}".format(class_name, method_name, stop_time))

        return result

    return wrapped


class MetaProcTest(type):
    def __new__(meta, class_name, bases, classDict):
        newClassDict = {}
        for attributeName, attribute in classDict.items():
            if isinstance(attribute, FunctionType):
                # replace it with a wrapped version
                attribute = wrapper(attribute)
            newClassDict[attributeName] = attribute
        return type.__new__(meta, class_name, bases, newClassDict)


class ProcTest(MetaProcTest('ProcTest', (object,), {})):
    pass
