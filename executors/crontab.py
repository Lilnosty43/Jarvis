import os
import subprocess
from typing import NoReturn

from modules.logger import config

LOG_FILE = os.path.join('logs', 'cron_%d-%m-%Y.log')


def crontab_executor(statement: str) -> NoReturn:
    """Executes a cron statement.

    Args:
        statement: Cron statement to be executed.
    """
    filename = config.multiprocessing_logger(filename=LOG_FILE)
    with open(filename, 'a') as file:
        file.write('\n')
        try:
            subprocess.call(statement, shell=True, stdout=file, stderr=file)
        except (subprocess.CalledProcessError, subprocess.SubprocessError, Exception) as error:
            file.write(error)
