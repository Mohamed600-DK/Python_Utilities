#!/usr/bin/env python3.10

import os
from enum import Enum
import logging
from  .files_handler import create_logfile

class LOG_LEVEL(Enum):
    DEBUG = 0
    INFO = 1
    ERROR = 2
    CRITICAL = 3
    WARNING = 4





class Stream__ColoredFormatter(logging.Formatter):
    # Define color codes
    class LogColors:
        RESET = "\033[0m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
    # Define colors for different log levels
    COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.MAGENTA,
    }
    def format(self, record):
        # Get the color based on the log level
        color = self.COLORS.get(record.levelno, self.LogColors.WHITE)
        # Apply the color to the level name
        record.levelname = f"{color}{record.levelname}{self.LogColors.WHITE}"
        return super().format(record)
class File__ColoredFormatter(logging.Formatter):
    # Define color codes
    class LogColors:
        RESET = "\033[0m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
    # Define colors for different log levels
    COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.MAGENTA,
    }

    def format(self, record):
        # Get the color based on the log level
        color = self.COLORS.get(record.levelno, self.LogColors.WHITE)
        # Apply the color to the level name
        record.levelname = f"{color}{record.levelname}{self.LogColors.WHITE}"
        return super().format(record)



# ANSI escape codes for colors
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
class loggingFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.DEBUG, logging.ERROR)
class LOGGER:
    LOGLEVEL=LOG_LEVEL
    def __init__(self,logger_name):
        if logger_name != None:
            self.__logger=logging.Logger(logger_name)
            self.__logger.setLevel(logging.DEBUG)
        else:
            self.__logger=None

    def create_File_logger(self,logs_name:str):
        file_path=create_logfile(logs_name)
        file_logger=logging.FileHandler(file_path)
        logger_formate_file=logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # logger_formate_file=File__ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_logger.setFormatter(logger_formate_file)
        # Custom filter to allow only DEBUG and ERROR logs
        file_logger.addFilter(loggingFilter())  # Apply the filter
        self.__logger.addHandler(file_logger)

    def create_Stream_logger(self):
        Stream_logger=logging.StreamHandler()
        # logger_formate_consol=logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger_formate_consol=Stream__ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        Stream_logger.setFormatter(logger_formate_consol)
        # Stream_logger.setFormatter(self.__logger_formate_consol)
        Stream_logger.setLevel(logging.INFO)
        self.__logger.addHandler(Stream_logger)
    
    def write_logs(self,logs_message,logs_level:LOG_LEVEL):
        if self.__logger:
            if logs_level==logs_level.DEBUG:
                self.__logger.debug(logs_message)
            elif logs_level==logs_level.INFO:
                self.__logger.info(logs_message)
            elif logs_level==logs_level.ERROR:
                self.__logger.error(logs_message)
            elif logs_level==logs_level.CRITICAL:
                self.__logger.critical(logs_message)
            elif logs_level==logs_level.WARNING:
                self.__logger.warning(logs_message)
            else:
                raise ValueError()


