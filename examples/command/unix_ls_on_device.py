import logging
import sys
from moler.config import load_config
from moler.device.device import DeviceFactory

def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s |%(name)-45s | %(threadName)22s |%(message)s',
        # format=' |%(name)-45s | %(threadName)12s |%(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stderr,
    )

# configure library directly from dict
load_config(config={'DEVICES': {'DEFAULT_CONNECTION':
                                    {'CONNECTION_DESC': {'io_type': 'terminal', 'variant': 'threaded'}},
                                'RebexTestMachine':
                                    {'DEVICE_CLASS': 'moler.device.unixremote.UnixRemote',
                                     'CONNECTION_HOPS': {'UNIX_LOCAL':
                                                             {'UNIX_REMOTE':
                                                                  {'execute_command': 'ssh',
                                                                   'command_params': {'expected_prompt': 'demo@',
                                                                                      'host': 'test.rebex.net',
                                                                                      'login': 'demo',
                                                                                      'password': 'password',
                                                                                      'target_newline': "\r\n",
                                                                                      'set_timeout': None}}}}}}},
            config_type='dict')

configure_logging()

remote_unix = DeviceFactory.get_device(name='RebexTestMachine')  # it starts in local shell
remote_unix.goto_state(state="UNIX_REMOTE")                      # make it go to remote shell

ls_cmd = remote_unix.get_cmd(cmd_name="ls", cmd_params={"options": "-l"})

remote_files = ls_cmd()

if 'readme.txt' in remote_files['files']:
    print("readme.txt file:")
    readme_file_info = remote_files['files']['readme.txt']
    for attr in readme_file_info:
        print(f"  {attr:<18}: {readme_file_info[attr]}")

# result:
"""
readme.txt file:
  permissions       : -rw-------
  hard_links_count  : 1
  owner             : demo
  group             : users
  size_raw          : 403
  size_bytes        : 403
  date              : Apr 08  2014
  name              : readme.txt
"""
