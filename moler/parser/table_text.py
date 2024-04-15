# -*- coding: utf-8 -*-
"""
Last modification: adding support for EPC tables and partially empty tables changes till 23.05.2018
                   added adjustments for project requirements.

Command TableText is parsing Linux Command to according to headers and columns (adjusted)
For initialization it is getting 4 parameters (2 required 2 optional)
Required parameters:
_header_regexps --> regexp array for finding headers
_header_keys --> array of keys assigned for found columns
Optional parameters:
_skip --> regexp for skipping line
_finish --> regexp for finishing parsing (next parse execution will not give any line)
Value_splitter --> value for splitting values in line by default 1+ spaces
WARNING ==> in current version no special signs or spaces are allowed in Name field (header key regexp)
"""

__author__ = "Rosinski Dariusz"
__copyright__ = "Copyright (C) 2018, Nokia"
__email__ = "dariusz.rosinski@nokia.com"

import re


class TableText:
    def __init__(
        self, _header_regexps, _header_keys, _skip="", _finish="", value_splitter=r"\s+"
    ):
        self._header_regexps = _header_regexps  # array of regexps defining header parts
        self._header_keys = (
            _header_keys  # array of keys returned for matched header parts
        )
        self._skip = _skip  # regexp to be used to find lines that should be skipped
        self._finish = _finish  # regexp that shows we have finished table processing
        self._finish_found = 0  # flag for matching finish regexp
        self._found = None
        self._value_splitter = value_splitter

        self.header_regexp_groups = self.build_hdr_groups()
        self.header_positions = []  # array of "column position" of header

    def build_hdr_groups(self):
        """
        Function for building group of headers. If not enough keys defined name COL_x will be added at the end
        :return: regexp allowing to read headers group with column names in format (?P<name>regexp) what allows to
        read assign correct name for matched value
        """
        hdr_groups = ""
        amount_of_keys = len(self._header_keys)
        amount_of_regexps = len(self._header_regexps)
        # if there is more regexps than keys then add COL_x to result
        if amount_of_regexps > amount_of_keys:
            for index in range(amount_of_keys + 1, amount_of_regexps + 1, 1):
                self._header_keys.append(f"COL_{str(index)}")
        for index in range(amount_of_regexps):
            regexp = self._header_regexps[index]
            name = self._header_keys[index]
            # add dictionary keys to regexp
            group_re = f"(?P<{name}>{regexp})"
            hdr_groups += f".*{group_re}"
        return hdr_groups

    def parse(self, data):
        """
        :param data: accepts one parameter which is line for parsing. Without headers found it will look for it
        :return: returns result dictionary according to your header regexps set during initialization
                 returns None when nothing was found or headers when values were found
        """
        result = {}
        # looking for finish pareser. If found stop processing
        if re.match(r"^\s*$", data):
            return None
        finish = self._finish
        if finish != "" and re.search(finish, data):
            self._finish_found = True
        if self._finish_found:
            return None
        # looking for skip keyword
        skip = self._skip
        if skip != "" and re.search(skip, data):
            return None
        hdr_regexp = self.header_regexp_groups
        compiled_header_re = re.compile(hdr_regexp)
        # finding header in line until headers are found
        if not self.header_positions:
            header_search_result = re.search(compiled_header_re, data)
            if header_search_result is not None:
                groups_found = header_search_result.groupdict()
                for index in range(0, len(self._header_keys), 1):
                    hdr_name = self._header_keys[index]
                    hdr_value = groups_found[hdr_name]
                    hdr_value_searched = re.search(r"\b" + hdr_value + r"\b", data)
                    self.header_positions.append(hdr_value_searched)
        else:
            header_keys_number = len(self._header_keys)
            # split values into table of values
            split_values = re.split(self._value_splitter, str.strip(str(data)))
            # connect values and end of them in order to manage them correclty
            split_values_positions = self.split_with_end_position(split_values, data)
            value_index = 0
            data_key = self._header_keys
            for header_index in range(0, header_keys_number, 1):
                res, value_index = self.get_value_for_header(
                    header_index, split_values_positions, value_index
                )
                result[data_key[header_index]] = res
            return result

    def get_value_for_header(self, current_header_position, values, start_value_index):
        """
        :param current_header_position: matched headers positions (get with re.search(regexp, line)) for which search
            will take place
        :param values: values connected into list
        :param start_value_index: current start from which search will take place
        :return: Returns found value for specific header
        """
        value_index = 0
        connected_value = ""
        if current_header_position + 1 < len(self.header_positions):
            next_header_position = self.header_positions[current_header_position + 1]
            # for values that stayed in search
            for i in range(len(values[start_value_index:])):
                # check if value end is on position of start of next header
                if values[start_value_index + i]["end"] >= next_header_position.start():
                    if not connected_value:
                        connected_value = " "
                    break
                else:
                    connected_value += f" {values[start_value_index + i]['value']}"
                    value_index += 1
            # if values were connected then set it to data value in other case set only passed value for index
            if connected_value:
                data_value = connected_value
                value_index -= 1
            else:
                data_value = ""
        else:
            for i in range(len(values[start_value_index:])):
                connected_value += f" {values[start_value_index + i]['value']}"
            data_value = connected_value
        data_value = str.strip(str(data_value))
        return self.convert_data_to_type(
            data_value
        ), start_value_index + value_index + 1

    @staticmethod
    def split_with_end_position(values, data):
        """
        :param values: values splitted from data
        :param data: data full line with values in raw form
        :return: returns list of dictionary where each dict contains 2 keys 'value' and 'end' which is end position of
            string
        """
        current_value = values[0]
        current_end = re.search(r"[\b\s]??" + current_value + r"[\b\s]??", data).end()
        result = []
        result.append({"value": current_value, "end": current_end})
        for i in range(1, len(values), 1):
            current_value = values[i]
            current_search = re.search(
                r"[\b\s]??" + re.escape(values[i]) + r"[\b\s]??", data[current_end:]
            )
            current_end += current_search.end()
            result.append({"value": current_value, "end": current_end})
        return result

    @staticmethod
    def convert_data_to_type(data):
        # when casting wrong type Value Error will be raised
        try:
            d_int = int(data)
            if str(d_int) == data:
                return d_int
        except ValueError:
            pass
        try:
            d_float = float(data)
            return d_float
        except ValueError:
            pass
        return data


