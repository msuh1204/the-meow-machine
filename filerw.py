import logging
import errors

from datetime import datetime, timedelta
from setup import connection, cursor
from psycopg2 import sql

logging.basicConfig(filename='console.log', filemode='w', level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

async def setTime(tz):
     command = sql.SQL('''SET TIMEZONE TO {timezone};''').format(
               timezone = sql.Identifier(tz))
     cursor.execute(command)

async def retrieveCurrentTime():
     command = sql.SQL("SELECT LOCALTIMESTAMP")
     cursor.execute(command)
     return cursor.fetchone()

async def retrieveFirstEntry(database, key, columns):
     try:
          cursor.execute(
               sql.SQL('SELECT {columns} FROM {table} ORDER BY {orderKey};').format(
                    columns = sql.SQL(', ').join(
                         sql.Identifier(database, column) for column in columns    
                    ), 
                    table = sql.Identifier(database), 
                    orderKey = sql.Identifier(database, key)))
          return cursor.fetchone()
     except Exception as e:
          logging.info("Error with retrieving first entry: {}".format(e))

async def retrieveAllEntries(database):
     try:
          cursor.execute(
               sql.SQL("SELECT * FROM {table}").format(
                    table = sql.Identifier(database)))
          return cursor.fetchall()
     except Exception as e:
          logging.info("Error with retrieving entries: {}".format(e))

async def findEntries(database, searchTerms, columns):
     try:
          command = sql.SQL(
               '''
                    SELECT {columns} 
                    FROM {table} 
                    WHERE {conditions}
               ''').format(
                    columns = sql.SQL(', ').join(
                         sql.Identifier(database, column) for column in columns    
                    ),
                    table = sql.Identifier(database),
                    conditions = sql.SQL(' AND ').join(
                         sql.Composed([sql.Identifier(database, key), sql.SQL(" = "), sql.Placeholder()]) for key in searchTerms.keys()
                    )
               )
          cursor.execute(command, list(searchTerms.values()))
          return cursor.fetchall()
     except Exception as e:
          logging.info("Error with retrieving entries with matching keys: {}".format(e))

async def insertEntry(database, entry):
     command = sql.SQL(
          '''
               INSERT INTO {table}
               VALUES ({values});
          ''').format(
               table = sql.Identifier(database),
               values = sql.SQL(",").join(
                    sql.Placeholder() for item in entry
               ))
     cursor.execute(command, entry)
     connection.commit()

async def insertEvent(entry):
     try:
          await setTime(entry[4])
     except Exception as e:
          logging.info("Error with setting time zone: {}".format(e))
     else:
          try:
               matches = await findEntries("events", {"name" : entry[0], "channel" : entry[2], "datetime" : entry[3]}, ["name", "channel", "datetime"])
               if len(matches) != 0:
                    raise errors.RepetitionError
          except errors.RepetitionError:
               logging.info("Entry already exists")
               raise errors.RepetitionError
          except Exception as e:
               logging.info("Error with retrieving matching entries: {}".format(e)) 
          else:
               try:
                    await insertEntry("events", entry)
               except Exception as e:
                    logging.info("Error with inserting data: {}".format(e))

async def insertMultipleEvents(entriesList):
     try:
          await setTime(entriesList[0][4])
     except Exception as e:
          logging.info("Error with setting time zone: {}".format(e))
     else:
          try:
               for entry in entriesList:
                    matches = await findEntries("events", {"name" : entry[0], "channel" : entry[2], "datetime" : entry[3]}, ["name"])
                    if len(matches) != 0:
                         raise errors.RepetitionError
          except errors.RepetitionError:
               logging.info("Entry or entries already exist(s)")
               raise errors.RepetitionError
          else:
               try:
                    await insertEntry("events", entriesList)
               except Exception as e:
                    logging.info("Error with inserting data: {}".format(e))

async def deleteEntry(database, params):
     try:
          cursor.execute(
               sql.SQL("DELETE FROM {table} WHERE {column};").format(
                    table = sql.Identifier(database),
                    column = sql.SQL(' AND ').join(
                         sql.Composed([sql.Identifier(database, key), sql.SQL(" = "), sql.Placeholder()]) for key in params.keys()
                    )), list(params.values()))
          connection.commit()
     except Exception as e:
          logging.info("Error with deleting data: {}".format(e))

async def updateEntry(database, updates, conditions):
     command = sql.SQL(
          '''
               UPDATE {table}
               SET {updateValues}
               WHERE {updateConditions}
          ''').format(
               table = sql.Identifier(database),
               updateValues = sql.SQL(',').join(
                    sql.Composed([sql.Identifier(key), sql.SQL(" = "), sql.Placeholder()]) for key in updates.keys()
               ),
               updateConditions = sql.SQL(' AND ').join(
                    sql.Composed([sql.Identifier(key), sql.SQL(" = "), sql.Placeholder()]) for key in conditions.keys()
               )
          )
     try:
          cursor.execute(command, list(updates.values()) + list(conditions.values()))
          connection.commit()
     except Exception as e:
          logging.info("Error with updating data: {}".format(e))

