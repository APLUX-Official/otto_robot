# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

"""
Arduino UNO Q Web Control Server

This is the main entry point for the Arduino UNO Q robot control web server.
It provides a WebSocket-based interface for controlling:
- Digital pin toggles
- Servo motors (4 channels)
- OTTO robot movements and dance sequences

Architecture:
    - main.py: Web server, message handlers, and API endpoints
    - otto_controller.py: OTTO robot motion control (imported)
    - otto_core.py: Core movement algorithms

Dependencies:
    - arduino.app_utils: Bridge for hardware communication
    - arduino.app_bricks.web_ui: WebUI framework
    - otto_controller: Robot motion controller
"""

import json
import ast
from datetime import datetime, UTC
from arduino.app_utils import *
from arduino.app_bricks.web_ui import WebUI
from otto_controller import get_controller


# ============================================================================
# Hardware Configuration
# ============================================================================

# Pin configuration with active-low flags
# Set "active_low": True if hardware turns ON when pin is LOW
PIN_CONFIG = {
    # Digital pins
    "D21": {"active_low": False},
    "D20": {"active_low": False},
    "D13": {"active_low": False},
    "D12": {"active_low": False},
    "D11": {"active_low": False},
    "D10": {"active_low": False},
    "D9": {"active_low": False},
    "D8": {"active_low": False},
    "D7": {"active_low": False},
    "D6": {"active_low": False},
    "D5": {"active_low": False},
    "D4": {"active_low": False},
    "D3": {"active_low": False},
    "D2": {"active_low": False},
    "D1": {"active_low": False},
    "D0": {"active_low": False},
    # Analog pins
    "A0": {"active_low": False},
    "A1": {"active_low": False},
    "A2": {"active_low": False},
    "A3": {"active_low": False},
    "A4": {"active_low": False},
    "A5": {"active_low": False},
    # STM LEDs (active low)
    "LED3_R": {"active_low": True},
    "LED3_G": {"active_low": True},
    "LED3_B": {"active_low": True},
    "LED4_R": {"active_low": True},
    "LED4_G": {"active_low": True},
    "LED4_B": {"active_low": True},
}

PIN_NAMES = tuple(PIN_CONFIG.keys())

# ============================================================================
# State Management
# ============================================================================

# Logical pin states (True = ON as seen by the UI)
pin_states = {name: False for name in PIN_NAMES}

# Servo configuration
SERVO_PINS = ["D3", "D5", "D6", "D9"]
SERVO_NAMES = {
    "D3": "左腿",
    "D5": "右腿",
    "D6": "左脚",
    "D9": "右脚"
}
servo_states = {pin: 90 for pin in SERVO_PINS}  # Default 90 degrees (center)

# Initialize OTTO controller
otto = get_controller()

# WebUI instance
ui = WebUI()


# ============================================================================
# Utility Functions
# ============================================================================

def _iso_now() -> str:
    """Return current ISO timestamp."""
    return datetime.now(UTC).isoformat()


