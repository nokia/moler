# -*- coding: utf-8 -*-
"""
Testing of id command.
"""
__email__ = 'michal.ernst@nokia.com'


def test_id_returns_proper_command_string(buffer_connection):
    from moler.cmd.unix.id import Id
    id_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    assert "id user" == id_cmd.command_string


def test_calling_id_returns_result_parsed_from_command_output(buffer_connection):
    from moler.cmd.unix.id import Id
    command_output, expected_result = command_output_and_expected_result()
    buffer_connection.remote_inject_response([command_output])
    cd_cmd = Id(connection=buffer_connection.moler_connection, user="user")
    result = cd_cmd()
    assert result == expected_result


def command_output_and_expected_result():
    data = """
host:~ # id user
uid=1000(user) gid=1000(user) groups=1000(user),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),108(netdev),110(lpadmin),113(scanner),118(bluetooth)
host:~ #
"""
    result = {
        'UID': [
            {
                'ID': 1000,
                'NAME': 'user'
            },
        ],
        'GID': [
            {
                'ID': 1000,
                'NAME': 'user'
            }
        ],
        'GROUPS': [
            {
                'ID': 1000,
                'NAME': 'user'
            },
            {
                'ID': 24,
                'NAME': 'cdrom'
            },
            {
                'ID': 25,
                'NAME': 'floppy'
            },
            {
                'ID': 29,
                'NAME': 'audio'
            },
            {
                'ID': 30,
                'NAME': 'dip'
            },
            {
                'ID': 44,
                'NAME': 'video'
            },
            {
                'ID': 46,
                'NAME': 'plugdev'
            },
            {
                'ID': 108,
                'NAME': 'netdev'
            },
            {
                'ID': 110,
                'NAME': 'lpadmin'
            },
            {
                'ID': 113,
                'NAME': 'scanner'
            },
            {
                'ID': 118,
                'NAME': 'bluetooth'
            }
        ]
    }
    return data, result
