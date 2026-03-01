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
# USB Audio Piano & Music Control
# ============================================================================

def on_piano_note_on(sid, message):
    """Handle piano note ON - start playing note with USB audio and optional action.
    
    Args:
        sid: Socket ID
        message: Dict with 'note' (e.g., "C4", "F#5") and optional 'enable_action' (bool)
    """
    try:
        data = _ensure_dict(message)
        note = data.get("note")
        enable_action = data.get("enable_action", True)
        
        if note:
            otto.piano_note_on(note, enable_action)
            action_status = "with action" if enable_action else "sound only"
            print(f"[{_iso_now()}] [{sid}] Piano note ON: {note} ({action_status})")
            
            ui.send_message("piano_state", {
                "note": note,
                "state": "on",
                "enable_action": enable_action,
                "timestamp": _iso_now()
            })
    except Exception as e:
        ui.send_message("error", f"Piano note error: {e}")


def on_piano_note_off(sid, message):
    """Handle piano note OFF - stop playing note.
    
    Args:
        sid: Socket ID
        message: Dict with 'note'
    """
    try:
        data = _ensure_dict(message)
        note = data.get("note")
        
        if note:
            otto.piano_note_off(note)
            print(f"[{_iso_now()}] [{sid}] Piano note OFF: {note}")
            
            ui.send_message("piano_state", {
                "note": note,
                "state": "off",
                "timestamp": _iso_now()
            })
    except Exception as e:
        ui.send_message("error", f"Piano note error: {e}")


