# -*- coding: utf-8 -*-
"""
Top command module.
"""

__author__ = 'Adrianna Pienkowska, Michal Ernst, Marcin Usielski'
__copyright__ = 'Copyright (C) 2018-2019, Nokia'
__email__ = 'adrianna.pienkowska@nokia.com, michal.ernst@nokia.com, marcin.usielski@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone


class Top(GenericUnixCommand):
    def __init__(self, connection, options=None, prompt=None, newline_chars=None, runner=None, n=1):
        """
        Top command.
        :param connection: moler connection to device, terminal when command is executed.
        :param options: options of top command for unix.
        :param prompt: prompt on system where ping is executed.
        :param newline_chars: characters to split lines.
        :param runner: Runner to run command.
        :param n: Specifies number of measurements.
        """
        super(Top, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)
        self.options = options
        self._processes_list_headers = list()
        self.current_ret = dict()
        self.n = n

    def build_command_string(self):
        """
        Builds command string from parameters passed to object.
        :return: String representation of command to send over connection to device.
        """
        cmd = "top"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        if self.n:
            cmd = "{} n {}".format(cmd, self.n)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.
        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        if is_full_line:
            try:
                self._command_failure(line)
                self._parse_top_row(line)
                self._parse_task_row(line)
                self._parse_cpu_row(line)
                self._parse_memory_rows(line)
                self._parse_processes_list_headers(line)
                self._parse_processes_list(line)
            except ParsingDone:
                pass
        return super(Top, self).on_new_line(line, is_full_line)

    _re_error = re.compile(r'top:\s*(?P<ERROR_MSG>.*)')

    def _command_failure(self, line):
        """
        Parses errors from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR_MSG"))))
            raise ParsingDone

    _re_top_row = re.compile(r'(?P<TOP_ROW>.*)\s-\s(?P<TIME>\d*:\d*:\d*)\sup\s(?P<UP_TIME>.*,.*),\s*(?P<USERS>.*)user'
                             r'.*load average:(?P<LOAD_AVE> .*)')

    def _parse_top_row(self, line):
        """
        Parses top row from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_top_row, line):
            command_name = self._regex_helper.group("TOP_ROW")
            current_time = self._regex_helper.group("TIME")
            up_time = self._regex_helper.group("UP_TIME").replace(", ", ",")
            users = int(self._regex_helper.group("USERS"))
            load_ave = self._regex_helper.group("LOAD_AVE").split()
            load_ave = [float(ave.strip(',')) for ave in load_ave]
            top_row_dict = {'current time': current_time, 'up time': up_time, 'users': users, 'load average': load_ave}
            self.current_ret.update({command_name: top_row_dict})
            raise ParsingDone

    _re_task_row = re.compile(r'(?P<TASK_ROW>Tasks):\s*(?P<TOTAL>\d*)\s*total,\s*(?P<RUN>\d*)\s*running,\s*'
                              r'(?P<SLEEP>\d*)\s*sleeping,\s*(?P<STOP>\d*)\s*stopped, \s*(?P<ZOMBIE>\d*)\s*zombie')

    def _parse_task_row(self, line):
        """
        Parses task row from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_task_row, line):
            total = int(self._regex_helper.group("TOTAL"))
            running = int(self._regex_helper.group("RUN"))
            sleeping = int(self._regex_helper.group("SLEEP"))
            stopped = int(self._regex_helper.group("STOP"))
            zombie = int(self._regex_helper.group("ZOMBIE"))
            task_row_dict = {'total': total, 'running': running, 'sleeping': sleeping, 'stopped': stopped,
                             'zombie': zombie}
            self.current_ret.update({'tasks': task_row_dict})
            raise ParsingDone

    _re_cpu_row = re.compile(r'.*(?P<CPU_ROW>Cpu).*:\s*(?P<US>\d*.\d*).*us,\s*(?P<SY>\d*.\d*).*sy,\s*(?P<NI>\d*.\d*)'
                             r'.*ni,\s*(?P<ID>\d*.\d*).*id,\s*(?P<WA>\d*.\d*).*wa,\s*(?P<HI>\d*.\d*)'
                             r'.*hi,\s*(?P<SI>\d*.\d*).*si,\s*(?P<ST>\d*.\d*).*st')

    def _parse_cpu_row(self, line):
        """
        Parses cpu row from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_cpu_row, line):
            user_processed = float(self._regex_helper.group("US"))
            system_processes = float(self._regex_helper.group("SY"))
            upgraded_nice = float(self._regex_helper.group("NI"))
            not_used = float(self._regex_helper.group("ID"))
            io_operations = float(self._regex_helper.group("WA"))
            hardware_interrupts = float(self._regex_helper.group("HI"))
            software_interrupts = float(self._regex_helper.group("SI"))
            steal_time = float(self._regex_helper.group("ST"))
            cpu_row_dict = {'user processes': user_processed, 'system processes': system_processes,
                            'not used': not_used,
                            'upgraded nice': upgraded_nice, 'steal time': steal_time, 'IO operations': io_operations,
                            'hardware interrupts': hardware_interrupts, 'software interrupts': software_interrupts}
            self.current_ret.update({'%Cpu': cpu_row_dict})
            raise ParsingDone

    _re_memory_rows = re.compile(r'(?P<MEM>.*):\s*(?P<TOTAL_MEM>\d*)(?P<UNIT>.)\s*total,\s*(?P<FREE>\d*)\s*free,\s*'
                                 r'(?P<USED>\d*)\s*used[,.]\s*(?P<OTHER>\d*)\s*')

    def _parse_memory_rows(self, line):
        """
        Parses memory rows from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_memory_rows, line):
            mem_type = self._regex_helper.group("MEM")
            mem_total = self._if_number_convert_to_int_or_float(self._regex_helper.group("TOTAL_MEM"))
            used = self._if_number_convert_to_int_or_float(self._regex_helper.group("USED"))
            free = self._if_number_convert_to_int_or_float(self._regex_helper.group("FREE"))
            cached = self._if_number_convert_to_int_or_float(self._regex_helper.group("OTHER"))
            mem_row_dict = {'total': mem_total, 'used': used, 'free': free, 'cached': cached}
            self.current_ret.update({mem_type: mem_row_dict})
            raise ParsingDone

    _re_processes_header = re.compile(r'(?P<HEADER> .*PID.*)')

    def _parse_processes_list_headers(self, line):
        """
        Parses processes list headers from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._regex_helper.search_compiled(Top._re_processes_header, line) and not self._processes_list_headers:
            self._processes_list_headers.extend(line.strip().split())
            self.current_ret.update({'processes': list()})
            raise ParsingDone

    def _parse_processes_list(self, line):
        """
        Parses processes list from the line of command output
        :param line: Line of output of command.
        :return: Nothing but raises ParsingDone if line has information to handle by this method.
        """
        if self._processes_list_headers:
            processes_info = line.strip().split()
            processes_info = [self._if_number_convert_to_int_or_float(process_info) for process_info in processes_info]
            processes_dict = dict(zip(self._processes_list_headers, processes_info))
            self.current_ret['processes'].append(processes_dict)

    def _if_number_convert_to_int_or_float(self, inscription):
        """
        Convert string to number.
        :param inscription: string to convert
        :return: Number or if number not in string return input string.
        """
        try:
            if inscription.isdigit():
                new_inscription = int(inscription)
            else:
                new_inscription = float(inscription)
            return new_inscription
        except ValueError:
            return inscription


