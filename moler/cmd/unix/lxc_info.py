# -*- coding: utf-8 -*-
"""
LxcInfo command module.
"""

__author__ = 'Piotr Frydrych, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'piotr.frydrych@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class LxcInfo(GenericUnixCommand):
    """LxcInfo command class."""

    def __init__(self, name, connection, prompt=None, newline_chars=None, runner=None, options=None):
        """
        Lxcinfo command lists information about given container.

        :param name: name of the container
        :param connection: moler connection to device, terminal when command is executed
        :param prompt: expected prompt sending by device after command execution
        :param newline_chars: Characters to split lines
        :param runner: Runner to run command
        :param options: command options as string
        """
        super(LxcInfo, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars, runner=runner)

        self.name = name
        self.options = options
        self.current_ret["RESULT"] = dict()

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "lxc-info -n {}".format(self.name)
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            try:
                self._command_error(line)
                self._container_name_error(line)
                self._parse_table_row(line)
            except ParsingDone:
                pass
        return super(LxcInfo, self).on_new_line(line, is_full_line)

    # lxc-info: invalid option -- 'z'
    _re_command_error = re.compile(r'(?P<ERROR>lxc-info:\s+.+)', re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(LxcInfo._re_command_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))
            raise ParsingDone

    # 0xe0199 doesn't exist
    _re_container_name_error = re.compile(r'(?P<NODE_ERROR>\w*\s+doesn\'t\s+exist)', re.I)

    def _container_name_error(self, line):
        if self._regex_helper.search_compiled(LxcInfo._re_container_name_error, line):
            self.set_exception(CommandFailure(self, "NODE_ERROR: {}".format(self._regex_helper.group("NODE_ERROR"))))
            raise ParsingDone

    def _parse_table_row(self, line):
        result = dict()
        if ': ' in line:
            key, value = re.split(r':\s+', line)
            if key in self.current_ret["RESULT"].keys():
                if not isinstance(self.current_ret["RESULT"][key], list):
                    result[key] = list()
                    result[key].append(self.current_ret["RESULT"][key])
                    result[key].append(value)
                else:
                    result[key] = self.current_ret["RESULT"][key]
                    result[key].append(value)
            else:
                result[key] = value
            self.current_ret["RESULT"].update(result)
            raise ParsingDone

    _re_incorrect_node = re.compile(r'(?P<ERROR>doesn\'t exist)', re.I)


COMMAND_OUTPUT = """lxc-info -n 0xe019
Name:           0xe019
State:          RUNNING
PID:            27135
IP:             10.1.1.1
IP:             10.1.1.2
IP:             10.83.182.26
IP:             192.168.2.60
IP:             192.168.253.1
IP:             192.168.253.16
IP:             192.168.253.193
IP:             192.168.253.217
IP:             192.168.253.219
IP:             192.168.253.224
IP:             192.168.253.225
IP:             192.168.253.226
IP:             192.168.253.227
IP:             192.168.253.228
IP:             192.168.253.233
IP:             192.168.253.234
IP:             192.168.253.235
IP:             192.168.253.236
IP:             192.168.253.237
IP:             192.168.255.1
IP:             192.168.255.129
IP:             192.168.255.253
CPU use:        771.13 seconds
Memory use:     235.17 MiB
KMem use:       13.25 MiB
root@server~ >"""

COMMAND_KWARGS = {
    "name": "0xe019"
}

COMMAND_RESULT = {
    "RESULT": {"Name": "0xe019",
               "State": "RUNNING",
               "PID": "27135",
               "IP": ["10.1.1.1", "10.1.1.2", "10.83.182.26", "192.168.2.60", "192.168.253.1", "192.168.253.16",
                      "192.168.253.193", "192.168.253.217", "192.168.253.219", "192.168.253.224", "192.168.253.225",
                      "192.168.253.226", "192.168.253.227", "192.168.253.228", "192.168.253.233", "192.168.253.234",
                      "192.168.253.235", "192.168.253.236", "192.168.253.237", "192.168.255.1", "192.168.255.129",
                      "192.168.255.253"],
               "CPU use": "771.13 seconds",
               "Memory use": "235.17 MiB",
               "KMem use": "13.25 MiB"
               }
}

COMMAND_OUTPUT_2 = """root@fserver >lxc-info -n 0xe019 -s
State:          RUNNING
root@fserver >"""

COMMAND_KWARGS_2 = {
    "name": "0xe019",
    "options": "-s"
}

COMMAND_RESULT_2 = {
    "RESULT": {"State": "RUNNING"}
}

"""
=================================================HELP=MESSAGE===========================================================
root@server~ >lxc-info --help
Usage: lxc-info --name=NAME

lxc-info display some information about a container with the identifier NAME

Options :
  -n, --name=NAME       NAME of the container
  -c, --config=KEY      show configuration variable KEY from running container
  -i, --ips             shows the IP addresses
  -p, --pid             shows the process id of the init container
  -S, --stats           shows usage stats
  -H, --no-humanize     shows stats as raw numbers, not humanized
  -s, --state           shows the state of the container
  --rcfile=FILE         Load configuration file FILE

Common options :
  -o, --logfile=FILE               Output log to FILE instead of stderr
  -l, --logpriority=LEVEL          Set log priority to LEVEL
  -q, --quiet                      Don't produce any output
  -P, --lxcpath=PATH               Use specified container path
  -?, --help                       Give this help list
      --usage                      Give a short usage message
      --version                    Print the version number

Mandatory or optional arguments to long options are also mandatory or optional
for any corresponding short options.

See the lxc-info man page for further information.

"""
