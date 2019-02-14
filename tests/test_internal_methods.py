from hourparser import check_morning_night, create_intervals, get_weekday_nums, parse_hour_min, process_line


def test_check_morning_night():
    assert check_morning_night([12, "pm"], [12, "am"]) == (True, False)
    assert check_morning_night([12, "pm"], [12, "pm"]) == (True, True)
    assert check_morning_night([12, "am"], [12, "am"]) == (False, False)
    assert check_morning_night([12, "am"], [12, "pm"]) == (False, True)
    assert check_morning_night([5, "pm"], [12, "am"]) == (True, False)
    assert check_morning_night([12, "am"], [5, "pm"]) == (False, True)
    assert check_morning_night([5, "pm"], [7, "pm"]) == (True, True)
    assert check_morning_night([5, "am"], [7, "am"]) == (False, False)


def test_create_intervals():
    assert create_intervals("Store 26", "Mon-Sun", "11 am - 4 am") == \
           [[26, 'Store 26', 0, '11:00', '24:00'],
            [26, 'Store 26', 1, '00:00', '04:00'],
            [26, 'Store 26', 1, '11:00', '24:00'],
            [26, 'Store 26', 2, '00:00', '04:00'],
            [26, 'Store 26', 2, '11:00', '24:00'],
            [26, 'Store 26', 3, '00:00', '04:00'],
            [26, 'Store 26', 3, '11:00', '24:00'],
            [26, 'Store 26', 4, '00:00', '04:00'],
            [26, 'Store 26', 4, '11:00', '24:00'],
            [26, 'Store 26', 5, '00:00', '04:00'],
            [26, 'Store 26', 5, '11:00', '24:00'],
            [26, 'Store 26', 6, '00:00', '04:00'],
            [26, 'Store 26', 6, '11:00', '24:00'],
            [26, 'Store 26', 0, '00:00', '04:00']]
    assert len(create_intervals("Store 41", "Mon-Sun", "11 am - 1 am")) == 14

    assert create_intervals("Store 49", "Fri", "11 am - 11 pm") == \
           [[49, 'Store 49', 4, '11:00', '23:00']]


def test_get_weekday_nums():
    assert get_weekday_nums(["Mon-Thu", "SUN"]) == [0, 1, 2, 3, 6]
    assert get_weekday_nums(["SUN"]) == [6]
    assert get_weekday_nums(["THU-TUE"]) == [0, 1, 3, 4, 5, 6]


def test_parse_hour_min():
    assert parse_hour_min("11:30 am - 9 pm") == (690, 1260)
    assert parse_hour_min("11:30 pm - 1 am") == (1410, 60)
    assert parse_hour_min("2 pm - 5 pm") == (840, 1020)
    assert parse_hour_min("2 am - 5 am") == (120, 300)


def test_process_line():
    assert process_line('"Store 1","Mon-Sun 11:30 am - 9 pm"')[0] == \
           [1, '"Store 1"', 0, '11:30', '21:00']
    assert process_line('"Store 6","Mon-Thu 11 am - 11 pm  / Fri-Sat 11 am - 12:30 am  / Sun 10 am - 11 pm"')[0] == \
           [6, '"Store 6"', 0, '11:00', '23:00']
    assert process_line('"Store 6","Mon-Thu 11 am - 11 pm  / Fri-Sat 11 am - 12:30 am  / Sun 10 am - 11 pm"')[-1] == \
           [6, '"Store 6"', 6, '10:00', '23:00']
    assert process_line('"Store 26","Mon-Sun 11 am - 4 am"')[0] == \
           [26, '"Store 26"', 0, '11:00', '24:00']
    assert process_line('"Store 26","Mon-Sun 11 am - 4 am"')[-1] == \
           [26, '"Store 26"', 0, '00:00', '04:00']
