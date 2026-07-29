from vireo.servo_voice_control import ServoCommand, parse_number, parse_servo_command


def test_parse_number_from_digits_and_words():
    assert parse_number("move 45 left") == 45
    assert parse_number("move thirty right") == 30
    assert parse_number("move nowhere") is None


def test_direction_corrections_match_prototype_vocabulary():
    assert parse_servo_command("thirty riot") == ServoCommand("relative", -30.0)
    assert parse_servo_command("twenty laugh") == ServoCommand("relative", 20.0)


def test_absolute_centre_and_exit_commands():
    assert parse_servo_command("center") == ServoCommand("centre")
    assert parse_servo_command("120") == ServoCommand("absolute", 120.0)
    assert parse_servo_command("please stop") == ServoCommand("exit")
