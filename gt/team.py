#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import logging
import pprint

from gt import database_utils

logger = logging.getLogger(__name__)


def load_team_from_csv(db, csv_file):
    team_info = dict()
    with open(csv_file) as csvfile:
        rows = csv.DictReader(csvfile)
        for row in rows:
            number = int(row['number'])
            name = row['name']

            team_info[number] = dict(number=number, name=name)

            db.execute('INSERT INTO team_info VALUES (?,?)', (number, name))

    logger.debug('Team info:\n' + pprint.pformat(team_info))


def load_team_from_db(db):
    team_info = dict()
    c = db.execute('SELECT number, name FROM team_info')
    ret = c.fetchall()

    for number, name in ret:
        team_info[number] = dict(number=number, name=name)

    logger.debug('Team info:\n' + pprint.pformat(team_info))

    return team_info


def reset(db):
    db.execute("""DELETE from team_info""")
