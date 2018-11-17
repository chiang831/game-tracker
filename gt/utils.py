#!/usr/bin/env python
# -*- coding: utf-8 -*-

def seconds_to_mins_secs(secs):
    secs = int(secs)
    minutes = secs / 60
    secs = secs % 60
    return '%s m %s s' % (minutes, secs)
