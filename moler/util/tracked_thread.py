import logging
import functools
import os
import sys
import threading
import time

# Need to store a reference to sys.exc_info for printing
# out exceptions when a thread tries to use a global var. during interp.
# shutdown and thus raises an exception about trying to perform some
# operation on/with a NoneType
_exc_info = sys.exc_info
# do_threads_debug = os.getenv('MOLER_DEBUG_THREADS', 'False').lower() in ('true', 't', 'yes', 'y', '1')
do_threads_debug = os.getenv('MOLER_DEBUG_THREADS', 'True').lower() in ('true', 't', 'yes', 'y', '1')  # just to catch that rare hanging thread issue


def log_exit_exception(fun):
    @functools.wraps(fun)
    def thread_exceptions_catcher(*args, **kwargs):
        logger = logging.getLogger("moler_threads")
        thread_name = threading.current_thread().name
        try:
            result = fun(*args, **kwargs)
            return result
        except SystemExit:
            pass
        except:  # noqa
            th_exc_info = _exc_info()
            try:
                logger.error("Exception in thread {}".format(thread_name), exc_info=th_exc_info)
            finally:
                del th_exc_info

    return thread_exceptions_catcher


def report_alive(report_tick=5.0):
    last_report_time = time.time()
    do_report = True
    while True:
        yield do_report  # TODO log long loop tick, allowed_loop_tick as param
        now = time.time()
        delay = now - last_report_time
        if delay >= report_tick:
            last_report_time = now
            do_report = do_threads_debug
        else:
            do_report = False


def threads_dumper(report_tick=10.0):
    while True:
        time.sleep(report_tick)
        logging.getLogger("moler_threads").info("ACTIVE: {}".format(threading.enumerate()))


def start_threads_dumper():
    if do_threads_debug:
        dumper = threading.Thread(target=threads_dumper)
        dumper.daemon = True
        dumper.start()