def on_piano_all_off(sid, message):
    """Stop all piano notes and audio.
    
    Args:
        sid: Socket ID
        message: Not used
    """
    try:
        otto.piano_all_off()
        print(f"[{_iso_now()}] [{sid}] All piano notes stopped")
        
        ui.send_message("piano_state", {
            "state": "all_off",
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Piano all off error: {e}")


def on_piano_sustain(sid, message):
    """Set sustain pedal state.
    
    Args:
        sid: Socket ID
        message: Dict with 'enabled' (bool)
    """
    try:
        data = _ensure_dict(message)
        enabled = bool(data.get("enabled", False))
        
        otto.set_sustain(enabled)
        print(f"[{_iso_now()}] [{sid}] Sustain pedal: {'ON' if enabled else 'OFF'}")
        
        ui.send_message("piano_sustain", {
            "enabled": enabled,
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Sustain error: {e}")


def on_audio_volume(sid, message):
    """Set audio volume.
    
    Args:
        sid: Socket ID
        message: Dict with 'volume' (0-100)
    """
    try:
        data = _ensure_dict(message)
        volume = int(data.get("volume", 80))
        volume = max(0, min(100, volume))
        
        otto.set_volume(volume)
        print(f"[{_iso_now()}] [{sid}] Audio volume: {volume}%")
        
        ui.send_message("audio_volume", {
            "volume": volume,
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Audio volume error: {e}")


# ============================================================================
# Music Playback & Dance Sync Control
# ============================================================================

import os

MUSIC_DIR = "assets/music"


def get_music_files():
    """获取可用音乐文件列表.
    
    Returns:
        包含文件名、路径的字典列表
    """
    import os
    songs = []
    
    possible_paths = [
        "assets/music",
        "../assets/music",
        "../../assets/music",
    ]
    
    for base_path in possible_paths:
        if os.path.exists(base_path):
            for file in os.listdir(base_path):
                if file.endswith('.txt'):
                    name = file.replace('.txt', '').replace('_', ' ').title()
                    songs.append({
                        "name": name,
                        "filename": file,
                        "path": os.path.join(base_path, file)
                    })
            break
    
    return sorted(songs, key=lambda x: x["name"])


def on_music_list(sid, message):
    """获取可用音乐文件列表.
    
    Args:
        sid: Socket ID
        message: 未使用
    """
    try:
        songs = get_music_files()
        print(f"[{_iso_now()}] [{sid}] Music list: {len(songs)} songs")
        
        ui.send_message("music_list", {
            "songs": songs,
            "timestamp": _iso_now()
        }, room=sid)
    except Exception as e:
        ui.send_message("error", f"Music list error: {e}")


def on_music_play(sid, message):
    """开始音乐播放并执行相应动作.
    
    解析音乐文件，根据每个音符的频率播放声音并执行OTTO动作.
    
    Args:
        sid: Socket ID
        message: 包含 'filename' 的字典
    """
    try:
        data = _ensure_dict(message)
        filename = data.get("filename")
        enable_dance = data.get("enable_dance", True)
        
        if not filename:
            ui.send_message("music_error", {"message": "未提供文件名"})
            return
        
        file_path = None
        for base_path in [MUSIC_DIR, "../assets/music", "../../assets/music"]:
            potential_path = os.path.join(base_path, filename)
            if os.path.exists(potential_path):
                file_path = potential_path
                break
        
        if not file_path:
            ui.send_message("music_error", {"message": f"文件未找到: {filename}"})
            return
        
        frequencies, durations = otto.parse_music_file(file_path)
        
        if frequencies is None or durations is None:
            ui.send_message("music_error", {"message": "解析音乐文件失败"})
            return
        
        def progress_callback(progress_data):
            if "status" in progress_data:
                if progress_data["status"] == "finished":
                    ui.send_message("music_finished", {"timestamp": _iso_now()})
                    ui.send_message("music_dance_state", {"status": "completed"})
                elif progress_data["status"] == "error":
                    ui.send_message("music_error", {"message": progress_data.get("message")})
            else:
                ui.send_message("music_progress", {
                    "position": progress_data.get("position", 0),
                    "note": progress_data.get("note", 0),
                    "total_notes": progress_data.get("total_notes", 0),
                    "frequency": progress_data.get("frequency", 0),
                    "timestamp": _iso_now()
                })
        
        otto.start_music_playback_with_dance(frequencies, durations, enable_dance, progress_callback)
        
        print(f"[{_iso_now()}] [{sid}] Music playback started: {filename} (dance: {enable_dance})")
        
        ui.send_message("music_state", {
            "is_playing": True,
            "is_paused": False,
            "filename": filename,
            "enable_dance": enable_dance,
            "timestamp": _iso_now()
        })
        
    except Exception as e:
        ui.send_message("error", f"Music play error: {e}")


def on_music_pause(sid, message):
    """Pause/resume music playback.
    
    Args:
        sid: Socket ID
        message: Not used
    """
    try:
        otto.pause_music_playback()
        print(f"[{_iso_now()}] [{sid}] Music pause toggled")
        
        ui.send_message("music_state", {
            "is_playing": otto.audio_state["is_playing"],
            "is_paused": otto.audio_state["is_paused"],
            "timestamp": _iso_now()
        })
    except Exception as e:
        ui.send_message("error", f"Music pause error: {e}")


def on_music_stop(sid, message):
    """停止音乐播放.
    
    Args:
        sid: Socket ID
        message: 未使用
    """
    try:
        otto.stop_music_playback()
        print(f"[{_iso_now()}] [{sid}] Music stopped")
        
        ui.send_message("music_state", {
            "is_playing": False,
            "is_paused": False,
            "timestamp": _iso_now()
        })
        
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

# USB Audio Piano Control
ui.on_message("piano:note_on", on_piano_note_on)
ui.on_message("piano:note_off", on_piano_note_off)
ui.on_message("piano:all_off", on_piano_all_off)
ui.on_message("piano:sustain", on_piano_sustain)
ui.on_message("audio:volume", on_audio_volume)

# Music Playback Control
ui.on_message("music:list", on_music_list)
ui.on_message("music:play", on_music_play)
ui.on_message("music:pause", on_music_pause)
ui.on_message("music:stop", on_music_stop)

# Start server
if __name__ == "__main__":
    print(f"[{_iso_now()}] Starting Arduino UNO Q Control Server")
    print(f"[{_iso_now()}] OTTO Controller initialized")
    App.run()
