# -*- coding: utf-8 -*-
"""
GetHwInventoryInfo AsiMgr command module.

:copyright: Nokia Networks
:author: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
:maintainer: I_MOLER_DEV
:contact: I_MOLER_DEV@internal.nsn.com
"""

__author__ = 'Szymon Czaplak'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'szymon.czaplak@nokia.com'

import re

from moler.cmd.unix.genericunix import GenericUnixCommand
from moler.exceptions import ParsingDone
from moler.exceptions import CommandFailure


class Journalctl(GenericUnixCommand):
    """Journalctl command class."""
    _re_outline= re.compile(r"(?P<DATE>^[\D]+ [\d]+\s[\d]+:[\d]+:[\d]+\s)(?P<CODE>[\w-]+\s)(?P<NAME>[\w\d\[\]]+):(?P<MSG>.*$)")

    def __init__(self, connection, prompt=None, newline_chars=None, runner=None, options=None,
                 expected_prompt=r'[^@]+@0x[^>]+>'):
        """
        Journalctl command attaches to specified gNB.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: expected prompt sending by device after command execution.
        :param newline_chars: Characters to split lines.
        :param runner: Runner to run command.
        :param options: command options as string.
        :param expected_prompt: prompt after calling command.
        """
        super(Journalctl, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                         runner=runner)

        self.options = options
        if expected_prompt:
            self._re_expected_prompt = GenericUnixCommand._calculate_prompt(expected_prompt)
        self.ret_required = False

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = "journalctl"
        if self.options:
            cmd = "{} {}".format(cmd, self.options)
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: Nothing
        """
        try:
            self._command_error(line)
            self._is_target_prompt(line)
            self._parse_line_complete(line)
        except ParsingDone:
            pass
        super(Journalctl, self).on_new_line(line, is_full_line)


    def _command_error(self, line):
        re_command_error = re.compile(r'(?P<ERROR>No journal files were opened\s+.+)', re.I)

        if self._regex_helper.search_compiled(re_command_error, line):
            self.set_exception(CommandFailure(self, "ERROR: {}".format(self._regex_helper.group("ERROR"))))

    def _is_target_prompt(self, line):
        if self._regex_helper.search_compiled(self._re_expected_prompt, line):
            if not self.done():
                self.set_result({})

    def _parse_line_complete(self, line):
        if self._regex_helper.search_compiled(Journalctl._re_outline, line):
            self.curr_out = {
                "DATE": self._regex_helper.group(1),
                "CODE": self._regex_helper.group(2),
                "NAME": self._regex_helper.group(3),
                "MSG": self._regex_helper.group(4)
            }
            raise ParsingDone





COMMAND_OUTPUT = """root@fct-0a:~ >journalctl --system
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Connection (1): Incoming message
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Request Type is HttpSupervision
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: SMA_XOHMessageInterpreter:: Message Type = HttpSupervision
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: ::SMA_XOHBTSOMForwarder:: Forward message to BTSOM.
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Connection (1): Finished handling message
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Calling handle_input with FD :: 12
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Connection (2): Incoming message
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Response Type is HttpSupervision
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: SMA_XOHMessageInterpreter:: Message Type = HttpSupervision
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Sent HttpSupervision to SEM
Apr 10 18:08:34 fct-0a SmaLiteXoh[26334]: Connection (2): Finished handling message
root@0xe019:~ >"""

COMMAND_KWARGS = {
    "options": "--system"
}

COMMAND_RESULT = {}

"""
=================================================HELP=MESSAGE===========================================================
root@0xe000:~ >journalctl --help
journalctl [OPTIONS...] [MATCHES...]

Query the journal.

Options:
     --system              Show the system journal
     --user                Show the user journal for the current user
  -M --machine=CONTAINER   Operate on local container
  -S --since=DATE          Show entries not older than the specified date
  -U --until=DATE          Show entries not newer than the specified date
  -c --cursor=CURSOR       Show entries starting at the specified cursor
     --after-cursor=CURSOR Show entries after the specified cursor
     --show-cursor         Print the cursor after all the entries
  -b --boot[=ID]           Show current boot or the specified boot
     --list-boots          Show terse information about recorded boots
  -k --dmesg               Show kernel message log from the current boot
  -u --unit=UNIT           Show logs from the specified unit
     --user-unit=UNIT      Show logs from the specified user unit
  -t --identifier=STRING   Show entries with the specified syslog identifier
  -p --priority=RANGE      Show entries with the specified priority
  -e --pager-end           Immediately jump to the end in the pager
  -f --follow              Follow the journal
  -n --lines[=INTEGER]     Number of journal entries to show
     --no-tail             Show all lines, even in follow mode
  -r --reverse             Show the newest entries first
  -o --output=STRING       Change journal output mode (short, short-precise,
                             short-iso, short-full, short-monotonic, short-unix,
                             verbose, export, json, json-pretty, json-sse, cat)
     --utc                 Express time in Coordinated Universal Time (UTC)
  -x --catalog             Add message explanations where available
     --no-full             Ellipsize fields
  -a --all                 Show all fields, including long and unprintable
  -q --quiet               Do not show info messages and privilege warning
     --no-pager            Do not pipe output into a pager
     --no-hostname         Suppress output of hostname field
     -m --merge               Show entries from all available journals
  -D --directory=PATH      Show journal files from directory
     --file=PATH           Show journal file
     --root=ROOT           Operate on files below a root directory
     --interval=TIME       Time interval for changing the FSS sealing key
     --verify-key=KEY      Specify FSS verification key
     --force               Override of the FSS key pair with --setup-keys

Commands:
  -h --help                Show this help text
     --version             Show package version
  -N --fields              List all field names currently used
  -F --field=FIELD         List all values that a specified field takes
     --disk-usage          Show total disk usage of all journal files
     --vacuum-size=BYTES   Reduce disk usage below specified size
     --vacuum-files=INT    Leave only the specified number of journal files
     --vacuum-time=TIME    Remove journal files older than specified time
     --verify              Verify journal file consistency
     --sync                Synchronize unwritten journal messages to disk
     --flush               Flush all journal data from /run into /var
     --rotate              Request immediate rotation of the journal files
     --header              Show journal header information
     --list-catalog        Show all message IDs in the catalog
     --dump-catalog        Show entries in the message catalog
     --update-catalog      Update the message catalog database
     --new-id128           Generate a new 128-bit ID
     --setup-keys          Generate a new FSS key pair

"""
