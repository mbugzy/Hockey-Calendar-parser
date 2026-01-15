import logging
from datetime import datetime
import os

class Logger():
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)        
        self.formatter = logging.Formatter("{levelname} - {message}", style="{", datefmt="%H:%M")
        self.file_handler = logging.FileHandler(f"Logs/log_{datetime.now().strftime('%Y%m%d')}.log")
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message):
        self.logger.critical(message)

    def close(self):
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def clean_logs_up_to_date(self, date):
        for file in os.listdir("Logs"):
            if file.endswith(".log") and file < f'log_{date}.log':
                os.remove(os.path.join("Logs", file))