COMMAND_OUTPUT = """
UID        PID   PPID  C STIME TTY   CMD                                                                                                                 TIME
avahi-a+  3597.5    1  0  2017 ?     avahi-autoipd: [ens4] sleeping                                                                                      00:00:45
root      3598   3597  0  2017 ?     avahi-autoipd: [ens4] callout dispatcher                                                                            00:00:00
root      3681      1  0  2017 ?     /sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf               00:00:17
root      3812      1  0  2017 ?     /usr/sbin/xinetd -stayalive -dontfork                                                                               00:00:00
root      3814      1  0  2017 ?     /usr/sbin/vsftpd /etc/vsftpd.conf                                                                                   00:00:00
root      3826      1  0  2017 ?     /usr/sbin/sshd -D                                                                                                   00:00:02
root      3835      2  0  2017 ?     [cifsiod]                                                                                                           00:00:00
root      3867      1  0  2017 ?     /usr/sbin/cron -n                                                                                                   00:00:18
root      3870      1  0  2017 tty1  /sbin/agetty --noclear tty1 linux                                                                                   00:00:00
avahi-a+  4592      1  0  2017 ?     avahi-autoipd: [ens3] sleeping                                                                                      00:17:15
root      45931    92  0  2017 ?     avahi-autoipd: [ens3] callout dispatcher                                                                            00:00:00
root      4648      1  0  2017 ?     /sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-              00:00:00
root      5823      2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
drosinsk  5823      2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
dr768nsk  5823      2  0 Mar09 ?     [kworker/u8:2]
finisher  2344      1  2 Mar09 ?     [dsfa]                                                                                                              00:00:03
root      5823      2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
root      5823      2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
root      5823      2  0 Mar09 ?     [kworker/u8:2]                                                                                                      00:00:03
"""

