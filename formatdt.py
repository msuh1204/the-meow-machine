import errors
import logging

from pytz import timezone
from datetime import datetime, timedelta

async def processDateTime(date, time, eventTz):
     try:
          utc = timezone("UTC")
          eventTimezone = timezone(eventTz)
          currentDateTime = utc.localize(datetime.utcnow()).astimezone(eventTimezone)
     except Exception as e:
          logging.info("Unable to retrieve current date: {}".format(e))
          raise ValueError
     if date.lower() == "today":
          logging.info("Current date in local time: {}".format(currentDateTime))
          year = currentDateTime.date().year
          month = currentDateTime.date().month
          day = currentDateTime.date().day
     elif date.lower() == "tomorrow":
          logging.info("Current date in local time: {}".format(currentDateTime))
          year = (currentDateTime + timedelta(days = 1)).date().year
          month = (currentDateTime + timedelta(days = 1)).date().month
          day = (currentDateTime + timedelta(days = 1)).date().day
     else:
          try:
               year = int(date.split("/")[0])
               month = int(date.split("/")[1])
               day = int(date.split("/")[2])
          except:
               logging.info("Invalid date inputted: {}".format(date))
               raise ValueError
     if time[-2:].upper() == "AM":
          try:
               hours = int(time.split(":")[0])
               if hours == 12:
                    hours = 0
               if hours > 12 or hours < 0:
                    raise ValueError
          except:
               logging.info("Invalid time hour value inputted: {}".format(time.split(":")[0]))
               raise ValueError
     elif time[-2:].upper() == "PM":
          try:
               hours = int(time.split(":")[0])
               if hours < 12:
                    hours = hours + 12
               if hours > 23 or hours < 12:
                    raise ValueError
          except:
               logging.info("Invalid time hour value inputted: {}".format(time.split(":")[0]))
               raise ValueError
     else:
          logging.info("Invalid meridian inputted: {}".format(time[-2:]))
          raise ValueError
     try:
          minutes = time.split(":")[1][0:2]
          minutes = int(minutes)
          if minutes < 0 or minutes > 59:
               raise ValueError
     except:
          logging.info("Invalid time minute value inputted: {}".format(time.split(":")[0]))
          raise ValueError
     try:
          return eventTimezone.localize(datetime(year, month, day, hours, minutes))
     except:
          logging.info("Invalid numerical values for year: {}, month: {}, day: {}, hours: {}, or minutes: {} inputted".format(year, month, day, hours, minutes))
          raise ValueError

async def humanFormatEventDateTime(eventDatetime, eventTimezone):
     eventTimezone = timezone(eventTimezone)
     localizedTime = eventDatetime.astimezone(eventTimezone)
     eventYear = localizedTime.date().year
     eventMonth = localizedTime.date().month
     eventDay = localizedTime.date().day
     eventHour = localizedTime.hour
     eventMeridian = ""
     if eventHour < 12:
          eventMeridian = "AM"
          if eventHour == 0:
               eventHour = 12
     else:
          if eventHour > 12:
               eventHour = eventHour - 12
          eventMeridian = "PM"
     eventMinute = localizedTime.minute
     if eventMinute < 10:
          eventMinute = "0{}".format(eventMinute)
     return (eventYear, eventMonth, eventDay, eventHour, eventMinute, eventMeridian)

async def ensureValidTime(eventTz, eventDateTime):
     utc = timezone("UTC")
     eventTimeZone = timezone(eventTz)
     currentDateTime = utc.localize(datetime.utcnow()).astimezone(eventTimeZone)
     logging.info("Current date and time: {}".format(currentDateTime))
     logging.info("Inserted event datetime: {}".format(eventDateTime))
     if currentDateTime > eventDateTime:
          raise errors.EventTooEarlyError

async def testTimezone(inputtedTimezone):
     try:
          timezone(inputtedTimezone)
     except Exception as e:
          logging.info("Error with user timezone: {}".format(e))
          raise errors.InvalidTimeZoneError

def getDatetime(event):
     return event[1]