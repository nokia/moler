# -*- coding: utf-8 -*-
"""
Utility/common code of library.
"""

__author__ = 'Michal Ernst'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'michal.ernst@nokia.com'

import datetime

from types import FunctionType
from functools import wraps


def wrapper(method):
    @wraps(method)
    def wrapped(*args, **kwrds):
        start_time = datetime.datetime.now()
        print("Method: {} started: {}".format(method.__name__, start_time))
        result = method(*args, **kwrds)
        stop_time = datetime.datetime.now()
        print("End: {}".format(stop_time))

        return result

    return wrapped


class MetaTMgr(type):
    def __new__(meta, class_name, bases, classDict):
        newClassDict = {}
        for attributeName, attribute in classDict.items():
            if isinstance(attribute, FunctionType):
                # replace it with a wrapped version
                attribute = wrapper(attribute)
            newClassDict[attributeName] = attribute
        return type.__new__(meta, class_name, bases, newClassDict)


class ProcTest(MetaTMgr('ProcTest', (object,), {})):
    pass