COMMAND_KWARGS = {
    "_header_regexps": ["UID", "PID", "PPID", "C", "STIME", "TTY", "CMD", "TIME"],
    "_header_keys": ["UID1", "PID", "PPID", "C", "STIME", "TTY", "CMD"],
}

COMMAND_RESULT = [
    {
        "UID1": "avahi-a+",
        "PID": 3597.5,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:45",
        "CMD": "avahi-autoipd: [ens4] sleeping",
    },
    {
        "UID1": "root",
        "PID": 3598,
        "PPID": 3597,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "avahi-autoipd: [ens4] callout dispatcher",
    },
    {
        "UID1": "root",
        "PID": 3681,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:17",
        "CMD": "/sbin/dhclient6 -6 -cf /var/lib/dhcp6/dhclient6.ens3.conf -lf /var/lib/dhcp6/dhclient6.ens3.lease -pf",
    },
    {
        "UID1": "root",
        "PID": 3812,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "/usr/sbin/xinetd -stayalive -dontfork",
    },
    {
        "UID1": "root",
        "PID": 3814,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "/usr/sbin/vsftpd /etc/vsftpd.conf",
    },
    {
        "UID1": "root",
        "PID": 3826,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:02",
        "CMD": "/usr/sbin/sshd -D",
    },
    {
        "UID1": "root",
        "PID": 3835,
        "PPID": 2,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "[cifsiod]",
    },
    {
        "UID1": "root",
        "PID": 3867,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:18",
        "CMD": "/usr/sbin/cron -n",
    },
    {
        "UID1": "root",
        "PID": 3870,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "tty1",
        "COL_8": "00:00:00",
        "CMD": "/sbin/agetty --noclear tty1 linux",
    },
    {
        "UID1": "avahi-a+",
        "PID": 4592,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:17:15",
        "CMD": "avahi-autoipd: [ens3] sleeping",
    },
    {
        "UID1": "root",
        "PID": 45931,
        "PPID": 92,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "avahi-autoipd: [ens3] callout dispatcher",
    },
    {
        "UID1": "root",
        "PID": 4648,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "COL_8": "00:00:00",
        "CMD": "/sbin/dhcpcd --netconfig -L -E -HHH -c /etc/sysconfig/network/scripts/dhcpcd-hook -t 0 -h FZM-FDD-086-",
    },
    {
        "UID1": "root",
        "PID": 5823,
        "PPID": 2,
        "C": 0,
        "STIME": "Mar09",
        "TTY": "?",
        "COL_8": "00:00:03",
        "CMD": "[kworker/u8:2]",
    },
    {
        "UID1": "dr768nsk",
        "PID": 5823,
        "PPID": 2,
        "C": 0,
        "STIME": "Mar09",
        "TTY": "?",
        "COL_8": "",
        "CMD": "[kworker/u8:2]",
    },
]

COMMAND_OUTPUT_V2 = """
| UID    |    PID |PPID | C|STIME |TTY|   CMD                            |                                                                                    TIME
|avahi-a+|   3597 |1    |0 | 2017 |?  |   avahi-autoipd: [ens4] sleeping |                                                                                 00:00:45"""

COMMAND_RESULT_V2 = [
    {
        "UID1": "avahi-a+",
        "PID": 3597,
        "PPID": 1,
        "C": 0,
        "STIME": 2017,
        "TTY": "?",
        "TIME": "00:00:45",
        "CMD": "avahi-autoipd: [ens4] sleeping",
    }
]

COMMAND_KWARGS_V2 = {
    "_header_regexps": ["UID", "PID", "PPID", "C", "STIME", "TTY", "CMD", "TIME"],
    "_header_keys": ["UID1", "PID", "PPID", "C", "STIME", "TTY", "CMD", "TIME"],
}

