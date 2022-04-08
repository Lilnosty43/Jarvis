import time
from multiprocessing import Process
from multiprocessing.context import TimeoutError as ThreadTimeoutError
from multiprocessing.pool import ThreadPool
from typing import NoReturn

import requests
from ics import Calendar

from executors.logger import logger
from modules.audio import speaker
from modules.database import database
from modules.models import models
from modules.utils import globals, support

env = models.env
fileio = models.fileio
db = database.Database(database=fileio.base_db)
db.create_table(table_name="ics", columns=["info"])


def meetings_writer() -> NoReturn:
    """Gets return value from ``meetings()`` and writes it to a file.

    This function runs in a dedicated process every hour to avoid wait time when meetings information is requested.
    """
    meeting_info = meetings_gatherer()
    support.await_commit()  # TODO: Create a condition here to re-create db connection if return value is False
    globals.database_is_free = False
    db.cursor.execute("INSERT OR REPLACE INTO ics (info) VALUES (?);", (meeting_info,))
    db.connection.commit()
    globals.database_is_free = True


def meetings_gatherer() -> str:
    """Gets ICS data and converts into a statement.

    Returns:
        str:
        - On success, returns a message saying which event is scheduled at what time.
        - If no events, returns a message saying there are no events today.
        - On failure, returns a message saying Jarvis was unable to read the calendar schedule.
    """
    if not env.ics_url:
        return f"I wasn't given a calendar URL to look up your meetings {env.title}!"
    response = requests.get(url=env.ics_url)
    if not response.ok:
        logger.error(response.status_code)
        return "I wasn't able to read your calendar schedule sir! Please check the shared URL."
    calendar = Calendar(response.text)
    events = list(calendar.timeline.today())
    if not events:
        logger.info("No meetings found!")
        return f"You don't have any meetings today {env.title}!"
    meeting_status, count = "", 0
    for index, event in enumerate(events):
        if event.end.timestamp < int(time.time()):  # Skips if meeting ended earlier than current time
            continue
        count += 1
        begin_local = event.begin.strftime("%I:%M %p")
        if len(events) == 1:
            meeting_status += f"You have an all day meeting {env.title}! {event.name}. " if event.all_day else \
                f"You have a meeting at {begin_local} {env.title}! {event.name}. "
        else:
            meeting_status += f"{event.name} - all day" if event.all_day else f"{event.name} at {begin_local}"
            meeting_status += ', ' if index + 1 < len(events) else '.'
    if count:
        plural = "meeting" if count == 1 else "meetings"
        meeting_status = f"You have {count} {plural} today {env.title}! {meeting_status}"
    else:
        meeting_status = f"You have no more meetings for rest of the day {env.title}! " \
                         f"However, you had {len(events)} meetings earlier today."
    return meeting_status


def meetings() -> NoReturn:
    """Controller for meetings."""
    if meeting_status := db.cursor.execute("SELECT info FROM ics").fetchone():
        speaker.speak(text=meeting_status[0])
    else:
        if globals.called_by_offline:
            Process(target=meetings_gatherer).start()
            speaker.speak(text=f"Meetings table is empty {env.title}. Please try again in a minute or two.")
            return False
        meeting = ThreadPool(processes=1).apply_async(func=meetings_gatherer)  # Runs parallely and awaits completion
        speaker.speak(text=f"Please give me a moment {env.title}! I'm working on it.", run=True)
        try:
            speaker.speak(text=meeting.get(timeout=60), run=True)
        except ThreadTimeoutError:
            logger.error("Unable to read the calendar schedule within 60 seconds.")
            speaker.speak(text=f"I wasn't able to read your calendar within the set time limit {env.title}!", run=True)
