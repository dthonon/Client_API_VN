"""
Test download size regulator.
"""
import logging

from export_vn.regulator import PID

import pytest


@pytest.mark.order(index=90)
class TestRegulator:
    def test_version(self):
        """Check if version is defined."""
        logging.debug("package version: %s", PID().version)

    def test_tunings(self):
        """Check tunings property and setter."""
        pid = PID(1, 2, 3, output_limits=(0, 10))
        assert pid.tunings == (1, 2, 3)
        assert pid.output_limits == (0, 10)
        pid.tunings = (4, 5, 6)
        assert pid.tunings == (4, 5, 6)
        pid.output_limits = (20, 30)
        assert pid.output_limits == (20, 30)
        with pytest.raises(ValueError):
            pid.output_limits = (30, 0)

    def test_zero(self):
        pid = PID(1, 1, 1, setpoint=0)
        assert pid(0) == 0

    def test_P(self):
        pid = PID(1, 0, 0, setpoint=10)
        assert pid(0) == 10
        assert pid(5) == 5
        assert pid(-5) == 15

    def test_P_negative_setpoint(self):
        pid = PID(1, 0, 0, setpoint=-10)
        assert pid(0) == -10
        assert pid(5) == -15
        assert pid(-5) == -5
        assert pid(-15) == 5

    def test_I(self):
        pid = PID(0, 10, 0, setpoint=10)
        assert round(pid(0)) == 100.0  # make sure we are close to expected value
        assert round(pid(0)) == 200.0

    def test_I_negative_setpoint(self):
        pid = PID(0, 10, 0, setpoint=-10)
        assert round(pid(0)) == -100.0
        assert round(pid(0)) == -200.0

    def test_D(self):
        pid = PID(0, 0, 1, setpoint=10)
        # should not compute derivate when there is no previous input
        # (don't assume 0 as first input)
        assert pid(0) == 0
        # derivate is 0 when input is the same
        assert pid(0) == 0
        assert pid(0) == 0
        assert pid(5) == -5
        assert pid(20) == -15

    def test_D_negative_setpoint(self):
        pid = PID(0, 0, 1, setpoint=-10)
        # should not compute derivate when there is no previous input
        # (don't assume 0 as first input)
        assert pid(0) == 0
        # derivate is 0 when input is the same
        assert pid(0) == 0
        assert pid(0) == 0
        assert pid(5) == -5
        assert pid(-5) == 10
        assert pid(-30) == 25

    def test_desired_state(self):
        pid = PID(10, 5, 2, setpoint=10)
        # should not make any adjustment when setpoint is achieved
        assert pid(10) == 0

    def test_output_limits(self):
        pid = PID(100, 20, 40, setpoint=10, output_limits=(0, 100))
        assert 0 <= pid(0) <= 100
        assert 0 <= pid(-100) <= 100
        pid.output_limits = (0, 50)
        assert 0 <= pid(0) <= 50
        assert 0 <= pid(-100) <= 50
