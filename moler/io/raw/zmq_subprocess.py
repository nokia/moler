"""
External-IO connections based on subprocess library with zeroMQ proxy.

ZeroMQ used to minimize impact of os.fork inside subprocess.Popen
"""
import os
import platform
import subprocess
import threading
import time

import zmq

from moler.io.raw import TillDoneThread


def create_output_socket_publisher(port):
    sock_address = 'tcp://127.0.0.1:{}'.format(port)
    python_version = platform.python_version()
    print("Python v.%s subprocess output publisher at PID:%i %s" % (python_version, os.getpid(), sock_address))
    ctx = zmq.Context()
    outsock = ctx.socket(zmq.PUB)
    outsock.bind(sock_address)
    return outsock


def create_output_socket_subsciber(port):
    sock_address = 'tcp://127.0.0.1:{}'.format(port)
    python_version = platform.python_version()
    print("Python v.%s subprocess output subscriber at PID:%i %s" % (python_version, os.getpid(), sock_address))
    ctx = zmq.Context()
    outsock = ctx.socket(zmq.SUB)
    outsock.connect(sock_address)
    topic = b'process'
    print("Subscriber receiving messages on topics: %s ..." % topic)
    outsock.setsockopt(zmq.SUBSCRIBE, topic)
    return outsock


def create_input_socket_server(port):
    sock_address = 'tcp://127.0.0.1:{}'.format(port)
    python_version = platform.python_version()
    print("Python v.%s subprocess input forwarder server at PID:%i %s" % (python_version, os.getpid(), sock_address))
    ctx = zmq.Context()
    insock = ctx.socket(zmq.PAIR)
    insock.bind(sock_address)
    return insock


def create_input_socket_client(port):
    sock_address = 'tcp://127.0.0.1:{}'.format(port)
    python_version = platform.python_version()
    print("Python v.%s subprocess input forwarder client at PID:%i %s" % (python_version, os.getpid(), sock_address))
    ctx = zmq.Context()
    insock = ctx.socket(zmq.PAIR)
    insock.connect(sock_address)
    return insock


class ZmqSubprocess(object):
    """
    Connection speaking with program running in subprocess.
    It uses ZeroMQ sockets as proxy to minimize memory usage
    (caused by fork dep inside subprocess.Popen)
    Price payed for this is additional process, 2 threads and 4 ZMQ-sockets.
    """
    def __init__(self, stdin_port, stdout_port, command='/bin/bash', args=None, env=None, starting_path=None):
        self.command = command
        self.args = [command]  # command have to be arg0
        if args:
            self.args.extend(args)
        self.env = env  # if env == None spawned bash will be given with os.environ
        self.path = starting_path
        self.forward_in_sock = create_input_socket_client(port=stdin_port)
        self.forward_out_sock = create_output_socket_subsciber(port=stdout_port)
        self._done = threading.Event()
        self._out_thread = TillDoneThread(target=self.read_subprocess_output,
                                          done_event=self._done,
                                          name="reader",
                                          kwargs={'reading_done': self._done,
                                                  'forward_sock': self.forward_out_sock})
        self.start()

    def start(self):
        self._out_thread.start()

    def stop(self):
        self._out_thread.join()

    def send(self, data):
        """
        Send data towards subprocess.

        :param data: data
        :type data: str
        """
        print("sending: {}".format(data))
        self.forward_in_sock.send_string("{}\n".format(data))

    def data_received(self, data):
        """Incoming-IO API: external-IO should call this method when data is received"""
        print("Received {}".format(data.strip()))

    def read_subprocess_output(self, reading_done, forward_sock):
        print("read_subprocess_output ... STARTED")
        while not reading_done.is_set():
            try:
                topic, message = forward_sock.recv_multipart(flags=zmq.NOBLOCK)
                # print("ZMQ Received {} output: {}".format(topic, message))
                output = message.decode("utf-8")
                self.data_received(output)
            except zmq.Again:
                pass  # no data on nonblocking zmq socket
        print("read_subprocess_output ... DONE")


class Popen(object):
    def __init__(self, command2run, stdin_port, stdout_port):
        self.command2run = command2run
        self.forward_in_sock = create_input_socket_server(port=stdin_port)
        self.forward_out_sock = create_output_socket_publisher(port=stdout_port)
        self._done = threading.Event()
        self.__subproc = subprocess.Popen(command2run,
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
        self._out_thread = TillDoneThread(target=self.forward_subprocess_output,
                                          done_event=self._done,
                                          name="puller",
                                          kwargs={'pulling_done': self._done,
                                                  'sub_process': self.__subproc,
                                                  'forward_sock': self.forward_out_sock})
        self._in_thread = TillDoneThread(target=self.forward_subprocess_input,
                                         done_event=self._done,
                                         name="injector",
                                         kwargs={'pulling_done': self._done,
                                                 'sub_process': self.__subproc,
                                                 'forward_sock': self.forward_in_sock})
        self.start()

    def start(self):
        self._out_thread.start()
        self._in_thread.start()

    def stop(self):
        self.__subproc.stdin.write("exit\n".encode("utf-8"))
        self._out_thread.join()
        self._in_thread.join()

    @staticmethod
    def forward_subprocess_output(pulling_done, sub_process, forward_sock=None):
        print("forward_subprocess_output ... STARTED")
        while not pulling_done.is_set():
            # for line in iter(sub_process.stdout.readline, b''):
            line = sub_process.stdout.readline()  # BLOCKING !!!
            topic = 'process.pid:{}'.format(sub_process.pid)
            # print("Forwarding {} output: {}".format(topic, line.strip()))
            if forward_sock:
                forward_sock.send_multipart([topic.encode('utf-8'), line])
        sub_process.stdout.close()
        print("forward_subprocess_output ... DONE")

    @staticmethod
    def forward_subprocess_input(pulling_done, sub_process, forward_sock):
        print("forward_subprocess_input ... STARTED")
        while not pulling_done.is_set():
            if sub_process.poll() is None:  # process still running
                try:
                    data = forward_sock.recv(flags=zmq.NOBLOCK)
                    print("Input forwarder received: {}".format(data))
                    if not data:  # is it same way signaling socket-closed
                        break
                    # forward data to subprocess
                    print("Forwarding {} into subprocess PID:{}".format(data, sub_process.pid))
                    sub_process.stdin.write(data)
                except zmq.Again:
                    pass  # no data on nonblocking zmq socket
            else:
                print("subprocess PID:{} is gone".format(sub_process.pid))
                break
        print("forward_subprocess_input ... DONE")


if __name__ == '__main__':
    # shell_path = "cmd.exe"
    shell_path = "bash"
    command2run = [shell_path]

    # backend
    # TODO: to be run inside separate Python process:
    # TODO: cmd2run = sys.executable
    # TODO: arg = os.path.join(os.path.dirname(__file__), "zmq_shell.py")
    # TODO: os.spawnv(os.P_NOWAIT, cmd2run, (cmd2run, arg))
    zmq_proc = Popen(command2run, stdin_port=5568, stdout_port=5569)

    # frontend
    shell_connection = ZmqSubprocess(command=command2run, stdin_port=5568, stdout_port=5569)

    time.sleep(2)  # give subprocess a chance to start
    # shell_connection.send("dir")
    shell_connection.send("ls -l")
    time.sleep(3)  # give other threads a chance to handle cmd just sent

    print("awaiting threads join")
    zmq_proc.stop()
    shell_connection.stop()
    print("all threads done")
