# -*- coding: utf-8 -*-
# Copyright (C) 2018 Nokia
"""
Runner abstraction goal is to hide concurrency machinery used
to make it exchangeable (threads, asyncio, twisted, curio)
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

from moler.config import runners as runner_cfg


def get_runner(variant=None, reuse_last=True, **constructor_kwargs):
    """
    Return runner instance of given variant

    :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
    :param reuse_last: should we return cached last runner of given variant
    :param constructor_kwargs: arguments specific for given variant
    :return: requested runner

    If variant is not given then it is taken from configuration.
    """
    variant = _try_select_runner_variant(variant)

    runner = RunnerFactory.get_runner(variant, reuse_last=reuse_last, **constructor_kwargs)
    return runner


class RunnerFactory:
    """
    RunnerFactory creates plugin-system: external code can register
    "construction recipe" that will be used to create specific runner.

    "Construction recipe" means: class to be used or any other callable that can
    produce instance of runner.

    Specific means runner variant like: threaded, asyncio, twisted, ...

    ConnectionFactory responsibilities:
    - register "recipe" how to build given variant of runner
    - return runner instance created via utilizing registered "recipe"
    """
    _constructors_registry = {}
    _runners_cache = {}

    @classmethod
    def register_construction(cls, variant, constructor):  # TODO: need subvariant (asyncio-in-thread)?
        """
        Register constructor that will return "runner construction recipe"

        :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
        :param constructor: callable building runner object
        :return: None
        """
        if not callable(constructor):
            raise ValueError(
                f"constructor must be callable not {constructor}")
        cls._constructors_registry[variant] = constructor

    @classmethod
    def get_runner(cls, variant, reuse_last=True, **constructor_kwargs):
        """
        Return runner instance of given variant

        :param variant: implementation variant, ex. 'threaded', 'twisted', 'asyncio', ...
        :param reuse_last: should we return cached last runner of given variant
        :param constructor_kwargs: arguments specific for given variant
        :return: requested runner
        """
        key = variant
        if key not in cls._constructors_registry:
            raise KeyError(
                f"No constructor registered for [{key}] runner")
        if reuse_last and (key in cls._runners_cache):
            runner = cls._runners_cache[key]
        else:
            constructor = cls._constructors_registry[key]
            runner = constructor(**constructor_kwargs)
            cls._runners_cache[key] = runner
        return runner

    @classmethod
    def available_variants(cls):
        """
        Return available variants of runners

        :return: list of variants, ex. ['threaded', 'twisted']
        """
        available = cls._constructors_registry.keys()
        return available


def _try_select_runner_variant(variant):
    if variant is None:
        variant = runner_cfg.default_variant
    if variant is None:
        whats_wrong = "No variant selected"
        selection_method = "directly or via configuration"
        raise KeyError(f"{whats_wrong} ({selection_method}) for runner")
    if variant not in RunnerFactory.available_variants():
        whats_wrong = "is not registered inside RunnerFactory"
        raise KeyError(f"'{variant}' variant of runner {whats_wrong}")
    return variant


# actions during import
runner_cfg.register_builtin_runners(RunnerFactory)
