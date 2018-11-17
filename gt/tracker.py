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

logger = logging.getLogger(__name__)


class EVENT():
    CHECK_IN = 'check_in'
    CHECK_OUT = 'check_out'
    START = 'start'
    STOP = 'stop'

class TrackerError(Exception):
    pass


class Tracker(object):
    INSERT_STR = 'INSERT INTO events VALUES (?,?,?)'
    NULL_PLAYER = -1
    def __init__(self, db, team_info):
        self._db = db
        self._on_court_players = None
        self._players = None
        self._time_events = None
        self._on_court_results = []
        self._off_court_results = []
        self._is_running = False
        self._team_info = team_info

    def _has_event(self):
        c = self._db.execute('SELECT * FROM events')
        ret = c.fetchall()
        return len(ret)

    def set_starters(self, starters):
        if self._has_event():
            logger.exception('Reset the game first.')
            raise TrackerError

        timestamp = time.time()
        event_type = EVENT.CHECK_IN
        for player in starters:
            self._db.execute(self.INSERT_STR,
                             (timestamp, event_type, player))

    def start(self):
        self._time_events = self._get_time_events()
        if self._time_events and self._time_events[-1][1] == EVENT.START:
            logger.exception('Should not call start twice')
            raise TrackerError

        timestamp = time.time()
        event_type = EVENT.START
        self._db.execute(self.INSERT_STR,
                         (timestamp, event_type, self.NULL_PLAYER))

        self.show()

    def stop(self):
        self._time_events = self._get_time_events()
        if self._time_events and self._time_events[-1][1] == EVENT.STOP:
            logger.exception('Should not call stop twice')
            raise TrackerError

        timestamp = time.time()
        event_type = EVENT.STOP
        self._db.execute(self.INSERT_STR,
                         (timestamp, event_type, self.NULL_PLAYER))

        self.show()

    def _get_players(self):
        c = self._db.execute('SELECT DISTINCT player FROM events WHERE event_type = (?)',
                             (EVENT.CHECK_IN,))
        ret = c.fetchall()
        # Get value from tuple.
        ret = [x[0] for x in ret]

        logger.debug('Players: %s', ret)

        return ret

    def _get_time_events(self):
        c = self._db.execute('SELECT timestamp, event_type FROM events WHERE event_type = :e1 OR event_type = :e2',
                            {'e1': EVENT.START, 'e2': EVENT.STOP})
        ret = c.fetchall()

        logger.debug('Time events: %s', ret)

        return ret

    def _check_in(self, player, timestamp):
        logger.debug('%s Player %d check in', timestamp, player)
        event_type = EVENT.CHECK_IN
        self._db.execute(self.INSERT_STR,
                         (timestamp, event_type, player))

    def _check_out(self, player, timestamp):
        logger.debug('%s Player %d check out', timestamp, player)
        event_type = EVENT.CHECK_OUT
        self._db.execute(self.INSERT_STR,
                         (timestamp, event_type, player))

    def replace(self, down, up):
        # First we need to calculate to check who is on court.
        self.calculate()
        if down not in self._on_court_players:
            logger.exception('Player %d is not on the court', down)
            raise TrackerError

        if up in self._on_court_players:
            logger.exception('Player %d is already on the court', up)
            raise TrackerError

        timestamp = time.time()
        self._check_out(down, timestamp)
        self._check_in(up, timestamp)

        self.show()

    def calculate(self):
        self._players = self._get_players()
        self._time_events = self._get_time_events()

        if not self._players:
            logger.warning('Game is not created yet')
            return

        if not self._time_events:
            logger.warning('Game is not started yet')
            return

        if self._time_events and self._time_events[-1][1] != EVENT.STOP:
            self._is_running = True
            # Add a fake stop event so we can get latest on court time.
            self._time_events.append((time.time(), EVENT.STOP))

        # Find out who is on court in _calculate_player.
        self._on_court_players = set()
        self._on_court_results = []
        self._off_court_results = []

        for player in self._players:
            acu_time, latest_on_time, latest_off_time = self._calculate_player(player)

            if player in self._on_court_players:
                 res = (player, acu_time, latest_on_time)
                 self._on_court_results.append(res)

            else:
                 res = (player, acu_time, latest_off_time)
                 self._off_court_results.append(res)

    def reset(self):
        self._db.execute("""DELETE from events""")

    def show(self):
        self.calculate()

        print('=' * 60)
        print('Game is %s' % ('RUNNING' if self._is_running else 'PAUSED'))
        print('-' * 60)
        print('On the court:\n')
        for player, acu_time, latest_on_time in self._on_court_results:
            name = self._get_player_name(player)
            print('Player: %d %s\t\t total: %d\t playing for: %d' % (player, name, acu_time, latest_on_time))

        print('-' * 60)
        print('On the bench:\n')

        for player, acu_time, latest_off_time in self._off_court_results:
            name = self._get_player_name(player)
            print('Player: %d %s\t\t total: %d\t resting for: %d' % (player, name, acu_time, latest_off_time))

        print('=' * 60)

    def _get_player_name(self, player):
        """Tries to get player name by its number."""
        if player in self._team_info:
            return self._team_info[player]['name']
        return ''

    def _get_player_events(self, player):
        c = self._db.execute('SELECT timestamp, event_type FROM events WHERE player = (?)',
                            (player,))
        ret = c.fetchall()

        logger.debug('Player %d events: %s', player, ret)

        return ret

    def _is_on_court_players(self, player_events):
        return player_events[-1][1] == EVENT.CHECK_IN

    def _calculate_player(self, player):
        player_events = self._get_player_events(player)

        if self._is_on_court_players(player_events):
            self._on_court_players.add(player)

        mixed_events = player_events + self._time_events
        logger.debug('Mixed events: %s', mixed_events)
        # Sorted by timestamp.
        mixed_events.sort(key=lambda x: x[0])

        logger.debug('Mixed events: %s', mixed_events)

        current_check_in_time = None
        time_on_going = False
        on_court = False

        accumulated_on_time = 0
        latest_on_time = 0
        latest_off_time = None

        for ts, event_type in mixed_events:
            if event_type == EVENT.START:
                time_on_going = True
                # Player is on court.
                # Game is resumed.
                if on_court:
                    current_check_in_time = ts

            if event_type == EVENT.STOP:
                # TODO: raise?
                if not time_on_going:
                    logger.exception('Stop game without starting it. '
                                     'Player: %s, time %s', player, ts)
                    raise TrackerError

                if on_court:
                    if current_check_in_time is None:
                        logger.exception('Stop game without current check in time. '
                                         'Player: %s, time %s', player, ts)
                        raise TrackerError
                    latest_on_time = (ts - current_check_in_time)
                    accumulated_on_time += latest_on_time

                current_check_in_time = None
                time_on_going = False

            if event_type == EVENT.CHECK_IN:
                on_court = True
                if time_on_going:
                    current_check_in_time = ts
                else:
                    # Player check in, but game is in pause.
                    current_check_in_time = None

            if event_type == EVENT.CHECK_OUT:

                on_court = False

                if time_on_going:
                    if current_check_in_time is None:
                        logger.exception('Check out without current check in time. '
                                         'Player: %s, time %s', player, ts)
                        raise TrackerError
                    latest_on_time = (ts - current_check_in_time)
                    accumulated_on_time += latest_on_time

                current_check_in_time = None

                # Do the calculation using current time because the rest time is
                # for real.
                latest_off_time = time.time() - ts

        return accumulated_on_time, latest_on_time, latest_off_time