COMMAND_OUTPUT_V3 = """
=================================================================|
       |  s1   s1u  s11  s5   s5u  nas  rrc  x2  m3   x2u  lppa  |
-----------------------------------------------------------------|
MME-1  |  off  -    off  -    -    off  -    -   off  -    off   |
-----------------------------------------------------------------|
SGW-1  |  -    off  off  off  off  -    -    -   -    -    -     |
-----------------------------------------------------------------|
PGW-1  |  -    -    -    off  off  -    -    -   -    -    -     |
-----------------------------------------------------------------|
"""

COMMAND_RESULT_V3 = [
    {
        "Name": "MME-1",
        "s1": "off",
        "s1u": "-",
        "s11": "off",
        "s5": "-",
        "s5u": "-",
        "nas": "off",
        "rrc": "-",
        "x2": "-",
        "m3": "off",
        "x2u": "-",
        "lppa": "off",
    },
    {
        "Name": "SGW-1",
        "s1": "-",
        "s1u": "off",
        "s11": "off",
        "s5": "off",
        "s5u": "off",
        "nas": "-",
        "rrc": "-",
        "x2": "-",
        "m3": "-",
        "x2u": "-",
        "lppa": "-",
    },
    {
        "Name": "PGW-1",
        "s1": "-",
        "s1u": "-",
        "s11": "-",
        "s5": "off",
        "s5u": "off",
        "nas": "-",
        "rrc": "-",
        "x2": "-",
        "m3": "-",
        "x2u": "-",
        "lppa": "-",
    },
]


COMMAND_KWARGS_V3 = {
    "_header_regexps": [
        "",
        "s1",
        "s1u",
        "s11",
        "s5",
        "s5u",
        "nas",
        "rrc",
        "x2",
        "m3",
        "x2u",
        "lppa",
    ],
    "_header_keys": [
        "Name",
        "s1",
        "s1u",
        "s11",
        "s5",
        "s5u",
        "nas",
        "rrc",
        "x2",
        "m3",
        "x2u",
        "lppa",
    ],
    "_skip": "^(-+)|(=+)",
}

COMMAND_OUTPUT_V4 = """
Proto RefCnt Flags       Type       State         I-Node Path
unix  2      [ ]         DGRAM      zsad          13962  /var/lib/dhcp6/dev/log
unix  3                  STREAM     CONNECTED     14058  /var/lib/dhcp6/dev/log
unix  3      [ ]         STREAM     CONNECTED     14007
unix
"""

COMMAND_RESULT_V4 = [
    {
        "Proto": "unix",
        "RefCnt": 2,
        "Flags": "[ ]",
        "Type": "DGRAM",
        "State": "zsad",
        "INode": 13962,
        "Path": "/var/lib/dhcp6/dev/log",
    },
    {
        "Proto": "unix",
        "RefCnt": 3,
        "Flags": "",
        "Type": "STREAM",
        "State": "CONNECTED",
        "INode": 14058,
        "Path": "/var/lib/dhcp6/dev/log",
    },
    {
        "Proto": "unix",
        "RefCnt": 3,
        "Flags": "[ ]",
        "Type": "STREAM",
        "State": "CONNECTED",
        "INode": 14007,
        "Path": "",
    },
    {
        "Proto": "unix",
        "RefCnt": "",
        "Flags": "",
        "Type": "",
        "State": "",
        "INode": "",
        "Path": "",
    },
]

COMMAND_KWARGS_V4 = {
    "_header_regexps": ["Proto", "RefCnt", "Flags", "Type", "State", "I-Node", "Path"],
    "_header_keys": ["Proto", "RefCnt", "Flags", "Type", "State", "INode", "Path"],
}

COMMAND_RESULT_NO_OPTIONS = {}

COMMAND_RESULT_WITH_OPTIONS = {}
