#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley6514.py: Driver for the Keithley 6514 electrometer.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import time
from flufl.enum import Enum, IntEnum
import struct

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Electrometer
from instruments.util_fns import assume_units, ProxyList, bool_property, enum_property

## CLASSES #####################################################################

class Keithley6514(SCPIInstrument, Electrometer):
    """
    The Keithley 6514 is an electrometer capable of doing sensitive current, 
    charge, voltage and resistance measurements.
    
    Example usage:
    
    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley6514.open_gpibusb('/dev/ttyUSB0', 12)
    
    .. _Keithley 6514 user's guide: http://www.tunl.duke.edu/documents/public/electronics/Keithley/keithley-6514-electrometer-manual.pdf
    """

    ## CONSTANTS ##

    _MODE_UNITS = {
        Mode.voltage: pq.volt,
        Mode.current: pq.amp,
        Mode.resistance: pq.ohm,
        Mode.charge: pq.coulomb
    }

    ## ENUMS ##
    
    class Mode(Enum):
        voltage = 'VOLT'
        current = 'CURR'
        resistance = 'RES'
        charge = 'CHAR'
       
    class TriggerMode(Enum):
        immediate = 'IMM'
        tlink = 'TLINK'

    class ArmSource(Enum):
        immediate = 'IMM'
        timer = 'TIM'
        bus = 'BUS'
        tlink = 'TLIN'
        stest = 'STES'
        pstest = 'PST'
        nstest = 'NST'
        manual = 'MAN'
        
    class ValidRange(Enum):
        voltage = (2, 20, 200)
        current = (20e-12, 200e-12, 2e-9, 20e-9, 200e-9, 2e-6, 20e-6, 200e-6, 2e-3,20e-3)
        resistance = (2e3, 20e3, 200e3, 2e6, 20e6, 200e6, 2e9, 20e9, 200e9)
        charge = (20e-9, 200e-9, 2e-6, 20e-6)

    ## PRIVATE METHODS ##    
    
    def _get_auto_range(self, mode):
        out = self.query('{}:RANGE:AUTO?'.format(mode.value))
        return out.strip() == 'ON'
    def _set_auto_range(self, mode, value):
        val = value.rescale(self._MODE_UNITS[mode]).item()
        if val not in self._valid_range(mode):
            raise ValueError('Unexpected range limit for current mode.')
        self.sendcmd('{}:RANGE AUTO {}'.format(mode.value, 'ON' if value else 'OFF')

    def _get_range(self, mode):
        self.query('{}:RANGE:UPPER?'.format(mode.value))
    def _set_range(self, mode, value):
        val = value.rescale(self._MODE_UNITS[mode]).item()
        
        self.sendcmd('{}:RANGE:LOWER {:e}'.format(mode.value, val)

    def _valid_range(mode):
        if mode == Mode.voltage:
            vrange = ValidRange.voltage
        elif mode == Mode.current:
            vrange = ValidRange.current
        elif mode == Mode.resistance:
            vrange = ValidRange.resistance
        elif mode == Mode.charge:
            vrange = ValidRange.charge
        else:
            raise ValueError('Invalid mode.')
        return vrange
    
    ## PROPERTIES ##  

    mode = enum_property('FUNCTION', 
        self.TriggerMode, 
        'Gets/sets the measurement mode of the Keithley 6514.'
    )

    trigger_mode = enum_property('TRIGGER:SOURCE', 
        self.Mode, 
        'Gets/sets the trigger mode of the Keithley 6514.'
    )

    trigger_mode = enum_property('ARM:SOURCE', 
        self.ArmSource, 
        'Gets/sets the arm source of the Keithley 6514.'
    )

    zero_check = bool_property('SYST:ZCH', 
        'ON', 'OFF',
        'Gets/sets the zero checking status of the Keithley 6514.'
    )
    zero_correct = bool_property('SYST:ZCOR', 
        'ON', 'OFF',
        'Gets/sets the zero correcting status of the Keithley 6514.'
    )

    @property
    def unit(self):
        return self._MODE_UNITS(self.mode)
  
    @property
    def auto_range(self):
        """
        Gets/sets the auto_range setting
               
        :type: `Keithley6514.TriggerMode`
        """
        return self._get_auto_range(self.mode)
    @trigger_mode.setter
    def auto_range(self, newval):
        self._set_auto_range(self.mode, newval)

    @property
    def input_range(self):
        """
        Gets/sets the auto_range setting
               
        :type: `Keithley6514.TriggerMode`
        """
        return self._get_range(self.mode)
    @trigger_mode.setter
    def auto_range(self, newval):
        self._set_range(self.mode, newval)
        
        
    ## METHODS ##

    def auto_config(self, mode):
        '''
        This command causes the device to do the following:
            - Switch to the specified mode
            - Reset all related controls to default values
            - Set trigger and arm to the 'immediate' setting
            - Set arm and trigger counts to 1
            - Set trigger delays to 0
            - Place unit in idle state
            - Disable all math calculations
            - Disable buffer operation
            - Enable autozero
        '''
        self.send_cmd('CONF:{}'.format(mode.value))
    
    def fetch(self):
        '''
        Request the latest post-processed readings using the current mode. 
        (So does not issue a trigger)
        '''
        return self.query('FETC?')


    def read(self):
        '''
        Trigger and acquire readings using the current mode.
        '''
        return self.query('READ?')

        


