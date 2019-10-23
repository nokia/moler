# -*- coding: utf-8 -*-

__author__ = 'Tomasz Krol'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'tomasz.krol@nokia.com'

import datetime

from moler.events.shared.genericshared_lineevent import GenericSharedLineEvent


class Wait4(GenericSharedLineEvent):
    def __init__(self, detect_patterns, connection, match='any', till_occurs_times=-1, runner=None):
        """
        Event for Wait4 - universal event observer.
        :param connection: moler connection to device, terminal when command is executed
        :param detect_patterns: list of patterns
        :param match: type of our awaiting. Possible values: any, all, sequence
        :param till_occurs_times: number of event occurrence
        :param runner: Runner to run event
        """
        super(Wait4, self).__init__(connection=connection, runner=runner, match=match,
                                    till_occurs_times=till_occurs_times, detect_patterns=detect_patterns)


EVENT_OUTPUT_any = """
Line1 contains message number 20
Line2 contains message number 15
Line3 contains message number 21
Line4 contains message number 20
Line5 contains message number 15
Line6 contains message number 20
"""

EVENT_KWARGS_any = {
    "detect_patterns": [r'number (\d5)', r'(?P<LINE_NUMBER>Line\d+)\s+(.*)\s+number 20'],
    "match": "any",
    "till_occurs_times": 3
}

EVENT_RESULT_any = [
    {u'groups': (u'Line1', u'contains message'),
     u'line': u'Line1 contains message number 20',
     u'matched': u'Line1 contains message number 20',
     u'named_groups': {u'LINE_NUMBER': u'Line1'},
     u'time': datetime.datetime(2019, 5, 17, 12, 37, 47, 778380)},
    {u'groups': (15,),
     u'line': u'Line2 contains message number 15',
     u'matched': u'number 15',
     u'named_groups': {},
     u'time': datetime.datetime(2019, 5, 17, 12, 37, 47, 778498)},
    {u'groups': (u'Line4', u'contains message'),
     u'line': u'Line4 contains message number 20',
     u'matched': u'Line4 contains message number 20',
     u'named_groups': {u'LINE_NUMBER': u'Line4'},
     u'time': datetime.datetime(2019, 5, 17, 12, 37, 47, 778554)}
]

EVENT_OUTPUT_all = """
Line1 contains message number 20
Line2 contains message number 15
Line3 contains message number 21
Line4 contains message number 20
Line5 contains message number 15
Line6 contains message number 20
"""

EVENT_KWARGS_all = {
    "detect_patterns": [r'number (\d5)', r'(?P<LINE_NUMBER>Line\d+)\s+(.*)\s+number 20'],
    "match": "all",
    "till_occurs_times": 1
}

EVENT_RESULT_all = [
    [{u'groups': (u'Line1', u'contains message'),
      u'line': u'Line1 contains message number 20',
      u'matched': u'Line1 contains message number 20',
      u'named_groups': {u'LINE_NUMBER': u'Line1'},
      u'time': datetime.datetime(2019, 5, 17, 12, 36, 24, 390745)},
     {u'groups': (15,),
      u'line': u'Line2 contains message number 15',
      u'matched': u'number 15',
      u'named_groups': {},
      u'time': datetime.datetime(2019, 5, 17, 12, 36, 24, 390769)}]
]

EVENT_OUTPUT_sequence = """
Line1 contains message number 20
Line2 contains message number 15
Line3 contains message number 21
Line4 contains message number 20
Line5 contains message number 15
Line6 contains message number 20
"""

EVENT_KWARGS_sequence = {
    "detect_patterns": [r'number (\d5)', r'(?P<LINE_NUMBER>Line\d+)\s+(.*)\s+number 20'],
    "match": "sequence",
    "till_occurs_times": 1
}

EVENT_RESULT_sequence = [
    [{u'groups': (15,),
      u'line': u'Line2 contains message number 15',
      u'matched': u'number 15',
      u'named_groups': {},
      u'time': datetime.datetime(2019, 5, 17, 12, 37, 17, 832166)},
     {u'groups': (u'Line4', u'contains message'),
      u'line': u'Line4 contains message number 20',
      u'matched': u'Line4 contains message number 20',
      u'named_groups': {u'LINE_NUMBER': u'Line4'},
      u'time': datetime.datetime(2019, 5, 17, 12, 37, 17, 832200)}]
]

EVENT_OUTPUT_sequence2 = """
Line1 contains message number 20
Line2 contains message number 15
Line3 contains message number 21
Line4 contains message number 20
Line5 contains message number 20
Line6 contains message number 20
Line7 contains message number 20
Line8 contains message number 15
Line9 contains message number 20
"""

EVENT_KWARGS_sequence2 = {
    "detect_patterns": [r'number \d5', r'(?P<LINE_NUMBER>Line\d+)\s+(.*)\s+number 20'],
    "match": "sequence",
    "till_occurs_times": 2
}

EVENT_RESULT_sequence2 = [
    [
        {
            'line': "Line2 contains message number 15",
            "groups": (),
            "named_groups": {},
            "matched": "number 15",
            'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
        },
        {
            'line': "Line4 contains message number 20",
            "groups": (u"Line4", u"contains message"),
            "named_groups": {"LINE_NUMBER": "Line4"},
            "matched": "Line4 contains message number 20",
            'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224935),
        }
    ],
    [
        {
            'line': "Line8 contains message number 15",
            "groups": (),
            "named_groups": {},
            "matched": "number 15",
            'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224940),
        },
        {
            'line': "Line9 contains message number 20",
            "groups": (u"Line9", u"contains message"),
            "named_groups": {"LINE_NUMBER": "Line9"},
            "matched": "Line9 contains message number 20",
            'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224945),
        }
    ]
]
