# -*- coding: utf-8 -*-
"""
LxcAttach command module.
"""


__author__ = 'Agnieszka Bylica, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2020, Nokia'
__email__ = 'agnieszka.bylica@nokia.com, marcin.usielski@nokia.com'


from moler.cmd.commandchangingprompt import CommandChangingPrompt
from moler.exceptions import CommandFailure
from moler.exceptions import ParsingDone
import re


class LxcAttach(CommandChangingPrompt):
    """LxcAttach command class."""

    def __init__(self, name, connection, prompt=None, newline_chars=None, runner=None, options=None,
                 expected_prompt=None):
        """
        Lxcattach command attaches to specified gNB.

        :param connection: moler connection to device, terminal when command is executed.
        :param prompt: expected prompt sending by device after command execution.
        :param newline_chars: Characters to split lines.
        :param runner: Runner to run command.
        :param name: name of the container.
        :param options: command options as string.
        :param expected_prompt: prompt after calling command.
        """
        super(LxcAttach, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                        runner=runner, expected_prompt=expected_prompt)

        self.name = name
        self.options = options
        self.ret_required = False

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """
        cmd = f"lxc-attach --name={self.name}"
        if self.options:
            cmd = f"{cmd} {self.options}"
        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Put your parsing code here.

        :param line: Line to process, can be only part of line. New line chars are removed from line.
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        try:
            self._command_error(line)
        except ParsingDone:
            pass
        super(LxcAttach, self).on_new_line(line, is_full_line)

    # lxc-attach: 0x2013: attach.c: lxc_attach: 843 Failed to get init pid.
    _re_command_error = re.compile(r'(?P<ERROR>lxc-attach:\s+.+)', re.I)

    def _command_error(self, line):
        if self._regex_helper.search_compiled(LxcAttach._re_command_error, line):
            self.set_exception(CommandFailure(self, f"ERROR: {self._regex_helper.group('ERROR')}"))
            raise ParsingDone()


COMMAND_OUTPUT = """root@server:~ >lxc-attach --name=0xe089
root@0xe089:~ >"""

COMMAND_KWARGS = {
    "name": "0xe089"
}

COMMAND_RESULT = {}


COMMAND_OUTPUT_2 = """root@server:~ >lxc-attach --name=0x2015 --quiet
root@0x2015:~ >"""

COMMAND_KWARGS_2 = {
    "name": "0x2015",
    "options": "--quiet"
}

COMMAND_RESULT_2 = {}


# =================================================HELP=MESSAGE===========================================================
# root@0xe000:~ >lxc-attach --help
# Usage: lxc-attach --name=NAME [-- COMMAND]

# Execute the specified COMMAND - enter the container NAME

# Options :
#   -n, --name=NAME   NAME of the container
#   -e, --elevated-privileges=PRIVILEGES
#                     Use elevated privileges instead of those of the
#                     container. If you don't specify privileges to be
#                     elevated as OR'd list: CAP, CGROUP and LSM (capabilities,
#                     cgroup and restrictions, respectively) then all of them
#                     will be elevated.
#                     WARNING: This may leak privileges into the container.
#                     Use with care.
#   -a, --arch=ARCH   Use ARCH for program instead of container's own
#                     architecture.
#   -s, --namespaces=FLAGS
#                     Don't attach to all the namespaces of the container
#                     but just to the following OR'd list of flags:
#                     MOUNT, PID, UTSNAME, IPC, USER or NETWORK.
#                     WARNING: Using -s implies -e with all privileges
#                     elevated, it may therefore leak privileges into the
#                     container. Use with care.
#   -R,--remount-sys-proc
#                     Remount /sys and /proc if not attaching to the
#                     mount namespace when using -s in order to properly
#                     reflect the correct namespace context. See the
#                     lxc-attach(1) manual page for details.
#       --clear-env   Clear all environment variables before attaching.
#                     The attached shell/program will start with only
#                     container=lxc set.
#       --keep-env    Keep all current environment variables. This
#                     is the current default behaviour, but is likely to
#                     change in the future.
#   -L, --pty-log=FILE
#                     Log pty output to FILE
#   -v, --set-var     Set an additional variable that is seen by the
#                     attached program in the container. May be specified
#                     multiple times.
#       --keep-var    Keep an additional environment variable. Only
#                     applicable if --clear-env is specified. May be used
#                     multiple times.
#   -f, --rcfile=FILE
#                     Load configuration file FILE

# Common options :
#   -o, --logfile=FILE               Output log to FILE instead of stderr
#   -l, --logpriority=LEVEL          Set log priority to LEVEL
#   -q, --quiet                      Don't produce any output
#   -P, --lxcpath=PATH               Use specified container path
#   -?, --help                       Give this help list
#       --usage                      Give a short usage message
#       --version                    Print the version number

# Mandatory or optional arguments to long options are also mandatory or optional
# for any corresponding short options.

# See the lxc-attach man page for further information.
