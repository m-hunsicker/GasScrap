#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 15:17:36 2018

@author: mitch
"""
#Import databae utils
import sqlite3
import os
import pandas as pd
from datetime import date

from common import log_print

FILE_PATH = os.path.dirname(os.path.realpath(__file__))

DB_FILE = os.path.join(FILE_PATH, 'Data', 'cotation.db')
QT = "QUOTES" #Name of quote table


def init_database():
    """
    Init database
    """
    log_print("DB initalization phase started")
    connection = sqlite3.connect(DB_FILE)
    # Table creations
    connection.executescript(f"DROP TABLE IF EXISTS {QT}")
    connection.commit()
    connection.executescript(f"CREATE TABLE {QT} ('Trading_day' TEXT NOT NULL,"+\
                                                  "'Gas_index' TEXT NOT NULL," +\
                                                  "'Season+1' FLOAT," +\
                                                  "'Season+2' float,"+\
                                                  "'Season+3' float,"+\
                                                  "'Season+4' float,"+\
                                                  "'Calendar+1' float,"+\
                                                  "'Calendar+2' float,"+\
                                                  "'Calendar+3' float,"+\
                                                  "'Calendar+4' float,"+\
                                                  "PRIMARY KEY ('TRADING_DAY', 'Gas_index'))")
    connection.commit()
    connection.close()
    log_print("DB initialized !")



def insert_data(data):
    """
    Import data
    """
    with sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES|\
                         sqlite3.PARSE_COLNAMES) as connection:
        #Prepare dataType elements.
        connection.execute(f"INSERT OR IGNORE INTO {QT} VALUES(\'"+ data['trading_day'] +"\',"+\
                                                    f"\'{data['Gas_index']}\',"+\
                                                    f"{data['Season+1']},"+\
                                                    f"{data['Season+2']},"+\
                                                    f"{data['Season+3']},"+\
                                                    f"{data['Season+4']},"+\
                                                    f"{data['Calendar+1']},"+\
                                                    f"{data['Calendar+2']},"+\
                                                    f"{data['Calendar+3']},"+\
                                                    f"{data['Calendar+4']})")
    connection.commit()
    connection.close()

def get_data(index_list):
    """
    Return the entire database in the form of a cleaned panda dataframe
    """
    with sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES|\
                         sqlite3.PARSE_COLNAMES) as connection:

        data_frame = pd.read_sql_query(f"select * from QUOTES WHERE Gas_index in"+\
                                       f"({','.join('?'*len(index_list))})",
                                       connection,
                                       params=[str(e) for e in index_list.keys()],
                                       parse_dates=['Trading_day'])
        log_print("Data extracted from database")
        return data_frame

def get_last_date():
    """
    Get the last Trading_day date inserted
    """
    with sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES|\
                         sqlite3.PARSE_COLNAMES) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(Trading_Day) from QUOTES")
        buffer = cursor.fetchone()[0]
        buffer = buffer.split('-')
        return date(int(buffer[0]), int(buffer[1]), int(buffer[2]))

if __name__ == "__main__":
    #init_database()
    pass
