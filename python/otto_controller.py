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

Dependencies:
    - otto_core: Core movement algorithms
    - arduino.app_utils.Bridge: Hardware communication
"""

import time
from datetime import datetime, UTC
from otto_core import OttoCore
from arduino.app_utils import Bridge


class OttoController:
    """
    OTTO Robot Motion Controller
    
    Manages all robot movements and dance sequences.
    Provides a clean interface for executing actions and handling servo controls.
    
    Attributes:
        otto (OttoCore): Core movement algorithm instance
        servo_pins (list): List of servo pin names [D3, D5, D6, D9]
        servo_names (dict): Mapping of pin to human-readable names
        servo_states (dict): Current angle of each servo
        action_stop_flag (bool): Flag to stop current action
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
        """Initialize OTTO controller with default states."""
        self.otto = OttoCore()
        self.servo_states = {pin: 90 for pin in self.SERVO_PINS}
        self.action_stop_flag = False
        
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
            {'action': 'jitter', 'steps': 2, 'T': 600, 'height': 30},
            {'action': 'crusaito', 'steps': 3, 'T': 900, 'height': 20, 'direction': 1},
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
