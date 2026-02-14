"""
Tests for voice WebSocket auto-reconnect logic
===============================================
Covers: reconnect scheduling, backoff calculation, user-initiated disconnect
handling, reconnect cancellation, attempt counting
"""

import pytest
import math


# ---------------------------------------------------------------------------
# Inline the reconnect logic from sowl.html / sowl_convai_server.py
# (JavaScript logic ported to Python for testability)
# ---------------------------------------------------------------------------

RECONNECT_BASE_DELAY = 2000  # ms
RECONNECT_MAX_DELAY = 30000  # ms
RECONNECT_MAX_ATTEMPTS = 10


def calculate_reconnect_delay(attempt):
    """Calculate reconnect delay for a given attempt number (1-indexed).

    Mirrors: Math.min(RECONNECT_BASE_DELAY * Math.pow(1.5, attempt), RECONNECT_MAX_DELAY)
    """
    return min(
        RECONNECT_BASE_DELAY * (1.5 ** attempt),
        RECONNECT_MAX_DELAY,
    )


def should_reconnect(user_disconnected, reconnect_attempts, max_attempts=RECONNECT_MAX_ATTEMPTS):
    """Determine if auto-reconnect should be scheduled.

    Returns (should_try, reason).
    """
    if user_disconnected:
        return False, "user_disconnected"
    if reconnect_attempts >= max_attempts:
        return False, "max_attempts_reached"
    return True, "ok"


class ReconnectState:
    """Simulates the reconnect state machine from the JS client."""

    def __init__(self):
        self.reconnect_attempts = 0
        self.reconnect_timer = None
        self.user_disconnected = False
        self.conversation = None
        self.session_started = False

    def on_connect(self):
        """Called when ElevenLabs session connects successfully."""
        self.reconnect_attempts = 0
        self.user_disconnected = False
        self.conversation = "active"
        self.session_started = True

    def on_disconnect(self):
        """Called when ElevenLabs session disconnects unexpectedly."""
        self.conversation = None
        self.session_started = False
        if not self.user_disconnected:
            return self._schedule_reconnect()
        return None

    def on_error(self):
        """Called on ElevenLabs session error."""
        self.conversation = None
        self.session_started = False
        if not self.user_disconnected:
            return self._schedule_reconnect()
        return None

    def user_end_session(self):
        """User intentionally ends the session (Escape / logout / settings)."""
        self.user_disconnected = True
        self.cancel_reconnect()
        self.conversation = None
        self.session_started = False

    def user_tap_orb(self):
        """User taps the orb to manually reconnect."""
        self.user_disconnected = False
        self.reconnect_attempts = 0
        self.cancel_reconnect()

    def cancel_reconnect(self):
        """Cancel any pending reconnect timer."""
        self.reconnect_timer = None

    def _schedule_reconnect(self):
        """Schedule a reconnect attempt. Returns delay in ms or None."""
        if self.user_disconnected or self.reconnect_attempts >= RECONNECT_MAX_ATTEMPTS:
            return None
        delay = calculate_reconnect_delay(self.reconnect_attempts)
        self.reconnect_attempts += 1
        self.reconnect_timer = delay  # In real code this would be setTimeout
        return delay


# ---------------------------------------------------------------------------
# Tests: Delay calculation
# ---------------------------------------------------------------------------

class TestReconnectDelay:
    """Test reconnect delay calculation."""

    def test_first_attempt_is_base_times_1_5(self):
        # attempt=0 -> 2000 * 1.5^0 = 2000 (but we pass attempt which is
        # reconnectAttempts before increment, i.e. 0)
        delay = calculate_reconnect_delay(0)
        assert delay == 2000  # 2000 * 1.5^0

    def test_second_attempt(self):
        delay = calculate_reconnect_delay(1)
        assert delay == 3000  # 2000 * 1.5^1

    def test_third_attempt(self):
        delay = calculate_reconnect_delay(2)
        assert delay == 4500  # 2000 * 1.5^2

    def test_delay_caps_at_max(self):
        delay = calculate_reconnect_delay(20)
        assert delay == RECONNECT_MAX_DELAY

    def test_delay_never_exceeds_max(self):
        for attempt in range(50):
            delay = calculate_reconnect_delay(attempt)
            assert delay <= RECONNECT_MAX_DELAY

    def test_delay_increases_monotonically(self):
        delays = [calculate_reconnect_delay(i) for i in range(20)]
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i - 1]

    def test_delay_is_always_positive(self):
        for attempt in range(50):
            assert calculate_reconnect_delay(attempt) > 0

    def test_specific_progression(self):
        expected = [2000, 3000, 4500, 6750, 10125, 15187.5, 22781.25, 30000]
        for i, exp in enumerate(expected):
            delay = calculate_reconnect_delay(i)
            assert abs(delay - exp) < 1  # floating point tolerance


# ---------------------------------------------------------------------------
# Tests: Should reconnect decision
# ---------------------------------------------------------------------------

class TestShouldReconnect:
    """Test the decision logic for whether to auto-reconnect."""

    def test_should_reconnect_normally(self):
        ok, reason = should_reconnect(False, 0)
        assert ok is True
        assert reason == "ok"

    def test_no_reconnect_when_user_disconnected(self):
        ok, reason = should_reconnect(True, 0)
        assert ok is False
        assert reason == "user_disconnected"

    def test_no_reconnect_at_max_attempts(self):
        ok, reason = should_reconnect(False, RECONNECT_MAX_ATTEMPTS)
        assert ok is False
        assert reason == "max_attempts_reached"

    def test_no_reconnect_over_max_attempts(self):
        ok, reason = should_reconnect(False, RECONNECT_MAX_ATTEMPTS + 5)
        assert ok is False
        assert reason == "max_attempts_reached"

    def test_reconnect_just_under_max(self):
        ok, reason = should_reconnect(False, RECONNECT_MAX_ATTEMPTS - 1)
        assert ok is True

    def test_user_disconnected_overrides_low_attempts(self):
        ok, _ = should_reconnect(True, 0)
        assert ok is False


