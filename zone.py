#!/usr/bin/env python
#
# Decoder for Texecom Connect API/Protocol
#
# Copyright (C) 2018 Joseph Heenan
# Updates Jul 2020 Charly Anderson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time


class Zone:
    """Information about a zone and it's current state"""

    ZONETYPE_UNUSED = 0

    def __init__(self, zone_number):
        self.number = zone_number
        self.text = "Zone{:d}".format(self.number)
        self.state = None
        self.state_text = None
        self.zoneType = self.ZONETYPE_UNUSED
        self.zoneType_text = "unknown"
        self.areas = {}
        self.__active = False
        self.active_func = None
        self.active_since = None
        self.last_active = None
        self.__smoothed_active = False
        self.smoothed_active_delay = (
            30  # how long 'smoothed_active' will stay after last activation
        )
        self.smoothed_active_func = None
        self.smoothed_active_since = None
        self.smoothed_last_active = None
        self.area_event_func = None
        self.zone_event_func = None
        self.alive_event_func = None

    def update(self):
        if self.smoothed_active and not self.active:
            time_since_last_active = time.time() - self.last_active
            if time_since_last_active > self.smoothed_active_delay:
                self.smoothed_active = False
        if self.smoothed_active and self.smoothed_active_func is not None:
            # Run the handler on every update whilst 'smoothed active' is true
            self.smoothed_active_func(self, True, True)
        if self.active and self.active_func is not None:
            self.active_func(self, True, True)

    @property
    def smoothed_active(self):
        return self.__smoothed_active

    @smoothed_active.setter
    def smoothed_active(self, smoothed_active):
        if smoothed_active == self.__smoothed_active:
            return
        if self.smoothed_active_func is not None:
            self.smoothed_active_func(self, self.__smoothed_active, smoothed_active)
        self.__smoothed_active = smoothed_active
        if smoothed_active:
            self.smoothed_active_since = time.time()
        else:
            self.smoothed_active_since = None
            self.smoothed_last_active = time.time()

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, active):
        if active == self.__active:
            return
        if self.active_func is not None:
            self.active_func(self, self.__active, active)
        self.__active = active
        if active:
            self.active_since = time.time()
            self.smoothed_active = True
        else:
            self.last_active = time.time()
            self.active_since = None

    def save_state(self, zone_bitmap):
        self.state = zone_bitmap
        if (self.state & 0x3) == 1:
            self.active = True
        else:
            self.active = False
        zone_str = ["secure", "active", "tamper", "short"][self.state & 0x3]
        if self.state & (1 << 2):
            zone_str += ", fault"
        if self.state & (1 << 3):
            zone_str += ", failed test"
        if self.state & (1 << 4):
            zone_str += ", alarmed"
            self.armed = True
        else:
            self.armed = False
        if self.state & (1 << 5):
            zone_str += ", manual bypassed"
        if self.state & (1 << 6):
            zone_str += ", auto bypassed"
        if self.state & (1 << 7):
            zone_str += ", zone masked"
        self.state_text = zone_str
