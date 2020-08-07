import logging
import json


class Logger_Engine():
    """Logger Engine Class

    Enables us to configure how we want to log information while executing the program

    Attributes:
        logger: Logging.Logger object fully configured on how we want to log
        formatter: Formatter object detailing how the logs are formatted
    """

    def __init__(self, level: str = "DEBUG"):
        """Created the logger and configure the basic elements of this logger

        Create the logger object with the proper logging level and log
        messages format

        Args:
            level: str for the logging level
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)
        self.formatter = logging.Formatter(
            "[%(asctime)s | %(levelname)s] %(message)s")
        self.formatter.datefmt = "%Y-%m-%d %H:%M:%S %Z"

    def log_to_file(self, filename: str = "semfio_mist.log"):
        """Create a file handler to allow us to log messages to a log file

        Args:
            filename: str containing the output log file (DEFAULT = "semfio_mist.log")
        """
        file_handler = logging.FileHandler("semfio_mist.log")
        file_handler.setFormatter(self.formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def log_to_console(self):
        """Create a stream handler to allow us to log messages to the console (stdout)"""
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(stream_handler)

    def dict_pretty_print(self, dict) -> str:
        """Print the content of a dict on multiple lines - Easier to ready

        Args:
            dict: The dict that we want to Print

        Returns:
            str: The multi-line string to print using the logger
        """
        return (json.dumps(dict, indent=4))


# Creating the logging engine
logger_engine = Logger_Engine("INFO")
# Enabling logging to a file
logger_engine.log_to_file()
# Enabling logging to the console
logger_engine.log_to_console()

# Creating the logger to be used elsewhere
logger = logger_engine.logger
