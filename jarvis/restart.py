# noinspection PyUnresolvedReferences
"""This is a basic query to start Jarvis after 5 seconds triggered by the ``restart()`` function in main module.

>>> Restart

"""

import os
import time
import inspect

time.sleep(5)
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
source_dir = os.path.dirname(os.path.dirname(current_dir)) + os.path.sep
os.system(f'python3 {source_dir}jarvis.py')
