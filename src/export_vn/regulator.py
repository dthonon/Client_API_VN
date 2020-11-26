"""
Regulator for interval download, aiming at maintaining a constant size of data.
The setpoint is the number of sightings to be downloaded.
The controled variable is the time interval, in days.

Derived from https://github.com/m-lundberg/simple-pid

"""

import logging

from . import _, __version__
from typing import Optional, Tuple

logger = logging.getLogger("transfer_vn.regulator")


class PID(object):
    """A simple PID controller. No fuss."""

    Limits = Tuple[Optional[float], Optional[float]]
    Tunings = Tuple[float, float, float]

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.0,
        setpoint: float = 0.0,
        output_limits: Limits = (None, None),
    ):
        """Simple PID creation.

        Parameters
        ----------
        kp : float
            The value for the proportional gain kp.
        ki : float
            The value for the integral gain ki.
        kd : float
            The value for the derivative gain kd.
        setpoint : float
            The initial setpoint that the PID will try to achieve.
        output_limits : tuple(float, float)
            The initial output limits to use, given as an iterable with 2
            elements, for example: (lower, upper). The output will never go
            below the lower limit or above the upper limit. Either of the
            limits can also be set to None to have no limit in that direction.
            Setting output limits also avoids integral windup, since the
            integral term will never be allowed to grow outside of the limits.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint

        self._min_output, self._max_output = output_limits

        self._error_sum = 0.0

        self._last_output = None
        self._proportional = 0.0
        self._last_input = None

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    def _clamp(self, value: float, limits: Limits) -> float:
        if value is not None:
            lower, upper = limits
            if upper is not None and value > upper:
                return upper
            elif lower is not None and value < lower:
                return lower
        return value

    def __call__(self, input_: float) -> float:
        """
        Call the PID controller with *input_* and calculate and return a
        control output since the last update. If no new output is calculated,
        return the previous output instead (or None if no value has been
        calculated yet).
        """

        # compute error terms
        error = self.setpoint - input_
        self._error_sum += self.ki * error
        d_input = input_ - (
            self._last_input if self._last_input is not None else input_
        )

        # compute the proportional term
        self._proportional = self.kp * error

        output = self._proportional + self._error_sum - self.kd * d_input
        output = self._clamp(output, self.output_limits)

        # keep track of state
        self._last_output = output
        self._last_input = input_

        return output

    @property
    def tunings(self) -> Tunings:
        """The tunings used by the controller as a tuple: (kp, ki, kd)"""
        return self.kp, self.ki, self.kd

    @tunings.setter
    def tunings(self, tunings: Tunings) -> None:
        """Setter for the PID tunings"""
        self.kp, self.ki, self.kd = tunings

    @property
    def output_limits(self) -> Limits:
        """The current output limits as a 2-tuple: (lower, upper).
        See also the *output_limits* parameter in :meth:`PID.__init__`."""
        return (self._min_output, self._max_output)

    @output_limits.setter
    def output_limits(self, limits: Limits) -> None:
        """Setter for the output limits"""
        if limits is None:
            self._min_output, self._max_output = None, None
            return

        min_output, max_output = limits

        if None not in limits and max_output < min_output:
            logger.error(_("lower limit must be less than upper limit"))
            raise ValueError(_("lower limit must be less than upper limit"))

        self._min_output = min_output
        self._max_output = max_output

        self._error_sum = min(self._error_sum, self._max_output)
        self._last_output = self._clamp(self._last_output, self.output_limits)
