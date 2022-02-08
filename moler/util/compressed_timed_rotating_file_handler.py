import subprocess
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler


class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, compress_command='zip -9mq {packed} {log_input}', compress_suffix='.zip', *args, **kwargs):
        self.compress_command = compress_command
        self.compress_suffix = compress_suffix
        super(CompressedTimedRotatingFileHandler, self).__init__(*args, **kwargs)

    def rotate(self, source, dest):
        super(CompressedTimedRotatingFileHandler, self).rotate(source, dest)
        full_pack_command = self.compress_command.format(packed=dest + self.compress_suffix, log_input=dest)
        subprocess.Popen(full_pack_command.split())