# ---------------------------------------------------------------------------
# Tests: State machine
# ---------------------------------------------------------------------------

class TestReconnectStateMachine:
    """Test the full reconnect state machine."""

    def test_initial_state(self):
        state = ReconnectState()
        assert state.reconnect_attempts == 0
        assert state.reconnect_timer is None
        assert state.user_disconnected is False
        assert state.conversation is None

    def test_connect_resets_attempts(self):
        state = ReconnectState()
        state.reconnect_attempts = 5
        state.on_connect()
        assert state.reconnect_attempts == 0
        assert state.conversation == "active"

    def test_disconnect_schedules_reconnect(self):
        state = ReconnectState()
        state.on_connect()
        delay = state.on_disconnect()
        assert delay is not None
        assert delay > 0
        assert state.reconnect_attempts == 1
        assert state.conversation is None

    def test_error_schedules_reconnect(self):
        state = ReconnectState()
        state.on_connect()
        delay = state.on_error()
        assert delay is not None
        assert delay > 0
        assert state.reconnect_attempts == 1

    def test_user_end_session_prevents_reconnect(self):
        state = ReconnectState()
        state.on_connect()
        state.user_end_session()
        assert state.user_disconnected is True
        assert state.reconnect_timer is None

        # Now simulate a disconnect event (from endSession callback)
        delay = state.on_disconnect()
        assert delay is None  # should NOT reconnect

    def test_user_tap_orb_resets_state(self):
        state = ReconnectState()
        state.reconnect_attempts = 5
        state.user_disconnected = True
        state.user_tap_orb()
        assert state.reconnect_attempts == 0
        assert state.user_disconnected is False

    def test_multiple_disconnects_increase_attempts(self):
        state = ReconnectState()
        state.on_connect()

        delays = []
        for _ in range(5):
            delay = state.on_disconnect()
            delays.append(delay)

        assert state.reconnect_attempts == 5
        # Delays should increase
        for i in range(1, len(delays)):
            assert delays[i] >= delays[i - 1]

    def test_max_attempts_stops_reconnecting(self):
        state = ReconnectState()
        state.on_connect()

        for _ in range(RECONNECT_MAX_ATTEMPTS):
            state.on_disconnect()

        # Next disconnect should return None (max reached)
        delay = state.on_disconnect()
        assert delay is None
        assert state.reconnect_attempts == RECONNECT_MAX_ATTEMPTS

    def test_successful_reconnect_resets_counter(self):
        state = ReconnectState()
        state.on_connect()

        # Disconnect 3 times
        for _ in range(3):
            state.on_disconnect()
        assert state.reconnect_attempts == 3

        # Successful reconnect
        state.on_connect()
        assert state.reconnect_attempts == 0

        # Next disconnect starts from 0 again
        delay = state.on_disconnect()
        assert delay == calculate_reconnect_delay(0)
        assert state.reconnect_attempts == 1

    def test_cancel_reconnect_clears_timer(self):
        state = ReconnectState()
        state.on_connect()
        state.on_disconnect()  # sets reconnect_timer
        assert state.reconnect_timer is not None
        state.cancel_reconnect()
        assert state.reconnect_timer is None

    def test_settings_button_flow(self):
        """Simulate: connected -> settings button -> should not reconnect."""
        state = ReconnectState()
        state.on_connect()
        assert state.conversation == "active"

        state.user_end_session()
        assert state.conversation is None
        assert state.user_disconnected is True

        # The onDisconnect callback fires from endSession
        delay = state.on_disconnect()
        assert delay is None  # no reconnect

    def test_escape_key_flow(self):
        """Simulate: connected -> Escape key -> should not reconnect."""
        state = ReconnectState()
        state.on_connect()
        state.user_end_session()
        delay = state.on_disconnect()
        assert delay is None

    def test_network_glitch_flow(self):
        """Simulate: connected -> network error -> auto-reconnect."""
        state = ReconnectState()
        state.on_connect()

        # Network error
        delay = state.on_error()
        assert delay is not None
        assert state.reconnect_attempts == 1

        # Simulated reconnect succeeds
        state.on_connect()
        assert state.reconnect_attempts == 0

    def test_logout_then_orb_tap(self):
        """Simulate: logout (user disconnect) -> tap orb -> fresh start."""
        state = ReconnectState()
        state.on_connect()
        state.user_end_session()
        assert state.user_disconnected is True

        state.user_tap_orb()
        assert state.user_disconnected is False
        assert state.reconnect_attempts == 0


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases for reconnect logic."""

    def test_disconnect_before_connect(self):
        """Disconnect without ever connecting should still try to reconnect."""
        state = ReconnectState()
        delay = state.on_disconnect()
        assert delay is not None

    def test_error_before_connect(self):
        """Error without ever connecting should try to reconnect."""
        state = ReconnectState()
        delay = state.on_error()
        assert delay is not None

    def test_rapid_disconnect_reconnect_cycle(self):
        """Rapid disconnect/reconnect should track attempts correctly."""
        state = ReconnectState()
        for i in range(RECONNECT_MAX_ATTEMPTS - 1):
            state.on_disconnect()
        assert state.reconnect_attempts == RECONNECT_MAX_ATTEMPTS - 1

        # One more should work
        delay = state.on_disconnect()
        assert delay is not None
        assert state.reconnect_attempts == RECONNECT_MAX_ATTEMPTS

        # Next one should fail
        delay = state.on_disconnect()
        assert delay is None
