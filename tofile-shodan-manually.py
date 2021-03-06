#!/usr/bin/env python3
from timetracker import TimeTracker
from base import get_user_boolean
from base import ask_output_file
from shodanfunctions import *
import sys
import os

os.chdir(sys.path[0])

# Script where user can enter Shodan queries manually in the command-line
should_convert = get_user_boolean('Also convert to es? y/n')
should_add_institutions = False
if should_convert:
    should_add_institutions = get_user_boolean("Should converter add the institution as a field?"
                                               " (requires 'INSTITUTIONS_FILE' in config.ini) y/n")
str_path_output_file = ask_output_file('outputfiles/shodan/')
queries = get_user_input_console_queries()
t = TimeTracker()
to_file_shodan(queries, str_path_output_file, should_convert, should_add_institutions)
t.print_statistics()
