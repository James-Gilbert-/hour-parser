"""Module for processing text files of store hours."""

import datetime
import re

import pandas as pd
import sqlalchemy
from sqlalchemy.sql import text


def check_morning_night(time_start=None, time_end=None):
    """
    Returns a boolean pair corresponding to whether a store opens at night or closes at night.

    Example format expected:
        [HH,am] (or pm)
        [HH:MM,am] (or pm)
    """

    open_night = (time_start[-1].upper() == "PM")
    close_night = (time_end[-1].upper() == "PM")
    return open_night, close_night


def get_weekday_nums(days=None):
    """
    Returns a list of enumerated days on which the interval is active. Monday is indexed at 0.

    Example format expected:
        [Mon-Thu, Sun]
    """

    days_ = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    day_map = {day: idx for idx, day in enumerate(days_)}
    day_set = {0, 1, 2, 3, 4, 5, 6}
    day_cover = []
    for item in days:
        item = item.split("-")
        try:
            days = [day_map[x.upper()] for x in item]
            if days[0] < days[1]:
                day_set = [day for day in range(days[0], days[1] + 1)]
                day_cover.extend(day_set)
            # later day in the week is listed first
            elif days[0] > days[1]:
                exclude_days = set(range(days[1] + 1, days[0]))
                day_cover.extend(list(day_set - exclude_days))
            else:
                day_cover.extend([days[0]])
        except IndexError:
            day_cover.extend([day_map[item[0].upper()]])
    return list(set(day_cover))


def parse_hour_min(time=None):
    """Parses the open-close range given as HH:MM(am/pm) - HH:MM(am/pm)."""

    time_range = time.split("-")
    time_start, time_end = [x.split() for x in time_range]
    open_night, close_night = check_morning_night(time_start, time_end)
    start_split = time_start[0].split(":")
    end_split = time_end[0].split(":")

    # The time either has minutes or no minutes
    try:
        open_hrs, open_mins = map(int, start_split)
    except ValueError:
        open_hrs, open_mins = start_split[0], 0
    try:
        close_hrs, close_mins = map(int, end_split)
    except ValueError:
        close_hrs = end_split[0]
        close_mins = 0

    open_time = (int(open_hrs) % 12 + 12 * open_night) * 60 + open_mins
    close_time = (int(close_hrs) % 12 + 12 * close_night) * 60 + close_mins

    return open_time, close_time


def create_intervals(store_id=None, day_text=None, time=None):
    """
    Returns a list of database rows for an interval.

    Computes the intervals during which a store is considered open.
    The times are converted into 24 hour format.

    Formatting and input expectations:
    There will always be an AM/PM value after each time
    Time will always be given in ranges (time1 - time2)

    """

    # For simplification, the id of the store is taken from the store_name.
    int_id = int(re.findall(r'\d+', store_id)[0])
    days = ["".join(x.split()) for x in day_text.split()]

    day_nums = get_weekday_nums(days)
    records = []
    open_time, close_time = parse_hour_min(time)

    # Same day open/close
    if open_time <= close_time:
        o_time, c_time = datetime.time(
            hour=open_time // 60, minute=open_time % 60), datetime.time(
            hour=close_time // 60, minute=close_time % 60)

        for day in day_nums:
            records.append([int_id, store_id, day, o_time.strftime(
                "%H:%M"), c_time.strftime("%H:%M")])

    # Closing of store extends to subsequent day
    else:
        o_time, c_time = datetime.time(
            hour=open_time // 60, minute=open_time %
                                         60).strftime("%H:%M"), "24:00"
        # New record created for subsequent day
        next_start = datetime.time(hour=0, minute=0).strftime("%H:%M")
        next_end = datetime.time(
            hour=close_time // 60,
            minute=close_time %
                   60).strftime("%H:%M")

        for day in day_nums:
            records.append([int_id, store_id, day, o_time, c_time])
            # Day is taken modulus 7 in case of week overflow
            records.append([int_id, store_id, (day + 1) %
                            7, next_start, next_end])
    return records


def process_line(line=None):
    """Returns records for a line of information in the log."""

    line = line.split(",")
    store_id, times = line[0], line[1:]
    # Split a record by separators denoting open/closing intervals
    times = re.split(r'["\/|,]+', ''.join(times))
    unproc_times = list(filter(None, times))
    line_records = []
    for time in unproc_times:
        # Splits the store information into day(s) and hours
        days, hours = re.split(r'(^[^\d]+)', time)[1:]
        proc_times = create_intervals(store_id, days, hours)
        line_records.extend(proc_times)
    return line_records


def db_load_disk(
        tempfile="temp.txt",
        db_uri='mysql://root:root@localhost/simplerose'):
    """Loads temporary large file from disk directly into database."""

    engine = sqlalchemy.create_engine(db_uri, connect_args={"local_infile": 1})
    with engine.connect() as con:
        drop_table = "DROP TABLE IF EXISTS store_hours"
        create_table = "CREATE TABLE IF NOT EXISTS store_hours(store_id INT, name VARCHAR(128),weekday TINYINT,open TIME, close TIME)"
        create_index_name = "CREATE INDEX name_idx on store_hours(name)"
        create_index_id = "CREATE INDEX id_index on store_hours(store_id)"
        load_data = text("""
        LOAD DATA LOCAL INFILE :target
        INTO TABLE store_hours
        FIELDS TERMINATED BY ','
        LINES TERMINATED BY '\n'
        (store_id,name,weekday,open,close)""")
        con.execute(drop_table)
        con.execute(create_table)
        con.execute(create_index_name)
        con.execute(create_index_id)
        con.execute(load_data, target=tempfile)


def db_load_mem(
        proc_logs=None,
        table="store_hours",
        db_uri='mysql://root:root@localhost/simplerose'):
    """Loads processed logs into the table from memory."""

    engine = sqlalchemy.create_engine(db_uri)
    proc_logs.to_sql(table, engine, if_exists="append")


def process_file(
        filename="store_hours.txt",
        output="temp.txt",
        large_file=False,
        debug=False,
        db_uri='mysql://root:root@localhost/simplerose'):
    """Processes a text file containing store and store hours."""

    try:
        assert db_uri != ''
    except AssertionError:
        print("Must specify database URI")

    proc_logs = []

    with open(filename, 'r') as file:
        for line in file:
            proc_logs.extend(process_line(line.split("\n")[0]))

    if large_file:
        with open(output, 'w') as out:
            for record in proc_logs:
                cols = map(str, record)
                out.write("%s\n" % ','.join(cols))
        db_load_disk(output, db_uri)
    else:
        cols = ["store_id", "name", "weekday", "open", "close"]
        proc_logs = pd.DataFrame.from_records(proc_logs, columns=cols)
        if debug:
            print(proc_logs)
        db_load_mem(proc_logs, db_uri)
