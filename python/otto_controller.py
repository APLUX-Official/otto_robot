# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

"""
OTTO Robot Motion Controller Module

This module handles all OTTO robot movement controls including:
- Walking (forward/backward)
- Turning (left/right)
- Dance moves (bend, shakeLeg, updown, swing, etc.)
- Servo frame execution
- Dance presets
- USB audio synthesis with WaveGenerator
- Piano and music playback with frequency-to-action mapping

Dependencies:
    - otto_core: Core movement algorithms
    - arduino.app_utils.Bridge: Hardware communication
    - arduino.app_bricks.wave_generator.WaveGenerator: Audio synthesis
"""

import time
import threading
from datetime import datetime, UTC
from otto_core import OttoCore
from arduino.app_utils import Bridge
from arduino.app_bricks.wave_generator import WaveGenerator


class OttoController:
    """
    OTTO Robot Motion Controller with USB Audio Support
    
    Manages all robot movements, dance sequences, and audio synthesis.
    Provides a clean interface for executing actions and handling servo controls.
    
    Attributes:
        otto (OttoCore): Core movement algorithm instance
        servo_pins (list): List of servo pin names [D3, D5, D6, D9]
        servo_names (dict): Mapping of pin to human-readable names
        servo_states (dict): Current angle of each servo
        action_stop_flag (bool): Flag to stop current action
        wave_gen (WaveGenerator): USB audio synthesis engine
        audio_state (dict): Current audio playback state
    """
    
    # Servo configuration
    SERVO_PINS = ["D3", "D5", "D6", "D9"]
    SERVO_NAMES = {
        "D3": "左腿",
        "D5": "右腿", 
        "D6": "左脚",
        "D9": "右脚"
    }
    
    def __init__(self):
        """Initialize OTTO controller with default states and audio engine."""
        self.otto = OttoCore()
        self.servo_states = {pin: 90 for pin in self.SERVO_PINS}
        self.action_stop_flag = False
        
        self.wave_gen = WaveGenerator(
            sample_rate=16000,
            wave_type="sine",
            block_duration=0.03,
            attack=0.01,
            release=0.03,
            glide=0.02,
        )
        self.wave_gen.set_frequency(440.0)
        self.wave_gen.set_amplitude(0.0)
        
        self.audio_state = {
            "is_playing": False,
            "is_paused": False,
            "volume": 80,
            "mode": "piano",
            "current_frequency": 440.0,
            "active_notes": {},
            "sustain": False,
        }
        
        self._audio_lock = threading.Lock()
        self._playback_thread = None
        self._stop_event = threading.Event()
        
    def _iso_now(self) -> str:
        """Return current ISO timestamp."""
        return datetime.now(UTC).isoformat()
    
    def _set_servo_angle_safe(self, pin: str, angle: int) -> bool:
        """
        Set servo angle only if it has changed (prevents jitter).
        
        Args:
            pin: Servo pin name
            angle: Target angle (0-180)
            
        Returns:
            bool: True if angle was changed, False if skipped
        """
        # Clamp angle to valid range
        angle = max(0, min(180, angle))
        
        # Only send command if angle has changed significantly (>2 degrees)
        if abs(self.servo_states.get(pin, -1) - angle) > 2:
            Bridge.call("set_servo_angle", pin, angle)
            self.servo_states[pin] = angle
            return True
        return False
    
    def go_home(self) -> None:
        """
        Move all servos to HOME position.
        
        HOME position is the neutral stance where all servos are centered.
        This is called after most actions to return to a stable position.
        """
        home_pos = self.otto.home()
        angles = home_pos.to_list()
        
        changed = False
        for i, pin in enumerate(self.SERVO_PINS):
            if self._set_servo_angle_safe(pin, angles[i]):
                changed = True
            
        if changed:
            print(f"[{self._iso_now()}] Servos moved to HOME position")
    
    def execute_servo_frames(self, frames: list, delay_ms: int = 30) -> None:
        """
        Execute a sequence of servo position frames.
        
        Args:
            frames: List of ServoPosition objects from otto_core
            delay_ms: Delay between frames in milliseconds
            
        Note:
            Checks action_stop_flag after each frame to allow interruption.
        """
        for frame in frames:
            # Check for stop signal
            if self.action_stop_flag:
                print(f"[{self._iso_now()}] Action stopped by user")
                break
                
            # Apply angles to servos (only if changed)
            angles = frame.to_list()
            for i, pin in enumerate(self.SERVO_PINS):
                self._set_servo_angle_safe(pin, angles[i])
                
            time.sleep(delay_ms / 1000.0)
    
    def stop_action(self) -> None:
        """Set stop flag to interrupt current action."""
        self.action_stop_flag = True
        print(f"[{self._iso_now()}] Stop signal received")
    
    def reset_stop_flag(self) -> None:
        """Reset stop flag before starting new action."""
        self.action_stop_flag = False
    
    # ==================== Audio Control Methods ====================
    
    def set_volume(self, volume: int) -> None:
        """Set audio volume (0-100).
        
        Args:
            volume: Volume level (0-100)
        """
        volume = max(0, min(100, volume))
        self.audio_state["volume"] = volume
        self.wave_gen.set_volume(volume)
    
    def get_volume(self) -> float:
        """Get current volume as normalized value (0.0-1.0).
        
        Returns:
            Normalized volume (0.0-1.0)
        """
        return self.audio_state["volume"] / 100.0
    
    def play_tone(self, frequency: float) -> None:
        """Play a tone with the given frequency using USB audio.
        
        Args:
            frequency: Frequency in Hz
        """
        volume = self.get_volume()
        self.wave_gen.set_frequency(frequency)
        self.wave_gen.set_amplitude(volume)
        self.audio_state["current_frequency"] = frequency
    
    def stop_tone(self) -> None:
        """Stop the current tone (set amplitude to 0)."""
        self.wave_gen.set_amplitude(0.0)
    
    def set_audio_mode(self, mode: str) -> None:
        """Set audio mode.
        
        Args:
            mode: "piano" or "theremin"
        """
        self.audio_state["mode"] = mode
    
    # ==================== Frequency-Action Mapping ====================
    
    FREQUENCY_ACTION_MAP = {
        (130.0, 147.0): {"action": "bend", "params": {"steps": 1, "T": 800, "direction": 1}, "name": "C3 - Bend Left"},
        (147.0, 165.0): {"action": "bend", "params": {"steps": 1, "T": 800, "direction": -1}, "name": "D3 - Bend Right"},
        (165.0, 185.0): {"action": "shake_leg", "params": {"steps": 1, "T": 1200, "direction": 1}, "name": "E3 - Shake Left Leg"},
        (185.0, 210.0): {"action": "shake_leg", "params": {"steps": 1, "T": 1200, "direction": -1}, "name": "F#3 - Shake Right Leg"},
        (210.0, 247.0): {"action": "updown", "params": {"steps": 1, "T": 800, "height": 15}, "name": "G3 - UpDown"},
        
        (247.0, 294.0): {"action": "swing", "params": {"steps": 1, "T": 700, "height": 20}, "name": "C4 - Swing"},
        (294.0, 349.0): {"action": "tiptoe_swing", "params": {"steps": 1, "T": 700, "height": 20}, "name": "D4 - Tiptoe Swing"},
        (349.0, 392.0): {"action": "jitter", "params": {"steps": 1, "T": 500, "height": 15}, "name": "E4 - Jitter"},
        (392.0, 466.0): {"action": "ascending_turn", "params": {"steps": 1, "T": 600, "height": 10}, "name": "F4 - Ascending Turn"},
        (466.0, 523.0): {"action": "moonwalker", "params": {"steps": 1, "T": 800, "height": 20, "direction": 1}, "name": "G4 - Moonwalker Left"},
        
        (523.0, 587.0): {"action": "crusaito", "params": {"steps": 1, "T": 800, "height": 20, "direction": 1}, "name": "C5 - Crusaito Left"},
        (587.0, 659.0): {"action": "flapping", "params": {"steps": 1, "T": 600, "height": 15, "direction": 1}, "name": "D5 - Flapping"},
        (659.0, 698.0): {"action": "jump", "params": {"steps": 1, "T": 1000}, "name": "E5 - Jump"},
        (698.0, 784.0): {"action": "crusaito", "params": {"steps": 1, "T": 800, "height": 20, "direction": -1}, "name": "F5 - Crusaito Right"},
        (784.0, 1000.0): {"action": "moonwalker", "params": {"steps": 1, "T": 800, "height": 20, "direction": -1}, "name": "G5 - Moonwalker Right"},
    }
    
    NOTE_ACTION_OVERRIDE = {
        "C3": {"action": "bend", "params": {"steps": 1, "T": 1000, "direction": 1}, "name": "C3 - Deep Bend Left"},
        "C#3": {"action": "bend", "params": {"steps": 1, "T": 1000, "direction": -1}, "name": "C#3 - Deep Bend Right"},
        "D3": {"action": "shake_leg", "params": {"steps": 1, "T": 1500, "direction": 1}, "name": "D3 - Shake Left Leg"},
        "D#3": {"action": "shake_leg", "params": {"steps": 1, "T": 1500, "direction": -1}, "name": "D#3 - Shake Right Leg"},
        "E3": {"action": "updown", "params": {"steps": 1, "T": 1000, "height": 20}, "name": "E3 - UpDown"},
        "F3": {"action": "updown", "params": {"steps": 1, "T": 1000, "height": 25}, "name": "F3 - UpDown High"},
        "G3": {"action": "swing", "params": {"steps": 1, "T": 800, "height": 25}, "name": "G3 - Swing Wide"},
        "G#3": {"action": "tiptoe_swing", "params": {"steps": 1, "T": 800, "height": 20}, "name": "G#3 - Tiptoe Swing"},
        "A3": {"action": "jitter", "params": {"steps": 1, "T": 500, "height": 20}, "name": "A3 - Jitter"},
        "A#3": {"action": "ascending_turn", "params": {"steps": 1, "T": 600, "height": 12}, "name": "A#3 - Ascending Turn"},
        "B3": {"action": "moonwalker", "params": {"steps": 1, "T": 900, "height": 20, "direction": 1}, "name": "B3 - Moonwalker"},
        
        "C4": {"action": "swing", "params": {"steps": 1, "T": 700, "height": 20}, "name": "C4 - Swing"},
        "C#4": {"action": "tiptoe_swing", "params": {"steps": 1, "T": 700, "height": 20}, "name": "C#4 - Tiptoe Swing"},
        "D4": {"action": "jitter", "params": {"steps": 1, "T": 500, "height": 15}, "name": "D4 - Jitter"},
        "D#4": {"action": "ascending_turn", "params": {"steps": 1, "T": 600, "height": 10}, "name": "D#4 - Ascending Turn"},
        "E4": {"action": "moonwalker", "params": {"steps": 1, "T": 800, "height": 20, "direction": 1}, "name": "E4 - Moonwalker Left"},
        "F4": {"action": "crusaito", "params": {"steps": 1, "T": 800, "height": 20, "direction": 1}, "name": "F4 - Crusaito Left"},
        "F#4": {"action": "flapping", "params": {"steps": 1, "T": 600, "height": 15, "direction": 1}, "name": "F#4 - Flapping"},
        "G4": {"action": "jump", "params": {"steps": 1, "T": 1000}, "name": "G4 - Jump"},
        "G#4": {"action": "crusaito", "params": {"steps": 1, "T": 800, "height": 20, "direction": -1}, "name": "G#4 - Crusaito Right"},
        "A4": {"action": "moonwalker", "params": {"steps": 1, "T": 800, "height": 20, "direction": -1}, "name": "A4 - Moonwalker Right"},
        "A#4": {"action": "ascending_turn", "params": {"steps": 1, "T": 600, "height": 12}, "name": "A#4 - Ascending Turn Fast"},
        "B4": {"action": "jitter", "params": {"steps": 1, "T": 450, "height": 20}, "name": "B4 - Fast Jitter"},
        
        "C5": {"action": "swing", "params": {"steps": 1, "T": 650, "height": 25}, "name": "C5 - Swing Fast"},
        "C#5": {"action": "tiptoe_swing", "params": {"steps": 1, "T": 650, "height": 25}, "name": "C#5 - Tiptoe Swing Fast"},
        "D5": {"action": "flapping", "params": {"steps": 1, "T": 550, "height": 20, "direction": 1}, "name": "D5 - Fast Flapping"},
        "D#5": {"action": "jump", "params": {"steps": 1, "T": 900}, "name": "D#5 - Quick Jump"},
        "E5": {"action": "jump", "params": {"steps": 1, "T": 800}, "name": "E5 - Jump Higher"},
        "F5": {"action": "crusaito", "params": {"steps": 1, "T": 700, "height": 25, "direction": -1}, "name": "F5 - Fast Crusaito"},
        "F#5": {"action": "moonwalker", "params": {"steps": 1, "T": 700, "height": 25, "direction": -1}, "name": "F#5 - Fast Moonwalker"},
        "G5": {"action": "jump", "params": {"steps": 1, "T": 700}, "name": "G5 - Jump Fast"},
    }
    
    def get_action_by_frequency(self, frequency: float, note: str = None) -> dict:
        """Get OTTO action based on note frequency.
        
        Args:
            frequency: Note frequency in Hz
            note: Optional note name (e.g., "C4", "F#5")
            
        Returns:
            dict with action configuration or None if no match
        """
        if note and note in self.NOTE_ACTION_OVERRIDE:
            return self.NOTE_ACTION_OVERRIDE[note].copy()
        
        for (low, high), config in self.FREQUENCY_ACTION_MAP.items():
            if low <= frequency < high:
                return config.copy()
        
        return None
    
    def execute_action_by_frequency(self, frequency: float, note: str = None, 
                                   enable_action: bool = True,
                                   sync_audio: bool = True) -> dict:
        """Execute OTTO action based on note frequency with optional USB audio playback.
        
        Args:
            frequency: Note frequency in Hz
            note: Optional note name
            enable_action: Whether to trigger robot action (default: True)
            sync_audio: Whether to play audio synchronously
            
        Returns:
            dict with execution result
        """
        result = {"frequency": frequency, "note": note, "action": None, "enable_action": enable_action}
        
        if enable_action:
            action_config = self.get_action_by_frequency(frequency, note)
            
            if not action_config:
                result["error"] = "No action mapped for this frequency"
                return result
            
            action_name = action_config["action"]
            params = action_config["params"]
            
            result["action"] = action_name
            result["params"] = params
            result["action_name"] = action_config.get("name", action_name)
        
        if sync_audio:
            self.play_tone(frequency)
        
        if enable_action and result.get("action"):
            def run_action():
                self.reset_stop_flag()
                
                action_name = result["action"]
                params = result.get("params", {})
                
                if action_name == "home":
                    self.go_home()
                elif hasattr(self, action_name):
                    action_method = getattr(self, action_name)
                    action_method(**params)
            
            thread = threading.Thread(target=run_action, daemon=True)
            thread.start()
            
            result["status"] = "executing"
        
        return result
    
    # ==================== Piano Methods ====================
    
    PIANO_NOTES = {
        "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81,
        "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00,
        "A#3": 233.08, "B3": 246.94,
        "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63,
        "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00,
        "A#4": 466.16, "B4": 493.88,
        "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.25,
        "F5": 698.46, "F#5": 739.99, "G5": 783.99,
    }
    
    def piano_note_on(self, note_name: str, enable_action: bool = True) -> None:
        """Start playing a piano note with USB audio and optional action.
        
        Args:
            note_name: Note name (e.g., "C4", "F#5")
            enable_action: Whether to trigger robot action (default: True)
        """
        if note_name in self.audio_state["active_notes"]:
            return
        
        if note_name not in self.PIANO_NOTES:
            return
        
        freq = self.PIANO_NOTES[note_name]
        
        self.audio_state["active_notes"][note_name] = {
            "start_time": time.time(),
            "frequency": freq,
        }
        
        self.execute_action_by_frequency(freq, note_name, enable_action=enable_action, sync_audio=True)
    
    def piano_note_off(self, note_name: str) -> None:
        """Stop playing a piano note.
        
        Args:
            note_name: Note name
        """
        if note_name in self.audio_state["active_notes"]:
            del self.audio_state["active_notes"][note_name]
        
        if not self.audio_state["sustain"] and not self.audio_state["active_notes"]:
            self.stop_tone()
        elif self.audio_state["active_notes"]:
            last_note = list(self.audio_state["active_notes"].keys())[-1]
            freq = self.audio_state["active_notes"][last_note]["frequency"]
            self.play_tone(freq)
    
    def piano_all_off(self) -> None:
        """Stop all piano notes and audio."""
        self.audio_state["active_notes"].clear()
        self.stop_tone()
    
    def set_sustain(self, enabled: bool) -> None:
        """Set sustain pedal state.
        
        Args:
            enabled: True to enable sustain
        """
        self.audio_state["sustain"] = enabled
        if not enabled and not self.audio_state["active_notes"]:
            self.stop_tone()
    
    # ==================== Music Playback Methods ====================
    
    def parse_music_file(self, file_path: str) -> tuple:
        """Parse music file and extract frequencies and durations.
        
        Args:
            file_path: Path to the music .txt file
            
        Returns:
            Tuple of (frequencies list, durations list) or (None, None) on error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frequencies = []
            durations = []
            
            freq_var_names = ['jasmine_freqs_full', 'freqs_full', 'jucildexiatian_freqs_full']
            freq_start = -1
            
            for var_name in freq_var_names:
                var_pattern = var_name + ' = ['
                pos = content.find(var_pattern)
                if pos != -1:
                    freq_start = pos + len(var_pattern) - 1
                    break
            
            if freq_start != -1:
                bracket_start = content.find('[', freq_start)
                if bracket_start != -1:
                    bracket_end = content.find(']', bracket_start + 1)
                    if bracket_end != -1:
                        freq_content = content[bracket_start + 1:bracket_end]
                        frequencies = [float(x.strip()) for x in freq_content.split(',') if x.strip()]
            
            dur_var_names = ['jasmine_durations_full', 'durations_full', 'jucildexiatian_durations_full']
            dur_start = -1
            
            for var_name in dur_var_names:
                var_pattern = var_name + ' = ['
                pos = content.find(var_pattern)
                if pos != -1:
                    dur_start = pos + len(var_pattern) - 1
                    break
            
            if dur_start != -1:
                bracket_start = content.find('[', dur_start)
                if bracket_start != -1:
                    bracket_end = content.find(']', bracket_start + 1)
                    if bracket_end != -1:
                        dur_content = content[bracket_start + 1:bracket_end]
                        durations = [float(x.strip()) for x in dur_content.split(',') if x.strip()]
            
            if frequencies and durations:
                return frequencies, durations
            return None, None
            
        except Exception as e:
            print(f"[{self._iso_now()}] Error parsing music file: {e}")
            return None, None
    
    def play_music_thread(self, frequencies: list, durations: list, 
                          progress_callback=None) -> None:
        """Play music sequence using USB audio.
        
        Args:
            frequencies: List of frequencies
            durations: List of durations in milliseconds
            progress_callback: Optional callback for progress updates
        """
        if not frequencies or not durations:
            if progress_callback:
                progress_callback({"status": "error", "message": "Invalid song data"})
            return
        
        num_notes = min(len(frequencies), len(durations))
        
        self._stop_event.clear()
        self.audio_state["is_playing"] = True
        self.audio_state["is_paused"] = False
        
        start_time = time.time()
        elapsed_time = 0.0
        
        for note_idx in range(num_notes):
            if self._stop_event.is_set():
                print(f"[{self._iso_now()}] Music playback stopped by user")
                break
            
            while self.audio_state["is_paused"] and not self._stop_event.is_set():
                time.sleep(0.02)
                start_time = time.time() - elapsed_time
            
            if self._stop_event.is_set():
                break
            
            freq = frequencies[note_idx]
            duration_ms = durations[note_idx]
            
            if freq > 0 and freq < 20000:
                self.play_tone(freq)
                
                if progress_callback and note_idx % 10 == 0:
                    progress_callback({
                        "position": elapsed_time,
                        "note": note_idx + 1,
                        "total_notes": num_notes,
                        "frequency": round(freq, 2)
                    })
            
            target_end_time = start_time + elapsed_time + duration_ms / 1000.0
            
            check_interval = 0.02
            while time.time() < target_end_time:
                if self._stop_event.is_set():
                    break
                if self.audio_state["is_paused"]:
                    start_time += check_interval
                    break
                time.sleep(check_interval)
            
            elapsed_time = time.time() - start_time
        
        self.stop_tone()
        
        if not self._stop_event.is_set():
            print(f"[{self._iso_now()}] Music playback completed")
        else:
            print(f"[{self._iso_now()}] Music playback stopped by user")
        
        self.audio_state["is_playing"] = False
        self.audio_state["is_paused"] = False
        
        if progress_callback:
            progress_callback({"status": "finished"})
    
    def start_music_playback(self, frequencies: list, durations: list,
                             progress_callback=None) -> None:
        """Start music playback in a new thread.
        
        Args:
            frequencies: List of frequencies
            durations: List of durations
            progress_callback: Optional callback for progress updates
        """
        if self.audio_state["is_playing"]:
            self.stop_music_playback()
        
        self._playback_thread = threading.Thread(
            target=self.play_music_thread,
            args=(frequencies, durations, progress_callback),
            daemon=True
        )
        self._playback_thread.start()
    
    def start_music_playback_with_dance(self, frequencies: list, durations: list,
                                        enable_dance: bool = True,
                                        progress_callback=None) -> None:
        """Start music playback with dance actions in a new thread.
        
        根据每个音符的频率播放声音并执行相应的OTTO动作.
        
        Args:
            frequencies: List of frequencies
            durations: List of durations (in milliseconds)
            enable_dance: Whether to enable dance actions
            progress_callback: Optional callback for progress updates
        """
        if self.audio_state["is_playing"]:
            self.stop_music_playback()
        
        self._playback_thread = threading.Thread(
            target=self._play_music_with_dance_thread,
            args=(frequencies, durations, enable_dance, progress_callback),
            daemon=True
        )
        self._playback_thread.start()
    
    def _play_music_with_dance_thread(self, frequencies: list, durations: list,
                                      enable_dance: bool,
                                      progress_callback=None) -> None:
        """Internal thread function for music playback with dance actions.
        
        内部线程函数，用于音乐播放和动作同步.
        """
        if not frequencies or not durations:
            if progress_callback:
                progress_callback({"status": "error", "message": "Invalid song data"})
            return
        
        num_notes = min(len(frequencies), len(durations))
        
        self._stop_event.clear()
        self.audio_state["is_playing"] = True
        self.audio_state["is_paused"] = False
        
        start_time = time.time()
        elapsed_time = 0.0
        
        self.reset_stop_flag()
        last_freq = None
        
        for note_idx in range(num_notes):
            if self._stop_event.is_set():
                print(f"[{self._iso_now()}] Music playback stopped by user")
                self.stop_tone()
                self.go_home()
                return
            
            while self.audio_state["is_paused"] and not self._stop_event.is_set():
                time.sleep(0.02)
                start_time = time.time() - elapsed_time
            
            if self._stop_event.is_set():
                self.stop_tone()
                self.go_home()
                return
            
            freq = frequencies[note_idx]
            duration_ms = durations[note_idx]
            last_freq = freq
            
            if freq > 0 and freq < 20000:
                self.play_tone(freq)
                
                if progress_callback and note_idx % 10 == 0:
                    progress_callback({
                        "position": elapsed_time,
                        "note": note_idx + 1,
                        "total_notes": num_notes,
                        "frequency": round(freq, 2)
                    })
            
            if enable_dance:
                action_config = self.get_action_by_frequency(freq)
                if action_config:
                    action_name = action_config["action"]
                    params = action_config.get("params", {})
                    
                    self._execute_dance_action(action_name, params)
            
            target_end_time = start_time + elapsed_time + duration_ms / 1000.0
            
            check_interval = 0.02
            while time.time() < target_end_time:
                if self._stop_event.is_set():
                    self.stop_tone()
                    self.go_home()
                    return
                if self.audio_state["is_paused"]:
                    start_time += check_interval
                    break
                time.sleep(check_interval)
            
            elapsed_time = time.time() - start_time
        
        self.stop_tone()
        
        if not self._stop_event.is_set():
            print(f"[{self._iso_now()}] Music playback completed")
            self.go_home()  # Return to home position after playback
        
        self.audio_state["is_playing"] = False
        self.audio_state["is_paused"] = False
        
        if progress_callback:
            progress_callback({"status": "finished"})
    
    def _execute_dance_action(self, action_name: str, params: dict) -> None:
        """Execute a dance action based on the action name and parameters.
        
        Args:
            action_name: Name of the action to execute
            params: Dictionary of action parameters
        """
        try:
            if action_name == "home":
                self.go_home()
            elif action_name == "stop":
                self.stop_action()
            elif hasattr(self, action_name):
                action_method = getattr(self, action_name)
                action_method(**params)
        except Exception as e:
            print(f"[{self._iso_now()}] Error executing dance action {action_name}: {e}")
    
    def stop_music_playback(self) -> None:
        """Stop music playback and audio completely, return servos to home position."""
        self._stop_event.set()
        self.action_stop_flag = True
        if self._playback_thread:
            self._playback_thread.join(timeout=1)
        self.stop_tone()
        self.go_home()
        self.audio_state["is_playing"] = False
        self.audio_state["is_paused"] = False
    
    def pause_music_playback(self) -> None:
        """Pause/resume music playback."""
        if self.audio_state["is_playing"]:
            is_now_paused = not self.audio_state["is_paused"]
            self.audio_state["is_paused"] = is_now_paused
            
            if is_now_paused:
                self.stop_tone()
                print(f"[{self._iso_now()}] Music paused - sound stopped")
    
    # ==================== Basic Movements ====================
    
    def walk(self, steps: int = 2, T: int = 1000, direction: int = 1) -> dict:
        """
        Execute walking movement.
        
        Args:
            steps: Number of steps to take
            T: Period of each step in milliseconds
            direction: 1 for forward, -1 for backward
            
        Returns:
            dict: Action result with steps and direction
        """
        frames = self.otto.walk(steps=steps, T=T, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "walk", "steps": steps, "direction": direction}
    
    def turn(self, steps: int = 2, T: int = 1000, direction: int = 1) -> dict:
        """
        Execute turning movement.
        
        Args:
            steps: Number of turn steps
            T: Period of each step in milliseconds
            direction: 1 for left, -1 for right
            
        Returns:
            dict: Action result with steps and direction
        """
        frames = self.otto.turn(steps=steps, T=T, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "turn", "steps": steps, "direction": direction}
    
    # ==================== Dance Moves ====================
    
    def bend(self, steps: int = 1, T: int = 500, direction: int = 1) -> dict:
        """
        Bend movement (lean left or right).
        
        Args:
            steps: Number of bend cycles
            T: Period in milliseconds
            direction: 1 for left, -1 for right
        """
        frames = self.otto.bend(steps=steps, T=T, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "bend", "steps": steps, "direction": direction}
    
    def shake_leg(self, steps: int = 1, T: int = 1500, direction: int = 1) -> dict:
        """
        Shake leg movement.
        
        Args:
            steps: Number of shakes
            T: Period in milliseconds
            direction: 1 for left leg, -1 for right leg
        """
        frames = self.otto.shakeLeg(steps=steps, T=T, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "shakeLeg", "steps": steps, "direction": direction}
    
    def updown(self, steps: int = 2, T: int = 1500, height: int = 20) -> dict:
        """
        Up and down movement (body oscillation).
        
        Args:
            steps: Number of cycles
            T: Period in milliseconds
            height: Oscillation amplitude
        """
        frames = self.otto.updown(steps=steps, T=T, height=height)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "updown", "steps": steps, "height": height}
    
    def swing(self, steps: int = 2, T: int = 1000, height: int = 20) -> dict:
        """
        Swing movement (side to side).
        
        Args:
            steps: Number of swings
            T: Period in milliseconds
            height: Swing amplitude
        """
        frames = self.otto.swing(steps=steps, T=T, height=height)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "swing", "steps": steps, "height": height}
    
    def tiptoe_swing(self, steps: int = 2, T: int = 1000, height: int = 20) -> dict:
        """
        Tiptoe swing movement.
        
        Args:
            steps: Number of swings
            T: Period in milliseconds
            height: Swing amplitude
        """
        frames = self.otto.tiptoeSwing(steps=steps, T=T, height=height)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "tiptoeSwing", "steps": steps, "height": height}
    
    def jitter(self, steps: int = 2, T: int = 1000, height: int = 20) -> dict:
        """
        Jitter movement (fast small oscillations).
        
        Args:
            steps: Number of jitter cycles
            T: Period in milliseconds
            height: Jitter amplitude
        """
        frames = self.otto.jitter(steps=steps, T=T, height=height)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "jitter", "steps": steps, "height": height}
    
    def ascending_turn(self, steps: int = 2, T: int = 1000, height: int = 50) -> dict:
        """
        Ascending turn movement (turn while rising).
        
        Args:
            steps: Number of cycles
            T: Period in milliseconds
            height: Rise amplitude
        """
        frames = self.otto.ascendingTurn(steps=steps, T=T, height=height)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "ascendingTurn", "steps": steps, "height": height}
    
    def moonwalker(self, steps: int = 3, T: int = 1000, height: int = 25, direction: int = 1) -> dict:
        """
        Moonwalker movement (sliding gait).
        
        Args:
            steps: Number of steps
            T: Period in milliseconds
            height: Step height
            direction: 1 for left, -1 for right
        """
        frames = self.otto.moonwalker(steps=steps, T=T, height=height, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "moonwalker", "steps": steps, "height": height, "direction": direction}
    
    def crusaito(self, steps: int = 2, T: int = 1000, height: int = 20, direction: int = 1) -> dict:
        """
        Crusaito movement (side step).
        
        Args:
            steps: Number of steps
            T: Period in milliseconds
            height: Step height
            direction: 1 for left, -1 for right
        """
        frames = self.otto.crusaito(steps=steps, T=T, height=height, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "crusaito", "steps": steps, "height": height, "direction": direction}
    
    def flapping(self, steps: int = 2, T: int = 1000, height: int = 20, direction: int = 1) -> dict:
        """
        Flapping movement (wing-like motion).
        
        Args:
            steps: Number of flaps
            T: Period in milliseconds
            height: Flap amplitude
            direction: 1 for forward, -1 for backward
        """
        frames = self.otto.flapping(steps=steps, T=T, height=height, direction=direction)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "flapping", "steps": steps, "height": height, "direction": direction}
    
    def jump(self, steps: int = 1, T: int = 2000) -> dict:
        """
        Jump movement.
        
        Args:
            steps: Number of jumps
            T: Period in milliseconds
        """
        frames = self.otto.jump(steps=steps, T=T)
        self.execute_servo_frames(frames)
        
        if not self.action_stop_flag:
            self.go_home()
            
        return {"action": "jump", "steps": steps}
    
    # ==================== Dance Presets ====================
    
    DANCE_SEQUENCES = {
        "happy": [
            {'action': 'swing', 'steps': 3, 'T': 700, 'height': 20},
            {'action': 'home'},
            {'action': 'walk', 'steps': 3, 'T': 900, 'direction': 1},
            {'action': 'walk', 'steps': 3, 'T': 900, 'direction': -1},
            {'action': 'tiptoeSwing', 'steps': 3, 'T': 500, 'height': 20},
            {'action': 'home'}
        ],
        "dance": [
            {'action': 'moonwalker', 'steps': 4, 'T': 900, 'height': 25, 'direction': 1},
            {'action': 'moonwalker', 'steps': 4, 'T': 900, 'height': 25, 'direction': -1},
            {'action': 'crusaito', 'steps': 3, 'T': 900, 'height': 20, 'direction': 1},
            {'action': 'crusaito', 'steps': 3, 'T': 900, 'height': 20, 'direction': -1},
            {'action': 'flapping', 'steps': 3, 'T': 900, 'height': 20, 'direction': 1},
            {'action': 'home'}
        ],
        "greeting": [
            {'action': 'swing', 'steps': 2, 'T': 700, 'height': 30},
            {'action': 'bend', 'steps': 2, 'T': 500, 'direction': 1},
            {'action': 'bend', 'steps': 2, 'T': 500, 'direction': -1},
            {'action': 'walk', 'steps': 3, 'T': 900, 'direction': 1},
            {'action': 'home'}
        ]
    }

    def execute_dance_sequence(self, preset: str, progress_callback=None) -> dict:
        """
        Execute a predefined dance sequence.
        
        Args:
            preset: Name of dance preset ("happy", "dance", "greeting")
            progress_callback: Optional callback(step, action) for progress updates
            
        Returns:
            dict: Result with preset name and completed steps
        """
        sequence = self.DANCE_SEQUENCES.get(preset, [{'action': 'home'}])
        self.reset_stop_flag()
        
        current_step = 0
        for action_dict in sequence:
            if self.action_stop_flag:
                print(f"[{self._iso_now()}] Dance stopped by user")
                break
            
            action_name = action_dict.get('action', 'home')
            
            # Execute action
            if action_name == "home":
                self.go_home()
            else:
                self._execute_action_dict(action_dict)
                if not self.action_stop_flag:
                    self.go_home()
            
            current_step += 1
            
            # Report progress
            if progress_callback:
                progress_callback(current_step, action_name)
        
        return {
            "preset": preset,
            "completed_steps": current_step,
            "stopped": self.action_stop_flag
        }
    
    def _execute_action_dict(self, action_dict: dict) -> None:
        """
        Execute an action from a dictionary specification.
        
        Args:
            action_dict: Dictionary with action parameters
        """
        action = action_dict.get('action')
        steps = action_dict.get('steps', 1)
        T = action_dict.get('T', 1000)
        direction = action_dict.get('direction', 1)
        height = action_dict.get('height', 20)
        
        action_map = {
            'walk': lambda: self.walk(steps, T, direction),
            'turn': lambda: self.turn(steps, T, direction),
            'bend': lambda: self.bend(steps, T, direction),
            'shakeLeg': lambda: self.shake_leg(steps, T, direction),
            'updown': lambda: self.updown(steps, T, height),
            'swing': lambda: self.swing(steps, T, height),
            'tiptoeSwing': lambda: self.tiptoe_swing(steps, T, height),
            'jitter': lambda: self.jitter(steps, T, height),
            'ascendingTurn': lambda: self.ascending_turn(steps, T, height),
            'moonwalker': lambda: self.moonwalker(steps, T, height, direction),
            'crusaito': lambda: self.crusaito(steps, T, height, direction),
            'flapping': lambda: self.flapping(steps, T, height, direction),
            'jump': lambda: self.jump(steps, T),
        }
        
        if action in action_map:
            action_map[action]()


    def execute_dance_sequence_from_list(self, sequence: list, progress_callback=None) -> dict:
        """
        Execute a dance sequence from a list of action dictionaries.
        
        Args:
            sequence: List of action dictionaries
            progress_callback: Optional callback(step, action) for progress updates
            
        Returns:
            dict: Result with completed steps and stopped status
        """
        self.reset_stop_flag()
        
        current_step = 0
        for action_dict in sequence:
            if self.action_stop_flag:
                print(f"[{self._iso_now()}] Dance stopped by user")
                break
            
            action_name = action_dict.get('action', 'home')
            
            if action_name == "home":
                self.go_home()
            else:
                self._execute_action_dict(action_dict)
                if not self.action_stop_flag:
                    self.go_home()
            
            current_step += 1
            
            if progress_callback:
                progress_callback(current_step, action_name)
        
        return {
            "completed_steps": current_step,
            "stopped": self.action_stop_flag
        }


# Global controller instance
_otto_controller = None


def get_controller() -> OttoController:
    """
    Get or create the global OttoController instance.
    
    Returns:
        OttoController: The singleton controller instance
    """
    global _otto_controller
    if _otto_controller is None:
        _otto_controller = OttoController()
    return _otto_controller
