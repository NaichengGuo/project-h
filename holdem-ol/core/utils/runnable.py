import traceback

from core.utils.logger import log


class Runnable(object):
    @staticmethod
    def run(func, name: str = 'unknown'):
        try:
            func()
        except KeyboardInterrupt:
            log.error(f'{name} stopped by keyboard interrupt')
        except Exception as e:
            log.error(f'{name} stopped by exception')
            log.error(traceback.format_exc())
            traceback.print_exc()
            print()
            raise e
