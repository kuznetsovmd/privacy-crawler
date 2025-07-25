import atexit
import sys
import logging
import signal
import logging.handlers

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import cpu_count, Pool

from active_modules import active_modules

from env import config
from crawler.web.driver import Driver
from tools.functions import get_logger, init


class ExitFilter(logging.Filter):
    def filter(self, record):
        if not record.exc_info:
            return True
        _, exc_value, _ = record.exc_info
        return not isinstance(exc_value, (SystemExit, BrokenPipeError))


def sysexit(*_):
    logger = get_logger()
    logger.info("Closing worker")
    raise SystemExit(0)


def init_logger(queue):
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    h = logging.handlers.QueueHandler(queue)
    root.addHandler(h)


def worker_constructor(queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, sysexit)
    atexit.register(worker_destructor)
    init_logger(queue)


def worker_destructor():
    Driver.close()


def logger_initializer(queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    f = logging.Formatter("%(asctime)s - [%(name)s] %(levelname)s: %(message)s", "%H:%M:%S")
    h = logging.StreamHandler(sys.stdout)
    h.addFilter(ExitFilter())
    h.setLevel(logging.INFO)
    h.setFormatter(f)
    logging.getLogger().addHandler(h)
    while True:
        record = queue.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def main():
    sys.stderr = open(".stderr.log", "a", buffering=1)
    init(config.path)

    proc_count = config.sub_proc_count if config.sub_proc_count > 1 else cpu_count()

    queue = Queue(-1)
    logger_process = Process(target=logger_initializer, args=(queue,))
    logger_process.start()

    init_logger(queue)

    logger = get_logger()
    logger.info(f"Using thread count: {proc_count}")

    Driver.check_installation(config.webdriver_settings)

    p = Pool(proc_count, initializer=worker_constructor, initargs=(queue,))

    try:
        for m in active_modules:
            m.run(p)
        p.close()

    except KeyboardInterrupt:
        logger.info("Keyboard interruption, closing gracefully")
        p.terminate()

    except Exception:
        p.terminate()
        raise

    finally:
        p.join()

        logger.info("Shutting down")
        queue.put_nowait(None)
        logger_process.join()


if __name__ == "__main__":
    default_stderr = sys.stderr
    try:
        main()
    except Exception as e:
        sys.stderr = default_stderr
        raise e
