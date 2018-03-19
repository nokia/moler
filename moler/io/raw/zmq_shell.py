"""
Subprocess+ZeroMQ based connection - backend.
"""
import os
import time
import sys
import atexit

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import zmq_subprocess


if __name__ == '__main__':
    shell_path = "cmd.exe"
    # shell_path = "bash"
    command2run = [shell_path]
    zmq_proc = zmq_subprocess.Popen(command2run, stdin_port=5568, stdout_port=5569)

    def shutdown():
        print("shutting down @@@@@@@@")
        zmq_proc.stop()

    atexit.register(shutdown)

    for sec in range(20):
        time.sleep(1)  # give subprocess a chance to start
        print("running {} [sec] @@@@@@@@".format(sec+1))
    print("end of file @@@@@@@@")
