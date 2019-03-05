# -*- coding: utf-8 -*-

__author__ = 'Tomasz Krol'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'tomasz.krol@nokia.com'

import datetime

from moler.events.lineevent import LineEvent


class Wait4(LineEvent):
    def __init__(self, connection, detect_patterns=list(), match='any', till_occurs_times=-1):
        super(Wait4, self).__init__(connection=connection, match=match, till_occurs_times=till_occurs_times,
                                    detect_patterns=detect_patterns)


EVENT_OUTPUT = """
8d FCT-1011 <2019-02-27T00:30:46.372Z> INF/NODEOAM/MZ Memory usage: { rss: 149495808,
8e FCT-1011 <2019-02-27T00:30:46.372Z> INF/NODEOAM/MZ   heapTotal: 91846144,
8f FCT-1011 <2019-02-27T00:30:46.372Z> INF/NODEOAM/MZ   heapUsed: 76202904,
90 FCT-1011 <2019-02-27T00:30:46.372Z> INF/NODEOAM/MZ   external: 378214 }
91 FCT-1011 <2019-02-27T00:30:56.372Z> INF/NODEOAM/MZ Memory usage: { rss: 149762048,
92 FCT-1011 <2019-02-27T00:30:56.372Z> INF/NODEOAM/MZ   heapTotal: 91846144,
93 FCT-1011 <2019-02-27T00:30:56.372Z> INF/NODEOAM/MZ   heapUsed: 76353672,
94 FCT-1011 <2019-02-27T00:30:56.372Z> INF/NODEOAM/MZ   external: 379414 }
"""

EVENT_KWARGS = {
    "detect_patterns": ['external', 'Memory'],
    "match": "sequence"
}

EVENT_RESULT = [
    {
        'line': "90 FCT-1011 <2019-02-27T00:30:46.372Z> INF/NODEOAM/MZ   external: 378214 }",
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224929),
    },
    {
        'line': "91 FCT-1011 <2019-02-27T00:30:56.372Z> INF/NODEOAM/MZ Memory usage: { rss: 149762048,",
        'time': datetime.datetime(2019, 1, 14, 13, 12, 48, 224935),
    }
]
