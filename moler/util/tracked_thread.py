import logging
import functools
import sys
import threading
import time

# Need to store a reference to sys.exc_info for printing
# out exceptions when a thread tries to use a global var. during interp.
# shutdown and thus raises an exception about trying to perform some
# operation on/with a NoneType
_exc_info = sys.exc_info


def track_target(fun):
    @functools.wraps(fun)
    def wrapped(*args, **kwargs):
        logger = logging.getLogger("moler_threads")
        thread_name = threading.current_thread().name
        try:
            logger.debug("Entering thread {}".format(thread_name))
            result = fun(*args, **kwargs)
            return result
        except SystemExit:
            pass
        except:
            th_exc_info = _exc_info()
            try:
                logger.error("Exception in thread {}".format(thread_name), exc_info=th_exc_info)

            finally:
                del th_exc_info
        finally:
            logger.debug("Exited   thread {}".format(thread_name))

    return wrapped


def report_alive(report_tick=1.0):
    logger = logging.getLogger("moler_threads")
    logger.debug("I'm alive")
    last_report_time = time.time()
    while True:
        yield
        now = time.time()
        delay = now - last_report_time
        if delay >= report_tick:
            logger.debug("I'm alive")
            last_report_time = now
