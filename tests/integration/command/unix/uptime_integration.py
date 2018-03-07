import pytest


def test_calling_uptime_returns_result_parsed_from_command_output(buffer_connection):
    from command.unix.uptime import Uptime
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    uptime_cmd = Uptime(connection=buffer_connection.moler_connection)
    result = uptime_cmd()
    assert result == expected_result


def command_output_and_expected_result():
    data = """
fzm-tdd-1:~ # uptime
 10:38am  up 3 days  2:14,  29 users,  load average: 0.09, 0.10, 0.07
fzm-tdd-1:~ #  
    """
    result = {
            "UPTIME": '3 days  2:14',
            "UPTIME_SECONDS": 8040,
            "USERS": '29',
             }
    return data, result
