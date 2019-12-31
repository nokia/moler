# -*- coding: utf-8 -*-
"""
Runners related configuration
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import sys

default_variant = "threaded"


def set_default_variant(variant):
    """Set variant to use as default when requesting runner"""
    global default_variant
    default_variant = variant


def clear():
    """Cleanup configuration related to runners"""
    global default_variant
    default_variant = "threaded"


def register_builtin_runners(runner_factory):
    _register_builtin_runners(runner_factory)
    if (sys.version_info[0] >= 3) and (sys.version_info[1] >= 5):
        _register_python3_builtin_runners(runner_factory)


def _register_builtin_runners(runner_factory):
    from moler.runner import ThreadPoolExecutorRunner

    def thd_runner(executor=None):
        runner = ThreadPoolExecutorRunner(executor=executor)
        return runner

    runner_factory.register_construction(variant="threaded", constructor=thd_runner)


def _register_python3_builtin_runners(runner_factory):
    from moler.asyncio_runner import AsyncioRunner
    from moler.asyncio_runner import AsyncioInThreadRunner

    def asyncio_runner():
        runner = AsyncioRunner()
        return runner

    def asyncio_thd_runner():
        runner = AsyncioInThreadRunner()
        return runner

    runner_factory.register_construction(variant="asyncio", constructor=asyncio_runner)
    runner_factory.register_construction(variant="asyncio-in-thread", constructor=asyncio_thd_runner)