COMMAND_OUTPUT_without_options = """
xyz@debian:~$ top n 1
top - 15:08:22 up 3 days,  1:56,  1 user,  load average: 0.14, 0.27, 0.19
Tasks: 223 total,   1 running, 158 sleeping,  64 stopped,   0 zombie
%Cpu(s):  1.8 us,  1.1 sy,  0.0 ni, 97.2 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem :  2052556 total,   257512 free,  1412260 used,   382784 buff/cache
KiB Swap:  2096124 total,  1993304 free,   102820 used.   460660 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
  2642 bylica    20   0 3322120 0.977g  18796 S  1.7 49.9 141:44.05 java
 11447 bylica    20   0  325000  20772  14380 S  1.3  1.0   0:38.90 lxterminal
  9497 root      20   0   46796   3844   3068 R  0.3  0.2   0:00.91 top
     1 root      20   0  138888   4500   3316 S  0.0  0.2   0:01.93 systemd
xyz@debian:~$"""

COMMAND_KWARGS_without_options = {

}

COMMAND_RESULT_without_options = {
    '%Cpu': {'IO operations': 0.0,
             'hardware interrupts': 0.0,
             'not used': 97.2,
             'software interrupts': 0.0,
             'steal time': 0.0,
             'system processes': 1.1,
             'upgraded nice': 0.0,
             'user processes': 1.8},
    'processes': [{'%CPU': 1.7,
                   '%MEM': 49.9,
                   'COMMAND': 'java',
                   'NI': 0,
                   'PID': 2642,
                   'PR': 20,
                   'RES': '0.977g',
                   'S': 'S',
                   'SHR': 18796,
                   'TIME+': '141:44.05',
                   'USER': 'bylica',
                   'VIRT': 3322120},
                  {'%CPU': 1.3,
                   '%MEM': 1.0,
                   'COMMAND': 'lxterminal',
                   'NI': 0,
                   'PID': 11447,
                   'PR': 20,
                   'RES': 20772,
                   'S': 'S',
                   'SHR': 14380,
                   'TIME+': '0:38.90',
                   'USER': 'bylica',
                   'VIRT': 325000},
                  {'%CPU': 0.3,
                   '%MEM': 0.2,
                   'COMMAND': 'top',
                   'NI': 0,
                   'PID': 9497,
                   'PR': 20,
                   'RES': 3844,
                   'S': 'R',
                   'SHR': 3068,
                   'TIME+': '0:00.91',
                   'USER': 'root',
                   'VIRT': 46796},
                  {'%CPU': 0.0,
                   '%MEM': 0.2,
                   'COMMAND': 'systemd',
                   'NI': 0,
                   'PID': 1,
                   'PR': 20,
                   'RES': 4500,
                   'S': 'S',
                   'SHR': 3316,
                   'TIME+': '0:01.93',
                   'USER': 'root',
                   'VIRT': 138888}],
    'KiB Mem ': {'cached': 382784,
                 'free': 257512,
                 'total': 2052556,
                 'used': 1412260},
    'KiB Swap': {'cached': 460660,
                 'free': 1993304,
                 'total': 2096124,
                 'used': 102820},
    'tasks': {'running': 1,
              'sleeping': 158,
              'stopped': 64,
              'total': 223,
              'zombie': 0},
    'top': {'current time': '15:08:22',
            'load average': [0.14, 0.27, 0.19],
            'up time': '3 days, 1:56',
            'users': 1}
}

