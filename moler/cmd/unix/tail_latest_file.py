# -*- coding: utf-8 -*-
"""
Tail latest file from the  directory.
"""

import os
import time
from moler.cmd.unix.genericunix import GenericUnixCommand

__author__ = 'Tomasz Krol'
__copyright__ = 'Copyright (C) 2020, Nokia'
__email__ = 'tomasz.krol@nokia.com'


class TailLatestFile(GenericUnixCommand):
    def __init__(self, connection, directory, file_pattern="*", prompt=None, newline_chars=None, runner=None,
                 time_for_failure=0.1):
        """
        Command for tail latest file from the directory.
        :param connection: Moler connection to device, terminal when command is executed.
        :param directory: path to directory to tail.
        :param file_pattern: pattern for files from directory.
        :param prompt: prompt (on system where command runs).
        :param newline_chars: Characters to split lines - list.
        :param runner: Runner to run command.
        :param time_for_failure: time (in seconds) for failure indication from first line of output. Set to 0 if skip
        all failure indications.
        """
        super(TailLatestFile, self).__init__(connection=connection, prompt=prompt, newline_chars=newline_chars,
                                             runner=runner)

        self.directory = directory
        self.file_pattern = file_pattern
        self.ret_required = False
        self.time_for_failure = time_for_failure
        self._first_line_time = None
        self._check_failure_indication = True

        self._multiline_cmd = True

    def build_command_string(self):
        """
        Build command string from parameters passed to object.

        :return: String representation of command to send over connection to device.
        """

        file_path = os.path.join(self.directory, self.file_pattern)
        bash_script = "bash -c '\n" \
                      'echo "Press [CTRL+C] to stop.."\n' \
                      r'trap "kill \$tail_pid; exit" INT' \
                      '\n' \
                      'last_file=""\n' \
                      'tail_pid=""\n' \
                      'file_index=0\n' \
                      'while :\n' \
                      'do\n' \
                      'current_last_file=`ls -t {} | head -1`\n' \
                      'if [ "$last_file" != "$current_last_file" ]\n' \
                      'then\n' \
                      '[ -n "$tail_pid" ] && kill $tail_pid\n' \
                      'last_file=$current_last_file\n' \
                      'if [ "$file_index" -eq 0 ]\n' \
                      'then\n' \
                      'tail -f $last_file &\n' \
                      'else\n' \
                      'tail -f -n +1 $last_file &\n' \
                      'fi\n' \
                      'tail_pid=$!\n' \
                      '((file_index=file_index+1))\n' \
                      'fi\n' \
                      'sleep 0.5\n' \
                      "done'"

        cmd = bash_script.format(file_path)

        return cmd

    def on_new_line(self, line, is_full_line):
        """
        Parse line from command output.

        :param line: Line from device
        :param is_full_line: True if line had new line chars, False otherwise
        :return: None
        """
        if is_full_line:
            if not self._first_line_time:
                self._first_line_time = time.time()
        super(TailLatestFile, self).on_new_line(line=line, is_full_line=is_full_line)

    def is_failure_indication(self, line):
        """
        Check if line has info about failure indication.

        :param line: Line from device
        :return: None if line does not match regex with failure, Match object if line matches the failure regex.
        """
        if self._check_failure_indication:
            if time.time() - self._first_line_time < self.time_for_failure:
                return self._regex_helper.search_compiled(self._re_fail, line)
            else:
                self._check_failure_indication = False  # do not check time for future output. It's too late already.
        return None


COMMAND_OUTPUT = r"""
user@host:~$ bash -c '
echo "Press [CTRL+C] to stop.."
trap "kill \$tail_pid; exit" INT
last_file=""
tail_pid=""
file_index=0
while :
do
current_last_file=`ls -t /tmp/sample_file* | head -1`
if [ "$last_file" != "$current_last_file" ]
then
[ -n "$tail_pid" ] && kill $tail_pid
last_file=$current_last_file
if [ "$file_index" -eq 0 ]
then
tail -f $last_file &
else
tail -f -n +1 $last_file &
fi
tail_pid=$!
((file_index=file_index+1))
fi
sleep 0.5
done'
Press [CTRL+C] to stop..
VmallocChunk:   34359608824 kB
HardwareCorrupted:     0 kB
AnonHugePages:         0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
DirectMap4k:       53184 kB
DirectMap2M:     4141056 kB
user@host:~$
"""

COMMAND_RESULT = {}

COMMAND_KWARGS = {
    "directory": "/tmp",
    "file_pattern": "sample_file*",
}


COMMAND_OUTPUT_command_not_found_in_output = r"""
user@server:~> bash -c '
echo "Press [CTRL+C] to stop.."
trap "kill \$tail_pid; exit" INT
last_file=""
tail_pid=""
file_index=0
while :
do
current_last_file=`ls -t /tmp/* | head -1`
if [ "$last_file" != "$current_last_file" ]
then
[ -n "$tail_pid" ] && kill $tail_pid
last_file=$current_last_file
if [ "$file_index" -eq 0 ]
then
tail -f $last_file &
else
tail -f -n +1 $last_file &
fi
tail_pid=$!
((file_index=file_index+1))
fi
sleep 0.5
done'
36B9 INF/LFS/LinuxSyslog error=No such file or directory
user@server:~>"""

COMMAND_RESULT_command_not_found_in_output = {
}

COMMAND_KWARGS_command_not_found_in_output = {
    "directory": "/tmp",
    "time_for_failure": 0
}
