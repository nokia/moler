# -*- coding: utf-8 -*-
"""
Testing command specific API

Command is a type of ConnectionObserver.
Testing ConnectionObserver API conformance of Command is done
inside test_connection_observer.py (as parametrized tests).

- call as function (synchronous)
- call as future  (asynchronous)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import importlib

import pytest
from moler.command import Command
from moler.connection import ObservableConnection
from moler.helpers import instance_id
from moler.io.raw.memory import FifoBuffer


def test_command_has_means_to_retrieve_embedded_command_string(do_nothing_command__for_major_base_class):
    """Command needs to start from sending 'command string' to some device"""
    command_instance = do_nothing_command__for_major_base_class
    assert hasattr(command_instance, "command_string")


def test_str_conversion_of_command_object():
    """
    String conversion shows embedded command string, class of command object
    and id to allow for differentiating between multiple instances of same command
    """
    class PingCmd(Command):
        def __init__(self, host='localhost', connection=None):
            super(PingCmd, self).__init__(connection=connection)
            self.command_string = 'ping {}'.format(host)

        def data_received(self, data):
            pass  # not important now

    ping = PingCmd()
    assert 'PingCmd("ping localhost", id:{})'.format(instance_id(ping)) == str(ping)

    ping = PingCmd(host='127.0.0.1')
    assert 'PingCmd("ping 127.0.0.1", id:{})'.format(instance_id(ping)) == str(ping)
    ping.command_string = ''
    assert 'PingCmd("<EMPTY COMMAND STRING>", id:{})'.format(instance_id(ping)) == str(ping)


def test_str_conversion_of_command_object_encodes_newline_for_display():
    """Important for logs and troubleshooting"""
    class PingCmd(Command):
        def __init__(self, host='localhost', connection=None):
            super(PingCmd, self).__init__(connection=connection)
            self.command_string = 'ping {}\n'.format(host)

        def data_received(self, data):
            pass  # not important now

    ping = PingCmd()
    assert r'PingCmd("ping localhost<\n>",' in str(ping)  # newline is visible in < > braces
    ping.command_string = 'ping localhost\\n'
    assert r'PingCmd("ping localhost\n",' in str(ping)  # \n (two characters string) is visible as \n  string


def test_repr_conversion_of_command_object():
    """
    repr() conversion shows same as str() plus embedded connection used by command
    """
    moler_conn = ObservableConnection(decoder=lambda data: data.decode("utf-8"))

    class LsCmd(Command):
        def __init__(self, options='-l', connection=None):
            super(LsCmd, self).__init__(connection=connection)
            self.command_string = 'ls {}'.format(options)

        def data_received(self, data):
            pass  # not important now

    ls = LsCmd(connection=moler_conn)

    # (1) command with ObservableConnection to glued to ext-io
    assert 'LsCmd("ls -l", id:{}, using ObservableConnection(id:{})-->[?])'.format(instance_id(ls), instance_id(moler_conn)) == repr(ls)
    # TODO: add test for <ObservableConnection( id:{}>

    # (2) command with ObservableConnection glued to ext-io
    ext_io_connection = FifoBuffer(moler_connection=moler_conn)
    how2send_repr = repr(ext_io_connection.write)
    assert 'LsCmd("ls -l", id:{}, using ObservableConnection(id:{})-->[{}])'.format(instance_id(ls), instance_id(moler_conn), how2send_repr) == repr(ls)
    # TODO: move ObservableConnection(id:{})-->[{}])'.format(instance_id(moler_conn), how2send_repr) into ObservableConnection __repr__ test
    # TODO: and here just:
    # assert 'LsCmd("ls -l", id:{}, using {})'.format(instance_id(ls), repr(moler_conn)) == repr(ls)

    # (3) command without connection
    ls.connection = None
    assert 'LsCmd("ls -l", id:{}, using <NO CONNECTION>)'.format(instance_id(ls)) == repr(ls)

    # TODO: generic - shift into ConnectionObserver; here just show that command's repr adds command string


def test_command_string_is_required_to_start_command(command_major_base_class):
    from moler.exceptions import NoCommandStringProvided
    moler_conn = ObservableConnection()

    command_class = do_nothing_command_class(base_class=command_major_base_class)
    command = command_class(connection=moler_conn)
    assert not command.command_string  # ensure it is empty before starting command

    with pytest.raises(NoCommandStringProvided) as error:
        command.start()  # start the command-future (background run)

    assert error.value.command == command
    assert 'for {}'.format(str(command)) in str(error.value)
    assert 'You should fill .command_string member before starting command' in str(error.value)


def test_command_string_is_required_to_call_command(command_major_base_class):
    from moler.exceptions import NoCommandStringProvided
    moler_conn = ObservableConnection()

    command_class = do_nothing_command_class(base_class=command_major_base_class)
    command = command_class(connection=moler_conn)
    assert not command.command_string  # ensure it is empty before starting command

    with pytest.raises(NoCommandStringProvided) as error:
        command()  # call the command-future (foreground run)

    assert error.value.command == command
    assert 'for {}'.format(str(command)) in str(error.value)
    assert 'You should fill .command_string member before starting command' in str(error.value)


def test_calling_command_sends_command_string_over_connection(do_nothing_command_class__for_major_base_class,
                                                              connection_to_remote):
    """Command as function"""
    from moler.exceptions import ConnectionObserverTimeout

    class QuickCmd(do_nothing_command_class__for_major_base_class):
        def await_done(self, timeout=0.1):
            return super(QuickCmd, self).await_done(timeout=timeout)

    ext_io = connection_to_remote
    ping = QuickCmd(connection=ext_io.moler_connection)
    ping.command_string = 'ping localhost'
    with ext_io:
        try:
            ping()  # call the command-future (foreground run)
        except ConnectionObserverTimeout:
            pass
        assert b'ping localhost' in ext_io.remote_endpoint()


def test_calling_start_on_command_sends_command_string_over_connection(do_nothing_command_class__for_major_base_class,
                                                                       connection_to_remote):
    """Command as future"""

    class QuickCmd(do_nothing_command_class__for_major_base_class):
        def await_done(self, timeout=0.1):
            return super(QuickCmd, self).await_done(timeout=timeout)

    ext_io = connection_to_remote
    ping = QuickCmd(connection=ext_io.moler_connection)
    ping.command_string = 'ping localhost'
    with ext_io:
        ping.start()  # start background-run of command-future
        assert b'ping localhost' in ext_io.remote_endpoint()


def test_command_is_running_after_sending_command_string(do_nothing_command__for_major_base_class):
    """
    Default behaviour is:
    after sending command string to device we treat command as running since
    we have just activated some action on device

    !!!!!!!!!!!!
    OR: when it is run in some 'feeder process' (thread, process, asyncio loop, Twisted loop)
        but even if we have no loop to progress our python-command
        the real command on device has started since we have called it over connection
    !!!!!!!!!!!!
    """
    ping = do_nothing_command__for_major_base_class

    class TheConnection(object):
        def sendline(self, data):
            assert data == 'ping localhost'  # ping command to be started on some shell
            assert ping.running()  # I'm in connection's send - command object should assume "real CMD (ping) is running"

        def subscribe(self, observer):
            pass

    ping.connection = TheConnection()
    ping.command_string = 'ping localhost'
    assert not ping.running()
    ping.start()  # start the command-future


# --------------------------- resources ---------------------------


@pytest.fixture(params=['command.Command'])
def command_major_base_class(request):
    module_name, class_name = request.param.rsplit('.', 1)
    module = importlib.import_module('moler.{}'.format(module_name))
    klass = getattr(module, class_name)
    return klass


def do_nothing_command_class(base_class):
    """Command class that can be instantiated (overwritten abstract methods); uses different base class"""
    class DoNothingCommand(base_class):
        def data_received(self, data):  # we need to overwrite it since it is @abstractmethod
            pass  # ignore incoming data
    return DoNothingCommand


@pytest.fixture
def do_nothing_command_class__for_major_base_class(command_major_base_class):
    klass = do_nothing_command_class(base_class=command_major_base_class)
    return klass


@pytest.fixture
def do_nothing_command__for_major_base_class(do_nothing_command_class__for_major_base_class):
    instance = do_nothing_command_class__for_major_base_class()
    return instance


@pytest.fixture
def connection_to_remote():
    """
    Any external-IO connection that embeds Moler-connection
    Alows to check if data send from command has reached remote side via:
    `data in conn.remote_endpoint()`
    """
    class RemoteConnection(FifoBuffer):
        def remote_endpoint(self):
            """Simulate remote endpoint that gets data"""
            return self.buffer

    ext_io = RemoteConnection(moler_connection=ObservableConnection(encoder=lambda data: data.encode("utf-8"),
                                                                    decoder=lambda data: data.decode("utf-8")))
    return ext_io