COMMAND_OUTPUT_batch_mode = """
xyz@debian:~$ top b n 1
top - 13:57:54 up 3 days,  7:59,  1 user,  load average: 0.14, 0.13, 0.14
Tasks: 222 total,   1 running, 157 sleeping,  64 stopped,   0 zombie
%Cpu(s):  4.9 us,  1.1 sy,  2.4 ni, 91.5 id,  0.1 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem :  2052556 total,    95988 free,  1501316 used,   455252 buff/cache
KiB Swap:  2096124 total,  1993508 free,   102616 used.   371152 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
  566 root      20   0  479652  94132  22008 S  6.2  4.6 133:37.58 Xorg
23091 root      20   0   46668   3676   3076 R  6.2  0.2   0:00.01 top
    1 root      20   0  138888   4500   3316 S  0.0  0.2   0:02.04 systemd
    2 root      20   0       0      0      0 S  0.0  0.0   0:00.02 kthreadd
    3 root      20   0       0      0      0 S  0.0  0.0   0:03.92 ksoftirqd/0
xyz@debian:~$"""

COMMAND_KWARGS_batch_mode = {
    'options': 'b'
}

COMMAND_RESULT_batch_mode = {
    '%Cpu': {'IO operations': 0.1,
             'hardware interrupts': 0.0,
             'not used': 91.5,
             'software interrupts': 0.0,
             'steal time': 0.0,
             'system processes': 1.1,
             'upgraded nice': 2.4,
             'user processes': 4.9},
    'processes': [{'%CPU': 6.2,
                   '%MEM': 4.6,
                   'COMMAND': 'Xorg',
                   'NI': 0,
                   'PID': 566,
                   'PR': 20,
                   'RES': 94132,
                   'S': 'S',
                   'SHR': 22008,
                   'TIME+': '133:37.58',
                   'USER': 'root',
                   'VIRT': 479652},
                  {'%CPU': 6.2,
                   '%MEM': 0.2,
                   'COMMAND': 'top',
                   'NI': 0,
                   'PID': 23091,
                   'PR': 20,
                   'RES': 3676,
                   'S': 'R',
                   'SHR': 3076,
                   'TIME+': '0:00.01',
                   'USER': 'root',
                   'VIRT': 46668},
                  {'%CPU': 0.0,
                   '%MEM': 0.2,
                   'COMMAND': 'systemd',
                   'NI': 0,
                   'PID': 1,
                   'PR': 20,
                   'RES': 4500,
                   'S': 'S',
                   'SHR': 3316,
                   'TIME+': '0:02.04',
                   'USER': 'root',
                   'VIRT': 138888},
                  {'%CPU': 0.0,
                   '%MEM': 0.0,
                   'COMMAND': 'kthreadd',
                   'NI': 0,
                   'PID': 2,
                   'PR': 20,
                   'RES': 0,
                   'S': 'S',
                   'SHR': 0,
                   'TIME+': '0:00.02',
                   'USER': 'root',
                   'VIRT': 0},
                  {'%CPU': 0.0,
                   '%MEM': 0.0,
                   'COMMAND': 'ksoftirqd/0',
                   'NI': 0,
                   'PID': 3,
                   'PR': 20,
                   'RES': 0,
                   'S': 'S',
                   'SHR': 0,
                   'TIME+': '0:03.92',
                   'USER': 'root',
                   'VIRT': 0}],
    'KiB Mem ': {'cached': 455252,
                 'free': 95988,
                 'total': 2052556,
                 'used': 1501316},
    'KiB Swap': {'cached': 371152,
                 'free': 1993508,
                 'total': 2096124,
                 'used': 102616},
    'tasks': {'running': 1,
              'sleeping': 157,
              'stopped': 64,
              'total': 222,
              'zombie': 0},
    'top': {'current time': '13:57:54',
            'load average': [0.14, 0.13, 0.14],
            'up time': '3 days, 7:59',
            'users': 1}
}

COMMAND_KWARGS_grep = {"options": r"-b -n 1 | grep ^%Cpu\(s\):", 'n': None}

COMMAND_OUTPUT_grep = """
top -b -n 1 | grep ^%Cpu\\(s\\):
%Cpu(s):  2.7 us,  0.7 sy,  0.0 ni, 96.6 id,  0.1 wa,  0.0 hi,  0.0 si,  0.0 st
xyz@debian:~$
"""

COMMAND_RESULT_grep = {
    '%Cpu': {
        'user processes': 2.7,
        'system processes': 0.7,
        'not used': 96.6,
        'upgraded nice': 0.0,
        'steal time': 0.0,
        'IO operations': 0.1,
        'hardware interrupts': 0.0,
        'software interrupts': 0.0
    }
}
