#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import datetime
import logging
import os
import pprint
import sqlite3
import time

from gt import database_utils
from gt import tracker
from gt import team

logger = logging.getLogger(__name__)

DB_PATH = 'gt.db'

def bootstrap_db(db):
    """Creates a database to store events."""
    db.execute("""CREATE TABLE events (timestamp, event_type, player)""")
    db.execute("""CREATE TABLE team_info (number UNIQUE, name)""")


def new_game(tk, starters):
    logging.info('starters: %s', starters)
    tk.set_starters(starters)


def main():
    """ This bot may raise exception. Suggest to run the bot by the command:
    while true; do trade_jbot ; sleep 3; done

    When there is exception, the bot will post message to slack.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true')
    subparsers = parser.add_subparsers(dest="command", help='sub-command help')

    parser_new = subparsers.add_parser(
      'new', help='Add a new game with starting lineup')
    parser_new.add_argument('starters', nargs=5, type=int, metavar="ID",
                            help='Create a game with starting lineup')

    parser_new = subparsers.add_parser(
      'load_team', help='Loads a CSV file for team members.')
    parser_new.add_argument('csv_file', type=str, metavar="FILE",
                            help='Loads a CSV file for team members.\n'
                                 'The fields are number and name.\n'
                                 'Check the example in data/team.csv')

    parser_start = subparsers.add_parser(
      'start', help='Start or resume the game')

    parser_stop = subparsers.add_parser(
      'stop', help='Stop or pause the game')

    parser_replace = subparsers.add_parser(
      'replace', help='Replace players')

    parser_replace.add_argument('down', type=int, metavar="out_ID",
                                help='The player to check out')
    parser_replace.add_argument('up', type=int, metavar="in_ID",
                                help='The player to check in')

    parser_reset = subparsers.add_parser(
      'reset', help='Clear the game')

    parser_show = subparsers.add_parser(
      'show', help='Show status')

    args = parser.parse_args()

    FORMAT = '%(asctime)-15s %(levelname)-10s %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    else:
        logging.basicConfig(level=logging.INFO, format=FORMAT)

    db = None
    db_path = DB_PATH
    # Connect to a database.
    # Create a new db and create table.
    if not os.path.exists(db_path):
        db = database_utils.DatabaseManager(db_path)
        bootstrap_db(db)
    else:
        db = database_utils.DatabaseManager(db_path)

    team_info = team.load_team_from_db(db)
    tk = tracker.Tracker(db, team_info)

    if args.command == 'new':
        new_game(tk, args.starters)

    if args.command == 'start':
        tk.start()

    if args.command == 'stop':
        tk.stop()

    if args.command == 'replace':
        logger.debug('replace %s with %s', args.down, args.up)
        tk.replace(args.down, args.up)

    if args.command == 'reset':
        logger.debug('Reset the game')
        tk.reset()
        team.reset(db)

    if args.command == 'load_team':
        team.load_team_from_csv(db, args.csv_file)

    if args.command == 'show':
        tk.show()

if __name__ == '__main__':
    main()
