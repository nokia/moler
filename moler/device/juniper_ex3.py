# -*- coding: utf-8 -*-
"""
JuniperEX module.
"""

__author__ = 'Sylwester Golonka, Jakub Kupiec, Marcin Usielski'
__copyright__ = 'Copyright (C) 2019-2025, Nokia'
__email__ = 'sylwester.golonka@nokia.com, jakub.kupiec@nokia.com, marcin.usielski@nokia.com'

from moler.device.junipergeneric3 import JuniperGeneric3
from moler.helpers import call_base_class_method_with_same_name


@call_base_class_method_with_same_name
class JuniperEX3(JuniperGeneric3):
    r"""
    Juniperex device class.


    ::


      Example of device in yaml configuration file:
      - with PROXY_PC:
        JUNIPER_EX_PROXY_PC:
          DEVICE_CLASS: moler.device.juniper_ex3.JuniperEX3
          CONNECTION_HOPS:
            PROXY_PC:
              CLI:
                execute_command: ssh
                command_params:
                  host: cli_host
                  login: cli_login
                  password: password
            UNIX_LOCAL:
              PROXY_PC:
                execute_command: ssh
                command_params:
                  expected_prompt: "proxy_pc#"
                  host: proxy_pc_host
                  login: proxy_pc_login
                  password: password
            CLI:
              PROXY_PC:
                execute_command: exit
                command_params:
                  expected_prompt: "proxy_pc#"
      - without PROXY_PC:
        JUNIPER_EX:
          DEVICE_CLASS: moler.device.juniper_ex3.JuniperEX3
          CONNECTION_HOPS:
            UNIX_LOCAL:
              CLI:
                execute_command: ssh # default value
                command_params:
                  host: cli_host
                  login: cli_login
                  password: password
    """
