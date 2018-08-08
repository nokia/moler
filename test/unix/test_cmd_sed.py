# -*- coding: utf-8 -*-
"""
Testing of sed command.
"""

__author__ = 'Agnieszka Bylica'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'agnieszka.bylica@nokia.com'


from moler.exceptions import CommandFailure
from moler.cmd.unix.sed import Sed
import pytest


def test_sed_returns_proper_command_string(buffer_connection):
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old2"], options="-r",
                  scripts=["s/a/A/"])
    assert "sed -r -e 's/a/A/' old2" == sed_cmd.command_string


def test_sed_returns_proper_command_string_with_files(buffer_connection):
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old", "old2"], scripts=["s/a/A/"],
                  output_file="new")
    assert "sed -e 's/a/A/' old old2 > new" == sed_cmd.command_string


def test_sed_returns_proper_command_string_with_script_file(buffer_connection):
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old", "old2"], script_files=["script"],
                  output_file="new")
    assert "sed -f script old old2 > new" == sed_cmd.command_string


def test_sed_catches_command_failure(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_command_failure()
    buffer_connection.remote_inject_response([command_output])
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old", "old2"], scripts=["s/a/A"])
    with pytest.raises(CommandFailure):
        sed_cmd()


def test_sed_catches_command_failure_empty_input_file(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_command_failure_empty_input_file()
    buffer_connection.remote_inject_response([command_output])
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["", " "], scripts=["s/a/A/"])
    with pytest.raises(CommandFailure):
        sed_cmd()


def test_sed_catches_command_failure_no_script(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_command_failure_no_script()
    buffer_connection.remote_inject_response([command_output])
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old"],
                  scripts=["", " "], script_files=[" ", " "])
    assert "sed -e '' -e ' ' -f   -f   old" == sed_cmd.command_string
    with pytest.raises(CommandFailure):
        sed_cmd()


def test_sed_catches_option_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_option_error()
    buffer_connection.remote_inject_response([command_output])
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old", "old2"], options="-h",
                  scripts=["s/a/A/"])
    with pytest.raises(CommandFailure):
        sed_cmd()


def test_sed_catches_file_error(buffer_connection):
    command_output, expected_result = command_output_and_expected_result_file_error()
    buffer_connection.remote_inject_response([command_output])
    sed_cmd = Sed(connection=buffer_connection.moler_connection, input_files=["old", "old3"], scripts=["s/a/A/"])
    with pytest.raises(CommandFailure):
        sed_cmd()


@pytest.fixture
def command_output_and_expected_result_command_failure():
    data = """xyz@debian:~$ sed -e 's/a/A' old old2
sed: -e expression #1, char 5: unterminated `s' command
xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_command_failure_empty_input_file():
    data = """xyz@debian:~$ sed -e 's/a/A'

xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_command_failure_no_script():
    data = """xyz@debian:~$ sed -e '' -e ' ' -f   -f   old
    sed: couldn't open file -f: No such file or directory
    xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_option_error():
    data = """xyz@debian:~$ sed -h -e 's/a/A/' old old2
sed: invalid option -- 'h'
Usage: sed [OPTION]... {script-only-if-no-other-script} [input-file]...

  -n, --quiet, --silent
                 suppress automatic printing of pattern space
  -e script, --expression=script
                 add the script to the commands to be executed
  -f script-file, --file=script-file
                 add the contents of script-file to the commands to be executed
  --follow-symlinks
                 follow symlinks when processing in place
  -i[SUFFIX], --in-place[=SUFFIX]
                 edit files in place (makes backup if SUFFIX supplied)
  -l N, --line-length=N
                 specify the desired line-wrap length for the `l' command
  --posix
                 disable all GNU extensions.
  -E, -r, --regexp-extended
                 use extended regular expressions in the script
                 (for portability use POSIX -E).
  -s, --separate
                 consider files as separate rather than as a single,
                 continuous long stream.
      --sandbox
                 operate in sandbox mode.
  -u, --unbuffered
                 load minimal amounts of data from the input files and flush
                 the output buffers more often
  -z, --null-data
                 separate lines by NUL characters
      --help     display this help and exit
      --version  output version information and exit

If no -e, --expression, -f, or --file option is given, then the first
non-option argument is taken as the sed script to interpret.  All
remaining arguments are names of input files; if no input files are
specified, then the standard input is read.

GNU sed home page: <http://www.gnu.org/software/sed/>.
General help using GNU software: <http://www.gnu.org/gethelp/>.
xyz@debian:~$"""
    result = dict()
    return data, result


@pytest.fixture
def command_output_and_expected_result_file_error():
    data = """xyz@debian:~$ sed -e 's/a/A/' old old3
Apple
peAr
plum
sed: can't read old3: No such file or directory
xyz@debian:~$"""
    result = dict()
    return data, result
