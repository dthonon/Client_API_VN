#!/usr/bin/env python3
"""
Regulator for interval download, aiming at maintaining a constant size of data.
The setpoint is the number of sightings to be downloaded.
The controled variable is the time interval, in days.

Derived from https://github.com/m-lundberg/simple-pid

"""

import logging

from . import __version__

logger = logging.getLogger('transfer_vn.regulator')


class PID(object):
    """
    A simple PID controller. No fuss.
    """

    def __init__(self,
                 kp=1.0,
                 ki=0.0,
                 kd=0.0,
                 setpoint=0,
                 output_limits=(None, None)):
        """
        :param kp: The value for the proportional gain kp
        :param ki: The value for the integral gain ki
        :param kd: The value for the derivative gain kd
        :param setpoint: The initial setpoint that the PID will try to achieve
        :param output_limits: The initial output limits to use, given as an iterable with 2 elements, for example: (lower, upper). The output will never go below the lower limit or above the upper limit. Either of the limits can also be set to None to have no limit in that direction. Setting output limits also avoids integral windup, since the integral term will never be allowed to grow outside of the limits.
        """
        self.kp, self.ki, self.kd = kp, ki, kd
        self.setpoint = setpoint

        self._min_output, self._max_output = output_limits

        self._error_sum = 0

        self._last_output = None
        self._proportional = 0
        self._last_input = None

    @property
    def version(self):
        """Return version."""
        return __version__

    def _clamp(self, value, limits):
        lower, upper = limits
        if value is None:
            return None
        elif upper is not None and value > upper:
            return upper
        elif lower is not None and value < lower:
            return lower
        return value

    def __call__(self, input_):
        """
        Call the PID controller with *input_* and calculate and return a control output
        since the last update. If no new output is calculated, return the previous output instead (or None if no value
        has been calculated yet).
        """

        # compute error terms
        error = self.setpoint - input_
        self._error_sum += self.ki * error
        d_input = input_ - (self._last_input
                            if self._last_input is not None else input_)

        # compute the proportional term
        self._proportional = self.kp * error

        output = self._proportional + self._error_sum - self.kd * d_input
        output = self._clamp(output, self.output_limits)

        # keep track of state
        self._last_output = output
        self._last_input = input_

        return output

    @property
    def tunings(self):
        """The tunings used by the controller as a tuple: (kp, ki, kd)"""
        return self.kp, self.ki, self.kd

    @tunings.setter
    def tunings(self, tunings):
        """Setter for the PID tunings"""
        self.kp, self.ki, self.kd = tunings

    @property
    def output_limits(self):
        """The current output limits as a 2-tuple: (lower, upper). See also the *output_limts* parameter in :meth:`PID.__init__`."""
        return (self._min_output, self._max_output)

    @output_limits.setter
    def output_limits(self, limits):
        """Setter for the output limits"""
        if limits is None:
            self._min_output, self._max_output = None, None
            return

        min_output, max_output = limits

        if None not in limits and max_output < min_output:
            logger.error(_('lower limit must be less than upper limit'))
            raise ValueError(_('lower limit must be less than upper limit'))

        self._min_output = min_output
        self._max_output = max_output

        self._error_sum = min(self._error_sum, self._max_output)
        self._last_output = _clamp(self._last_output, self.output_limits)
