# -*- coding: utf-8 -*-
"""
asyncio_common.py
~~~~~~~~~~~~~~~~~

Common part for asyncio examples.
"""

__author__ = 'Grzegorz Latuszek'
__copyright__ = 'Copyright (C) 2018, Nokia'
__email__ = 'grzegorz.latuszek@nokia.com'

import logging
import asyncio


def run_via_asyncio(async_to_run, debug_event_loop=False):
    logger = logging.getLogger('asyncio.main')

    asyncio.set_event_loop(asyncio.new_event_loop())
    event_loop = asyncio.get_event_loop()
    event_loop.set_debug(enabled=debug_event_loop)
    try:
        logger.info("starting events loop ...")
        event_loop.run_until_complete(async_to_run)

        # https://stackoverflow.com/questions/30765606/whats-the-correct-way-to-clean-up-after-an-interrupted-event-loop
        # https://medium.com/python-pandemonium/asyncio-coroutine-patterns-beyond-await-a6121486656f
        # Handle shutdown gracefully by waiting for all tasks to be cancelled
        logger.info("cancelling all remaining tasks")
        # NOTE: following code cancels all tasks - possibly not ours as well
        not_done_tasks = [task for task in asyncio.Task.all_tasks() if not task.done()]
        remaining_tasks = asyncio.gather(*not_done_tasks, return_exceptions=True)
        remaining_tasks.add_done_callback(lambda t: event_loop.stop())
        remaining_tasks.cancel()

        # Keep the event loop running until it is either destroyed or all
        # tasks have really terminated
        event_loop.run_until_complete(remaining_tasks)

    finally:
        logger.info("closing events loop ...")
        event_loop.close()
        logger.info("... events loop closed")