def _normalize_state(value) -> bool:
    """
    Normalize various input types to boolean.
    
    Supports: bool, int, float, string representations
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("on", "true", "1"):
            return True
        if v in ("off", "false", "0"):
            return False
    raise ValueError(f"Invalid state value: {value!r}")


def _ensure_dict(payload):
    """
    Ensure payload is a dictionary, parsing JSON if necessary.
    
    Handles various input formats including:
    - Already a dict
    - JSON string
    - Python literal string
    - Bytes/Bytearray
    """
    if isinstance(payload, (list, tuple)) and len(payload) == 1:
        payload = payload[0]
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8", errors="strict")
    if isinstance(payload, str):
        s = payload.strip()
        try:
            return json.loads(s)
        except Exception:
            try:
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple)) and len(val) == 1 and isinstance(val[0], dict):
                    return val[0]
                if isinstance(val, dict):
                    return val
            except Exception:
                pass
        raise ValueError(f"Unsupported string payload: {s[:80]}...")
    raise ValueError(f"Unsupported payload type: {type(payload).__name__}")


def _state_for_hw(name: str, logical_state: bool) -> bool:
    """
    Convert logical state to hardware state.
    
    Applies active-low inversion if configured for the pin.
    """
    cfg = PIN_CONFIG.get(name, {})
    return (not logical_state) if cfg.get("active_low") else logical_state


# ============================================================================
# Pin Control Handlers
# ============================================================================

def on_pin_toggle(sid, message):
    """
    Handle pin toggle requests from UI.
    
    Args:
        sid: Socket ID of the requesting client
        message: Dict with 'name' (pin name) and 'state' (on/off)
    """
    try:
        data = _ensure_dict(message)
        name = data.get("name")
        
        if name not in PIN_NAMES:
            raise ValueError(f"Unknown Pin '{name}'")

        # Get logical state from UI
        logical = _normalize_state(data.get("state"))
        pin_states[name] = logical

        # Apply active-low for hardware call
        state_for_hw = _state_for_hw(name, logical)
        Bridge.call("set_pin_by_name", name, state_for_hw)

        print(f"[{_iso_now()}] [{sid}] {name} -> logical={'ON' if logical else 'OFF'} hw={state_for_hw}")
        
        ui.send_message("pin_state_update", {
            "name": name,
            "state": logical,
            "timestamp": _iso_now()
        })

    except Exception as e:
        ui.send_message("error", f"Pin toggle error: {e}")


def on_get_states():
    """Return current logical pin states to the UI."""
    return {"timestamp": _iso_now(), "states": pin_states}


# ============================================================================
# Servo Control Handlers
# ============================================================================

def on_servo_set(sid, message):
    """
    Set servo angle.
    
    Args:
        sid: Socket ID of the requesting client
        message: Dict with 'pin' and 'angle'
    """
    try:
        data = _ensure_dict(message)
        pin = data.get("pin")
        angle = data.get("angle")

        if pin not in SERVO_PINS:
            raise ValueError(f"Unknown servo pin '{pin}'")

        # Validate and convert angle
        try:
            angle = int(angle)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid angle value: {angle}")

        # Clamp to valid range
        angle = max(0, min(180, angle))

        # Send to hardware
        Bridge.call("set_servo_angle", pin, angle)
        servo_states[pin] = angle

        print(f"[{_iso_now()}] [{sid}] Servo {pin}({SERVO_NAMES[pin]}) -> {angle}°")
        
        ui.send_message("servo_state_update", {
            "pin": pin,
            "name": SERVO_NAMES[pin],
            "angle": angle,
            "timestamp": _iso_now()
        })

    except Exception as e:
        ui.send_message("error", f"Servo control error: {e}")


def on_servo_get(sid, message):
    """
    Get current servo angle.
    
    Args:
        sid: Socket ID of the requesting client
        message: Dict with 'pin'
        
    Returns:
        Dict with pin info and current angle
    """
    try:
        data = _ensure_dict(message)
        pin = data.get("pin")

        if pin not in SERVO_PINS:
            raise ValueError(f"Unknown servo pin '{pin}'")

        # Get from hardware
        result = Bridge.call("get_servo_angle", pin)
        if result is not None:
            servo_states[pin] = result

        return {
            "pin": pin,
            "name": SERVO_NAMES[pin],
            "angle": servo_states[pin]
        }

    except Exception as e:
        ui.send_message("error", f"Servo get error: {e}")
        return None


def on_servo_get_all():
    """Return all servo states."""
    return {
        "timestamp": _iso_now(),
        "servos": [
            {
                "pin": pin,
                "name": SERVO_NAMES[pin],
                "angle": servo_states[pin]
            }
            for pin in SERVO_PINS
        ]
    }


# ============================================================================
# OTTO Robot Action Handlers
# ============================================================================

def on_otto_action(sid, message):
    """
    Handle OTTO robot action commands.
    
    Supports actions:
    - Basic: walk, turn, turn_left, turn_right, home, stop
    - Dance: bend, shakeLeg, updown, swing, tiptoeSwing
    - Advanced: jitter, ascendingTurn, moonwalker, crusaito, flapping, jump
    
    Args:
        sid: Socket ID of the requesting client
        message: Dict with 'action' and action-specific parameters
    """
    try:
        data = _ensure_dict(message)
        action = data.get("action")
        
        print(f"[{_iso_now()}] [{sid}] Otto action: {action}")
        
        # Handle stop command
        if action == "stop":
            otto.stop_action()
            ui.send_message("otto_action_complete", {
                "action": "stop",
                "timestamp": _iso_now()
            })
            return
        
        # Reset stop flag for new action
        otto.reset_stop_flag()
        
        # Execute action
        result = None
        
        if action == "walk":
            result = otto.walk(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                direction=data.get("direction", 1)
            )
        elif action == "turn":
            result = otto.turn(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                direction=data.get("direction", 1)
            )
        elif action == "turn_left":
            result = otto.turn(steps=data.get("steps", 2), T=data.get("T", 1000), direction=1)
        elif action == "turn_right":
            result = otto.turn(steps=data.get("steps", 2), T=data.get("T", 1000), direction=-1)
        elif action == "home":
            otto.go_home()
            result = {"action": "home"}
        elif action == "bend":
            result = otto.bend(
                steps=data.get("steps", 1),
                T=data.get("T", 500),
                direction=data.get("direction", 1)
            )
        elif action == "shakeLeg":
            result = otto.shake_leg(
                steps=data.get("steps", 1),
                T=data.get("T", 1500),
                direction=data.get("direction", 1)
            )
        elif action == "updown":
            result = otto.updown(
                steps=data.get("steps", 2),
                T=data.get("T", 1500),
                height=data.get("height", 20)
            )
        elif action == "swing":
            result = otto.swing(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 20)
            )
        elif action == "tiptoeSwing":
            result = otto.tiptoe_swing(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 20)
            )
        elif action == "jitter":
            result = otto.jitter(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 20)
            )
        elif action == "ascendingTurn":
            result = otto.ascending_turn(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 50)
            )
        elif action == "moonwalker":
            result = otto.moonwalker(
                steps=data.get("steps", 3),
                T=data.get("T", 1000),
                height=data.get("height", 25),
                direction=data.get("direction", 1)
            )
        elif action == "crusaito":
            result = otto.crusaito(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 20),
                direction=data.get("direction", 1)
            )
        elif action == "flapping":
            result = otto.flapping(
                steps=data.get("steps", 2),
                T=data.get("T", 1000),
                height=data.get("height", 20),
                direction=data.get("direction", 1)
            )
        elif action == "jump":
            result = otto.jump(steps=data.get("steps", 1), T=data.get("T", 2000))
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Send completion message
        if result:
            result["timestamp"] = _iso_now()
            ui.send_message("otto_action_complete", result)
            
    except Exception as e:
        ui.send_message("error", f"Otto action error: {e}")


def on_dance_preset(sid, message):
    """
    Execute a predefined dance sequence.
    
    Available presets:
    - "happy": Cheerful swinging and walking
    - "dance": Dynamic moonwalker and crusaito
    - "greeting": Polite bowing and waving
    
    Args:
        sid: Socket ID of the requesting client
        message: Dict with 'preset' name
    """
    try:
        data = _ensure_dict(message)
        preset = data.get("preset")
        
        print(f"[{_iso_now()}] [{sid}] Dance preset: {preset}")
        
        # Send start notification
        ui.send_message("dance_preset_state", {
            "preset": preset,
            "status": "playing",
            "timestamp": _iso_now()
        })
        
        # Execute dance with progress callback
        def progress_callback(step, action_name):
            ui.send_message("dance_step_complete", {
                "preset": preset,
                "step": step,
                "action": action_name,
                "timestamp": _iso_now()
            })
        
        result = otto.execute_dance_sequence(preset, progress_callback)
        
        # Send completion notification
        status = "stopped" if result["stopped"] else "completed"
        ui.send_message("dance_preset_state", {
            "preset": preset,
            "status": status,
            "total_steps": result["completed_steps"],
            "timestamp": _iso_now()
        })
        
        print(f"[{_iso_now()}] [{sid}] Dance preset '{preset}' {status}")
        
    except Exception as e:
        ui.send_message("error", f"Dance preset error: {e}")


# ============================================================================
# Frequency-Action Mapping
# ============================================================================

# Frequency to Action Mapping - Precise musical rhythm control
# Maps note frequencies to specific OTTO robot actions
# Creates a musical choreography where each note triggers a movement

FREQUENCY_ACTION_MAP = {
    # Low frequency range (C3-G3) - Slow, deliberate movements
    (130.0, 135.0): {"action": "bend", "params": {"steps": 1, "T": 600, "direction": 1}, "name": "C3 - Bend Left"},
    (135.0, 142.0): {"action": "bend", "params": {"steps": 1, "T": 600, "direction": -1}, "name": "C#3 - Bend Right"},
    (142.0, 151.0): {"action": "updown", "params": {"steps": 1, "T": 700, "height": 10}, "name": "D3 - Small Up"},
    (151.0, 160.0): {"action": "updown", "params": {"steps": 1, "T": 700, "height": 20}, "name": "D#3 - Medium Up"},
    (160.0, 170.0): {"action": "swing", "params": {"steps": 1, "T": 650, "height": 10}, "name": "E3 - Small Swing"},
    (170.0, 180.0): {"action": "swing", "params": {"steps": 1, "T": 650, "height": 20}, "name": "F3 - Medium Swing"},
    (180.0, 191.0): {"action": "tiptoeSwing", "params": {"steps": 1, "T": 600, "height": 10}, "name": "F#3 - Tiptoe Small"},
    (191.0, 202.0): {"action": "tiptoeSwing", "params": {"steps": 1, "T": 600, "height": 20}, "name": "G3 - Tiptoe Medium"},
    (202.0, 214.0): {"action": "bend", "params": {"steps": 1, "T": 550, "direction": 1}, "name": "G#3 - Quick Bend Left"},
    (214.0, 227.0): {"action": "bend", "params": {"steps": 1, "T": 550, "direction": -1}, "name": "A3 - Quick Bend Right"},
    (227.0, 240.0): {"action": "updown", "params": {"steps": 1, "T": 600, "height": 15}, "name": "A#3 - Quick Up"},
    (240.0, 254.0): {"action": "swing", "params": {"steps": 1, "T": 600, "height": 15}, "name": "B3 - Quick Swing"},

    # Middle frequency range (C4-B4) - Standard movements
    (254.0, 269.0): {"action": "walk", "params": {"steps": 1, "T": 600, "direction": 1}, "name": "C4 - Walk Forward"},
    (269.0, 285.0): {"action": "walk", "params": {"steps": 1, "T": 600, "direction": -1}, "name": "C#4 - Walk Backward"},
    (285.0, 302.0): {"action": "turn", "params": {"steps": 1, "T": 550, "direction": 1}, "name": "D4 - Turn Left"},
    (302.0, 320.0): {"action": "turn", "params": {"steps": 1, "T": 550, "direction": -1}, "name": "D#4 - Turn Right"},
    (320.0, 339.0): {"action": "moonwalker", "params": {"steps": 1, "T": 600, "height": 15, "direction": 1}, "name": "E4 - Moonwalk Left"},
    (339.0, 359.0): {"action": "moonwalker", "params": {"steps": 1, "T": 600, "height": 15, "direction": -1}, "name": "F4 - Moonwalk Right"},
    (359.0, 381.0): {"action": "crusaito", "params": {"steps": 1, "T": 600, "height": 15, "direction": 1}, "name": "F#4 - Crusaito Left"},
    (381.0, 404.0): {"action": "crusaito", "params": {"steps": 1, "T": 600, "height": 15, "direction": -1}, "name": "G4 - Crusaito Right"},
    (404.0, 428.0): {"action": "flapping", "params": {"steps": 1, "T": 550, "height": 15, "direction": 1}, "name": "G#4 - Flap Forward"},
    (428.0, 453.0): {"action": "flapping", "params": {"steps": 1, "T": 550, "height": 15, "direction": -1}, "name": "A4 - Flap Backward"},
    (453.0, 480.0): {"action": "jitter", "params": {"steps": 1, "T": 500, "height": 10}, "name": "A#4 - Jitter Small"},
    (480.0, 508.0): {"action": "jitter", "params": {"steps": 1, "T": 500, "height": 20}, "name": "B4 - Jitter Medium"},

    # High frequency range (C5-G5) - Quick, energetic movements
    (508.0, 539.0): {"action": "ascendingTurn", "params": {"steps": 1, "T": 550, "height": 20}, "name": "C5 - Ascend Turn"},
    (539.0, 571.0): {"action": "shakeLeg", "params": {"steps": 1, "T": 500, "direction": 1}, "name": "C#5 - Shake Left Leg"},
    (571.0, 605.0): {"action": "shakeLeg", "params": {"steps": 1, "T":500, "direction": 1}, "name": "D5 - Shake Right Leg"},
    (605.0, 641.0): {"action": "jump", "params": {"steps": 1, "T": 450}, "name": "D#5 - Jump Small"},
    (641.0, 679.0): {"action": "jump", "params": {"steps": 1, "T": 400}, "name": "E5 - Jump Medium"},
    (679.0, 719.0): {"action": "jump", "params": {"steps": 1, "T": 350}, "name": "F5 - Jump High"},
    (719.0, 761.0): {"action": "jitter", "params": {"steps": 1, "T": 400, "height": 25}, "name": "F#5 - Fast Jitter"},
    (761.0, 800.0): {"action": "jump", "params": {"steps": 1, "T": 300}, "name": "G5 - Jump Max"},
}

# Note to Action Override - Specific note names trigger specific actions
NOTE_ACTION_OVERRIDE = {
    # Bass notes - Strong foundation movements
    "C3": {"action": "bend", "params": {"steps": 2, "T": 1000, "direction": 1}, "name": "C3 Bass - Deep Bend"},
    "G3": {"action": "swing", "params": {"steps": 2, "T": 1000, "height": 30}, "name": "G3 Bass - Wide Swing"},
    
    # Middle C - Home position
    "C4": {"action": "walk", "params": {"steps": 1, "T": 600, "direction": 1}, "name": "C4 - Walk Forward"},
    
    # High notes - Energetic finales
    "C5": {"action": "jump", "params": {"steps": 2, "T": 600}, "name": "C5 - Double Jump"},
    "D5": {"action": "shakeLeg", "params": {"steps": 1, "T": 500, "direction": -1}, "name": "D5 - Shake Right Leg"},
    "G5": {"action": "jump", "params": {"steps": 3, "T": 500}, "name": "G5 - Triple Jump Finale"},
    
    # Black keys mapping - F#3 (V和B中间)
    "C#3": {"action": "bend", "params": {"steps": 1, "T": 600, "direction": 1}, "name": "C#3 - Bend Left"},
    "D#3": {"action": "updown", "params": {"steps": 1, "T": 700, "height": 15}, "name": "D#3 - Up Down"},
    "F#3": {"action": "tiptoeSwing", "params": {"steps": 1, "T": 600, "height": 15}, "name": "F#3 - Tiptoe Swing"},
    "G#3": {"action": "bend", "params": {"steps": 1, "T": 550, "direction": 1}, "name": "G#3 - Quick Bend"},
    "A#3": {"action": "updown", "params": {"steps": 1, "T": 600, "height": 15}, "name": "A#3 - Quick Up"},
    
    # Black keys mapping - C#5到D#5 (K和L中间)
    "C#5": {"action": "shakeLeg", "params": {"steps": 1, "T": 500, "direction": 1}, "name": "C#5 - Shake Left Leg"},
    "D#5": {"action": "jump", "params": {"steps": 1, "T": 450}, "name": "D#5 - Jump Small"},
    "F#5": {"action": "jitter", "params": {"steps": 1, "T": 400, "height": 25}, "name": "F#5 - Fast Jitter"},
}

# Instrument-specific action modifiers
INSTRUMENT_ACTION_MODIFIER = {
    "piano": {"speed_multiplier": 1.0, "height_multiplier": 1.0},      # Standard
    "violin": {"speed_multiplier": 0.9, "height_multiplier": 1.2},     # Smooth, elevated
    "guitar": {"speed_multiplier": 1.1, "height_multiplier": 1.0},     # Rhythmic
    "flute": {"speed_multiplier": 0.8, "height_multiplier": 0.8},       # Gentle, low
    "trumpet": {"speed_multiplier": 1.2, "height_multiplier": 1.3},     # Bold, high
    "saxophone": {"speed_multiplier": 1.0, "height_multiplier": 1.1},   # Jazzy
    "bass": {"speed_multiplier": 0.7, "height_multiplier": 0.6},        # Slow, grounded
    "guzheng": {"speed_multiplier": 0.85, "height_multiplier": 0.9},    # Elegant
    "accordion": {"speed_multiplier": 0.9, "height_multiplier": 0.8},   # Flowing
}

def execute_action_by_frequency(frequency: float, note: str = None, instrument: str = "piano") -> dict:
    """
    Execute OTTO action based on note frequency.
    
    Creates a precise musical choreography where each frequency range
    maps to a specific robot movement, creating visual music.
    
    Args:
        frequency: Note frequency in Hz
        note: Optional note name (e.g., "C4", "F#5")
        instrument: Current instrument for style modification
        
    Returns:
        dict: Action execution result
    """
    result = {"frequency": frequency, "note": note, "instrument": instrument, "action": None}
    
    # Check for note-specific override first
    if note and note in NOTE_ACTION_OVERRIDE:
        action_config = NOTE_ACTION_OVERRIDE[note].copy()
    else:
        # Find frequency range
        action_config = None
        for (low, high), config in FREQUENCY_ACTION_MAP.items():
            if low <= frequency < high:
                action_config = config.copy()
                break
    
    if not action_config:
        result["error"] = "No action mapped for this frequency"
        return result
    
    # Apply instrument modifier
    modifier = INSTRUMENT_ACTION_MODIFIER.get(instrument, {"speed_multiplier": 1.0, "height_multiplier": 1.0})
    
    action_name = action_config["action"]
    params = action_config["params"].copy()
    
    # Modify parameters based on instrument style
    if "T" in params:
        params["T"] = int(params["T"] / modifier["speed_multiplier"])
    if "height" in params:
        params["height"] = int(params["height"] * modifier["height_multiplier"])
    
    result["action"] = action_name
    result["params"] = params
    result["action_name"] = action_config.get("name", action_name)
    
    # Execute action in non-blocking thread (quick single execution, no return to home)
    ACTION_NAME_MAP = {
        "shakeLeg": "shake_leg",
        "tiptoeSwing": "tiptoe_swing",
        "ascendingTurn": "ascending_turn",
    }
    import threading
    def run_action():
        try:
            # Reset stop flag before executing new action
            otto.reset_stop_flag()
            
            if action_name == "home":
                otto.go_home()
            else:
                # Map action name to method name if needed
                method_name = ACTION_NAME_MAP.get(action_name, action_name)
                if hasattr(otto, method_name):
                    action_method = getattr(otto, method_name)
                    action_method(**params)
                else:
                    print(f"Action method not found: {method_name}")
        except Exception as e:
            print(f"Action execution error: {e}")
    
    thread = threading.Thread(target=run_action, daemon=True)
    thread.start()
    
    result["status"] = "executing"
    return result


def on_instrument_change(sid, message):
    """Placeholder for instrument change."""
    try:
        data = _ensure_dict(message)
        instrument = data.get("instrument")
        print(f"[{_iso_now()}] [{sid}] Instrument change (placeholder): {instrument}")
        
        ui.send_message("instrument_state", {
            "instrument": instrument,
            "status": "changed",
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Instrument change error: {e}")


def on_instrument_note(sid, message):
    """Handle instrument note - trigger action by frequency."""
    try:
        data = _ensure_dict(message)
        note = data.get("note")
        frequency = data.get("frequency")
        instrument = data.get("instrument", "piano")
        
        print(f"[{_iso_now()}] [{sid}] Instrument note: {note} ({frequency}Hz)")
        
        # Trigger action based on frequency
        if frequency and frequency > 0:
            action_result = execute_action_by_frequency(frequency, note, instrument)
            print(f"[{_iso_now()}] Action executed for {frequency}Hz: {action_result}")
        
        ui.send_message("instrument_note_state", {
            "note": note,
            "frequency": frequency,
            "instrument": instrument,
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Instrument note error: {e}")


# ============================================================================
# Music-Dance Sync Control
# ============================================================================

import os

def load_music_sequence(song_id: str) -> list:
    """
    Load dance sequence from txt file for the given song.
    
    Args:
        song_id: Song identifier (e.g., "apt", "jilejingtu")
        
    Returns:
        List of action dictionaries, or empty list if not found
    """
    possible_paths = [
        f"assets/music/{song_id}.txt",
        f"../assets/music/{song_id}.txt",
        f"../../assets/music/{song_id}.txt",
        f"/home/arduino/ArduinoApps/servo-toggle/assets/music/{song_id}.txt",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content = content.replace('"custom_sequence": [', '[')
                    if content.strip().endswith(']'):
                        content = content.strip()[:-1]
                    if not content.strip().endswith(']'):
                        content = content + ']'
                    
                    sequence = eval(content)
                    print(f"[{_iso_now()}] Loaded dance sequence for {song_id}: {len(sequence)} actions")
                    return sequence
            except Exception as e:
                print(f"[{_iso_now()}] Error loading {path}: {e}")
                continue
    
    print(f"[{_iso_now()}] No sequence found for {song_id}")
    return []


def on_music_play(sid, message):
    """
    Handle music play - load and start dance sequence.
    """
    try:
        data = _ensure_dict(message)
        song_id = data.get("song_id")
        
        print(f"[{_iso_now()}] [{sid}] Music play: {song_id}")
        
        if not song_id:
            ui.send_message("music_dance_state", {"status": "error", "message": "No song_id"})
            return
        
        sequence = load_music_sequence(song_id)
        
        if not sequence:
            ui.send_message("music_dance_state", {
                "song_id": song_id,
                "status": "no_sequence"
            })
            return
        
        # Execute sequence using otto controller
        def progress_callback(step, action):
            ui.send_message("music_dance_progress", {
                "song_id": song_id,
                "step": step,
                "action": action
            })
        
        otto.reset_stop_flag()
        result = otto.execute_dance_sequence_from_list(sequence, progress_callback)
        
        ui.send_message("music_dance_state", {
            "song_id": song_id,
            "status": "completed",
            "completed_steps": result.get("completed_steps", 0)
        })
        
    except Exception as e:
        ui.send_message("error", f"Music play error: {e}")


def on_music_stop(sid, message):
    """
    Handle music stop - stop the dance sequence.
    """
    try:
        print(f"[{_iso_now()}] [{sid}] Music stop requested")
        otto.stop_action()
        otto.go_home()
        
        ui.send_message("music_dance_state", {"status": "stopped"})
        
    except Exception as e:
        ui.send_message("error", f"Music stop error: {e}")


# ============================================================================
# Server Registration and Startup
# ============================================================================

# Pin control
ui.on_message("pin_toggle", on_pin_toggle)
ui.expose_api("GET", "/states", on_get_states)

# Servo control
ui.on_message("servo_set", on_servo_set)
ui.on_message("servo_get", on_servo_get)
ui.expose_api("GET", "/servo_states", on_servo_get_all)

# OTTO robot control
ui.on_message("otto_action", on_otto_action)
ui.on_message("dance_preset", on_dance_preset)

# Instrument control - triggers robot actions
ui.on_message("instrument_change", on_instrument_change)
ui.on_message("instrument_note", on_instrument_note)

# Music-dance sync control
ui.on_message("music_play", on_music_play)
ui.on_message("music_stop", on_music_stop)

# Start server
if __name__ == "__main__":
    print(f"[{_iso_now()}] Starting Arduino UNO Q Control Server")
    print(f"[{_iso_now()}] OTTO Controller initialized")
    App.run()
