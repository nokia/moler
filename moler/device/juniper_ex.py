# -*- coding: utf-8 -*-
"""
JuniperEX module.
"""

__author__ = 'Sylwester Golonka'
__copyright__ = 'Copyright (C) 2019, Nokia'
__email__ = 'sylwester.golonka@nokia.com'

from moler.device.junipergeneric import JuniperGeneric


class JuniperEX(JuniperGeneric):
    def _get_packages_for_state(self, state, observer):
        available = {JuniperEX.cmds: [], JuniperEX.events: []}
        if state == JuniperEX.unix_local or state == JuniperGeneric.proxy_pc:
            available = {JuniperEX.cmds: ['moler.cmd.unix'],
                         JuniperEX.events: ['moler.events.unix']}
        elif state == JuniperGeneric.cli:
            available = {JuniperEX.cmds: ['moler.cmd.unix', 'moler.cmd.juniper.cli'],
                         JuniperEX.events: ['moler.events.unix', 'moler.events.juniper']}
        elif state == JuniperGeneric.configure:
            available = {JuniperEX.cmds: ['moler.cmd.juniper.configure'],
                         JuniperEX.events: ['moler.events.juniper']}
        return available[observer]
