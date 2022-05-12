"""Bare init file to source the module."""
import os
import sys
import inspect
import time

from modules.utils import support, display

echo = display.Echo()

sys.stdout.write("\rValidating pre-requisites.")

try:
    import psutil  # noqa
    import packaging.version  # noqa
    import pvporcupine  # noqa
    import speech_recognition  # noqa
    import playsound  # noqa
    import pyaudio  # noqa
    import cv2  # noqa
    import face_recognition  # noqa
    import git  # noqa
    import requests  # noqa
    import psutil  # noqa
    import bs4  # noqa
    import pychromecast  # noqa
    import dotenv  # noqa
    import PIL  # noqa
    import googlehomepush  # noqa
    import jinja2  # noqa
    import pydantic  # noqa
    import uvicorn  # noqa
    import gmailconnector  # noqa
    import multipart  # noqa
    import wolframalpha  # noqa
    import randfacts  # noqa
    import holidays  # noqa
    import speedtest  # noqa
    import inflect  # noqa
    import pyrh  # noqa
    import vpn  # noqa
    import certifi  # noqa
    import yaml  # noqa
    import randfacts  # noqa
    import pyicloud  # noqa
    import timezonefinder  # noqa
    import search_engine_parser  # noqa
    import pywebostv  # noqa
    import wordninja  # noqa
    import joke  # noqa
    import pyttsx3  # noqa
    import pytz  # noqa
    import newsapi  # noqa
    import wikipedia  # noqa
except ModuleNotFoundError as error:
    support.flush_screen()
    current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    echo.error(msg=error)
    echo.critical(msg="Missing modules. Run the following command:\n"
                      f"bash {os.path.join(current_dir, 'lib', 'install.sh')}", add_prefix=False)
    os._exit(1)  # noqa

support.flush_screen()
for i in range(1, 4):
    sys.stdout.write(f"\rInitiating Jarvis in {4 - i} second(s)")
    time.sleep(i)
support.flush_screen()
