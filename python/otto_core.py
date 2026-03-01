# -*- coding: utf-8 -*-
"""
Otto Core - 硬件无关的核心算法库
用于Arduino UNO Q双核控制器的Otto机器人复刻项目

功能：
- 提取移动控制算法（行走、转弯、跳跃等）
- 提取舞蹈动作算法（月球漫步、滑翔、拍打等）
- 输出四个舵机角度值 [YL, YR, RL, RR]

作者：Otto DIY Community
版本：1.0.0
"""

import math
import time
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


# 常量定义
FORWARD = 1
BACKWARD = -1
LEFT = 1
RIGHT = -1

SMALL = 5
MEDIUM = 15
BIG = 30

HOME_POSITION = [90, 90, 90, 90]

SERVO_COUNT = 4


def deg2rad(degrees: float) -> float:
    """角度转弧度"""
    return (degrees * math.pi) / 180


@dataclass
class ServoAngles:
    """舵机角度数据类"""
    yl: int  # 左髋关节 (Left Hip)
    yr: int  # 右髋关节 (Right Hip)
    rl: int  # 左脚踝 (Left Ankle)
    rr: int  # 右脚踝 (Right Ankle)
    
    def to_list(self) -> List[int]:
        """转换为列表格式"""
        return [self.yl, self.yr, self.rl, self.rr]
    
    def to_dict(self) -> Dict[str, int]:
        """转换为字典格式"""
        return {
            'YL': self.yl,
            'YR': self.yr,
            'RL': self.rl,
            'RR': self.rr
        }


class Oscillator:
    """
    正弦振荡器类
    用于生成平滑的周期性运动
    
    参数说明：
    - A: 振幅（度）
    - O: 偏移量（度）
    - T: 周期（毫秒）
    - phase: 相位（弧度）
    """
    
    def __init__(self, trim: float = 0.0):
        self._A = 0.0
        self._O = 0.0
        self._T = 2000.0
        self._phase0 = 0.0
        self._trim = trim
        self._phase = 0.0
        self._pos = 90.0
        self._rev = False
        
        # 计算采样参数
        self._TS = 30  # 采样周期（毫秒）
        self._update_period_params()
    
    def _update_period_params(self):
        """更新周期参数"""
        self._N = self._T / self._TS
        self._inc = 2 * math.pi / self._N
    
    def SetA(self, A: float):
        """设置振幅"""
        self._A = A
    
    def SetO(self, O: float):
        """设置偏移量"""
        self._O = O
    
    def SetT(self, T: float):
        """设置周期（毫秒）"""
        self._T = T
        self._update_period_params()
    
    def SetPh(self, phase: float):
        """设置相位（弧度）"""
        self._phase0 = phase
    
    def SetTrim(self, trim: float):
        """设置校准偏移"""
        self._trim = trim
    
    def SetPosition(self, position: float):
        """设置位置（已校准）"""
        self._pos = position + self._trim
    
    def refresh(self, current_time: float = None) -> float:
        """
        刷新振荡器状态并返回当前位置
        模拟实时采样
        """
        if current_time is None:
            current_time = time.time() * 1000
        
        pos = self._A * math.sin(self._phase + self._phase0) + self._O
        
        if self._rev:
            pos = -pos
        
        self._pos = round(pos) + 90 + self._trim
        self._pos = max(0, min(180, self._pos))  # 限制在0-180度范围内
        
        self._phase += self._inc
        return self._pos


class OttoCore:
    """
    Otto机器人核心控制类
    
    舵机索引：
    0 - YL (左髋关节)
    1 - YR (右髋关节)
    2 - RL (左脚踝)
    3 - RR (右脚踝)
    """
    
    def __init__(self, servo_trim: List[float] = None):
        """
        初始化Otto核心
        
        参数：
        - servo_trim: 舵机校准值列表 [YL, YR, RL, RR]
        """
        self._oscillators = [Oscillator() for _ in range(SERVO_COUNT)]
        self._servo_trim = servo_trim or [0, 0, 0, 0]
        
        for i in range(SERVO_COUNT):
            self._oscillators[i].SetTrim(self._servo_trim[i])
        
        self._position = HOME_POSITION.copy()
        self._rest_state = True
        self._current_action = None
    
    def home(self) -> ServoAngles:
        """
        返回HOME位置
        所有舵机回到90度
        """
        self._position = HOME_POSITION.copy()
        self._rest_state = True
        return ServoAngles(90, 90, 90, 90)
    
    def _execute_oscillation(self, A: List[float], O: List[float], 
                           T: float, phase_diff: List[float], 
                           steps: float = 1.0,
                           sample_rate: float = 30) -> List[ServoAngles]:
        """
        执行振荡运动
        
        参数：
        - A: 各舵机振幅列表
        - O: 各舵机偏移量列表
        - T: 周期（毫秒）
        - phase_diff: 相位差列表
        - steps: 步数
        - sample_rate: 采样率（毫秒）
        
        返回：
        - 动作帧列表
        """
        frames = []
        
        # 设置振荡器参数
        for i in range(SERVO_COUNT):
            self._oscillators[i].SetA(A[i])
            self._oscillators[i].SetO(O[i])
            self._oscillators[i].SetT(T)
            self._oscillators[i].SetPh(phase_diff[i])
        
        # 计算总帧数
        total_samples = int((T * steps) / sample_rate)
        
        for i in range(total_samples):
            angles = []
            for j in range(SERVO_COUNT):
                pos = self._oscillators[j].refresh()
                angles.append(int(pos))
            frame = ServoAngles(angles[0], angles[1], angles[2], angles[3])
            frames.append(frame)
            self._position = angles
        
        self._rest_state = False
        return frames
    
    def walk(self, steps: int = 2, T: int = 1000, direction: int = FORWARD) -> List[ServoAngles]:
        """
        行走动作（前進或後退）
        
        参数：
        - steps: 步数
        - T: 周期（毫秒），值越大速度越慢（600-1400）
        - direction: FORWARD(1) 或 BACKWARD(-1)
        
        返回：
        - 动作帧列表
        """
        A = [30, 30, 15, 15]
        O = [0, 0, 4, -4]
        phase_diff = [0, 0, deg2rad(direction * -90), deg2rad(direction * -90)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def turn(self, steps: int = 2, T: int = 1000, direction: int = LEFT) -> List[ServoAngles]:
            """
            转向动作（左转或右转）
            
            参数：
            - steps: 步数
            - T: 周期（毫秒）
            - direction: LEFT(1) 或 RIGHT(-1)
            
            返回：
            - 动作帧列表
            """
            A = [30, 30, 15, 15]
            O = [0, 0, 4, -4]
            phase_diff = [0, 0, deg2rad(-90), deg2rad(-90)]
            
            if direction == LEFT:
                A[0] = 35
                A[1] = 5
            else:
                A[0] = 5
                A[1] = 35
            
            return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def bend(self, steps: int = 1, T: int = 500, direction: int = LEFT) -> List[ServoAngles]:
        """
        侧弯动作
        
        参数：
        - steps: 弯曲次数
        - T: 周期（毫秒）
        - direction: LEFT(1) 或 RIGHT(-1)
        
        返回：
        - 关键帧列表
        """
        frames = []
        
        if direction == LEFT:
            bend1 = [90, 90, 40, 35]
            bend2 = [90, 90, 40, 105]
        else:
            bend1 = [90, 90, 140, 80]
            bend2 = [90, 90, 75, 120]
        
        homes = HOME_POSITION
        
        T2 = 800
        
        for _ in range(steps):
            frames.append(ServoAngles(*bend1))
            frames.append(ServoAngles(*bend2))
            frames.append(ServoAngles(*homes))
        
        return frames
    
    def shakeLeg(self, steps: int = 1, T: int = 1500, direction: int = LEFT) -> List[ServoAngles]:
        """
        摇腿动作
        
        参数：
        - steps: 摇动次数
        - T: 周期（毫秒）
        - direction: LEFT(1) 或 RIGHT(-1)
        
        返回：
        - 关键帧列表
        """
        frames = []
        
        if direction == LEFT:
            shake_leg1 = [90, 90, 40, 35]
            shake_leg2 = [90, 90, 40, 120]
            shake_leg3 = [90, 90, 70, 60]
        else:
            shake_leg1 = [90, 90, 140, 35]
            shake_leg2 = [90, 90, 40, 140]
            shake_leg3 = [90, 90, 120, 58]
        
        homes = HOME_POSITION
        
        T2 = 1000
        numberLegMoves = 2
        
        T_remaining = max(T - T2, 200 * numberLegMoves)
        
        for _ in range(steps):
            frames.append(ServoAngles(*shake_leg1))
            frames.append(ServoAngles(*shake_leg2))
            
            for _ in range(numberLegMoves):
                frames.append(ServoAngles(*shake_leg3))
                frames.append(ServoAngles(*shake_leg2))
                frames.append(ServoAngles(*homes))
        
        return frames
    
    def updown(self, steps: int = 2, T: int = 1500, height: int = 20) -> List[ServoAngles]:
        """
        上下移动（跳跃前进）
        
        参数：
        - steps: 跳跃次数
        - T: 周期（毫秒）
        - height: 高度（0-90度）
        
        返回：
        - 动作帧列表
        """
        A = [0, 0, height, height]
        O = [0, 0, height, -height]
        phase_diff = [0, 0, deg2rad(-90), deg2rad(90)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def swing(self, steps: int = 2, T: int = 1000, height: int = 20) -> List[ServoAngles]:
        """
        摆动（左右摇摆）
        
        参数：
        - steps: 摆动次数
        - T: 周期（毫秒）
        - height: 摆动幅度（0-50度）
        
        返回：
        - 动作帧列表
        """
        A = [0, 0, height, height]
        O = [0, 0, height / 2, -height / 2]
        phase_diff = [0, 0, 0, 0]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def tiptoeSwing(self, steps: int = 2, T: int = 1000, height: int = 20) -> List[ServoAngles]:
        """
        踮脚摆动
        
        参数：
        - steps: 摆动次数
        - T: 周期（毫秒）
        - height: 摆动幅度（0-50度）
        
        返回：
        - 动作帧列表
        """
        A = [0, 0, height, height]
        O = [0, 0, height, -height]
        phase_diff = [0, 0, 0, 0]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def jitter(self, steps: int = 2, T: int = 1000, height: int = 20) -> List[ServoAngles]:
        """
        抖动动作
        
        参数：
        - steps: 抖动次数
        - T: 周期（毫秒）
        - height: 抖动幅度（5-25度）
        
        返回：
        - 动作帧列表
        """
        height = min(25, height)
        A = [height, height, 0, 0]
        O = [0, 0, 0, 0]
        phase_diff = [deg2rad(-90), deg2rad(90), 0, 0]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def ascendingTurn(self, steps: int = 2, T: int = 1000, height: int = 50) -> List[ServoAngles]:
        """
        上升旋转
        
        参数：
        - steps: 旋转次数
        - T: 周期（毫秒）
        - height: 高度（5-15度）
        
        返回：
        - 动作帧列表
        """
        height = min(13, height)
        A = [height, height, height, height]
        O = [0, 0, height + 4, -height + 4]
        phase_diff = [deg2rad(-90), deg2rad(90), deg2rad(-90), deg2rad(90)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def moonwalker(self, steps: int = 3, T: int = 1000, height: int = 25, 
                  direction: int = LEFT) -> List[ServoAngles]:
        """
        月球漫步（迈克尔杰克逊风格）
        
        参数：
        - steps: 步数
        - T: 周期（毫秒）
        - height: 高度（15-40度）
        - direction: LEFT(1) 或 RIGHT(-1)
        
        返回：
        - 动作帧列表
        """
        A = [0, 0, height, height]
        O = [0, 0, height / 2 + 2, -height / 2 - 2]
        phi = -direction * 90
        phase_diff = [0, 0, deg2rad(phi), deg2rad(-60 * direction + phi)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def crusaito(self, steps: int = 2, T: int = 1000, height: int = 20,
                direction: int = LEFT) -> List[ServoAngles]:
        """
        滑翔动作（月球漫步与行走的混合）
        
        参数：
        - steps: 步数
        - T: 周期（毫秒）
        - height: 高度（20-50度）
        - direction: LEFT(1) 或 RIGHT(-1)
        
        返回：
        - 动作帧列表
        """
        A = [25, 25, height, height]
        O = [0, 0, height / 2 + 4, -height / 2 - 4]
        phase_diff = [deg2rad(90), deg2rad(90), 0, deg2rad(-60 * direction)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def flapping(self, steps: int = 2, T: int = 1000, height: int = 20,
                direction: int = FORWARD) -> List[ServoAngles]:
        """
        拍打动作
        
        参数：
        - steps: 拍打次数
        - T: 周期（毫秒）
        - height: 高度（10-30度）
        - direction: FORWARD(1) 或 BACKWARD(-1)
        
        返回：
        - 动作帧列表
        """
        A = [12, 12, height, height]
        O = [0, 0, height - 10, -height + 10]
        phase_diff = [0, deg2rad(180), deg2rad(-90 * direction), deg2rad(90 * direction)]
        
        return self._execute_oscillation(A, O, T, phase_diff, steps)
    
    def jump(self, steps: int = 1, T: int = 2000) -> List[ServoAngles]:
        """
        跳跃动作
        
        参数：
        - steps: 跳跃次数
        - T: 周期（毫秒）
        
        返回：
        - 关键帧列表
        """
        frames = []
        
        up = [90, 90, 150, 30]
        down = HOME_POSITION
        
        for _ in range(steps):
            frames.append(ServoAngles(*up))
            frames.append(ServoAngles(*down))
        
        return frames
    
    def get_position(self) -> ServoAngles:
        """获取当前位置"""
        return ServoAngles(*self._position)
    
    def set_trim(self, servo_idx: int, trim_value: float):
        """
        设置舵机校准值
        
        参数：
        - servo_idx: 舵机索引（0-3）
        - trim_value: 校准值
        """
        if 0 <= servo_idx < SERVO_COUNT:
            self._oscillators[servo_idx].SetTrim(trim_value)
    
    def get_trim(self, servo_idx: int) -> float:
        """
        获取舵机校准值
        
        参数：
        - servo_idx: 舵机索引（0-3）
        
        返回：
        - 校准值
        """
        if 0 <= servo_idx < SERVO_COUNT:
            return self._oscillators[servo_idx]._trim
        return 0
    
    def get_action_frames(self, action_name: str, **kwargs) -> List[ServoAngles]:
        """
        获取指定动作的所有帧
        
        参数：
        - action_name: 动作名称
        - **kwargs: 动作参数
        
        返回：
        - 动作帧列表
        """
        action_methods = {
            'walk': lambda: self.walk(kwargs.get('steps', 2), 
                                    kwargs.get('T', 1000), 
                                    kwargs.get('direction', FORWARD)),
            'turn': lambda: self.turn(kwargs.get('steps', 2),
                                     kwargs.get('T', 1000),
                                     kwargs.get('direction', LEFT)),
            'bend': lambda: self.bend(kwargs.get('steps', 1),
                                     kwargs.get('T', 500),
                                     kwargs.get('direction', LEFT)),
            'shakeLeg': lambda: self.shakeLeg(kwargs.get('steps', 1),
                                             kwargs.get('T', 1500),
                                             kwargs.get('direction', LEFT)),
            'updown': lambda: self.updown(kwargs.get('steps', 2),
                                         kwargs.get('T', 1500),
                                         kwargs.get('height', 20)),
            'swing': lambda: self.swing(kwargs.get('steps', 2),
                                       kwargs.get('T', 1000),
                                       kwargs.get('height', 20)),
            'tiptoeSwing': lambda: self.tiptoeSwing(kwargs.get('steps', 2),
                                                   kwargs.get('T', 1000),
                                                   kwargs.get('height', 20)),
            'jitter': lambda: self.jitter(kwargs.get('steps', 2),
                                         kwargs.get('T', 1000),
                                         kwargs.get('height', 20)),
            'ascendingTurn': lambda: self.ascendingTurn(kwargs.get('steps', 2),
                                                       kwargs.get('T', 1000),
                                                       kwargs.get('height', 50)),
            'moonwalker': lambda: self.moonwalker(kwargs.get('steps', 3),
                                                 kwargs.get('T', 1000),
                                                 kwargs.get('height', 25),
                                                 kwargs.get('direction', LEFT)),
            'crusaito': lambda: self.crusaito(kwargs.get('steps', 2),
                                              kwargs.get('T', 1000),
                                              kwargs.get('height', 20),
                                              kwargs.get('direction', LEFT)),
            'flapping': lambda: self.flapping(kwargs.get('steps', 2),
                                             kwargs.get('T', 1000),
                                             kwargs.get('height', 20),
                                             kwargs.get('direction', FORWARD)),
            'jump': lambda: self.jump(kwargs.get('steps', 1),
                                     kwargs.get('T', 2000)),
            'home': lambda: [self.home()]
        }
        
        if action_name in action_methods:
            return action_methods[action_name]()
        return [self.home()]


def create_action_sequence(actions: List[Dict]) -> List[Tuple[ServoAngles, int]]:
    """
    创建动作序列
    
    参数：
    - actions: 动作字典列表，每个字典包含：
        - action: 动作名称
        - steps: 步数（可选）
        - T: 周期（可选）
        - direction: 方向（可选）
        - height: 高度（可选）
    
    返回：
    - (动作帧, 持续时间) 元组列表
    """
    otto = OttoCore()
    sequence = []
    
    for action_dict in actions:
        action_name = action_dict.get('action', 'home')
        frames = otto.get_action_frames(action_name, **action_dict)
        duration = action_dict.get('T', 1000) * action_dict.get('steps', 1)
        sequence.append((frames, duration))
    
    return sequence


# 预设舞蹈动作序列
DANCE_SEQUENCES = {
    'happy': [
        {'action': 'swing', 'steps': 2, 'T': 800, 'height': 20},
        {'action': 'home'},
        {'action': 'walk', 'steps': 2, 'T': 1000, 'direction': FORWARD},
        {'action': 'walk', 'steps': 2, 'T': 1000, 'direction': BACKWARD},
        {'action': 'tiptoeSwing', 'steps': 2, 'T': 500, 'height': 20},
        {'action': 'home'}
    ],
    
    'dance': [
        {'action': 'moonwalker', 'steps': 3, 'T': 1000, 'height': 25, 'direction': LEFT},
        {'action': 'moonwalker', 'steps': 3, 'T': 1000, 'height': 25, 'direction': RIGHT},
        {'action': 'crusaito', 'steps': 2, 'T': 1000, 'height': 20, 'direction': LEFT},
        {'action': 'crusaito', 'steps': 2, 'T': 1000, 'height': 20, 'direction': RIGHT},
        {'action': 'flapping', 'steps': 2, 'T': 1000, 'height': 20, 'direction': FORWARD},
        {'action': 'home'}
    ],
    
    'greeting': [
        {'action': 'swing', 'steps': 1, 'T': 800, 'height': 30},
        {'action': 'bend', 'steps': 1, 'T': 500, 'direction': LEFT},
        {'action': 'bend', 'steps': 1, 'T': 500, 'direction': RIGHT},
        {'action': 'walk', 'steps': 2, 'T': 1000, 'direction': FORWARD},
        {'action': 'home'}
    ]
}


if __name__ == '__main__':
    otto = OttoCore()
    
    print("=== Otto Core 算法测试 ===")
    print(f"HOME位置: {otto.home().to_list()}")
    
    print("\n测试行走动作...")
    walk_frames = otto.walk(steps=1, T=1000, direction=FORWARD)
    print(f"行走帧数: {len(walk_frames)}, 前3帧: {[f.to_list() for f in walk_frames[:3]]}")
    
    print("\n测试月球漫步...")
    moonwalk_frames = otto.moonwalker(steps=1, T=1000, height=25, direction=LEFT)
    print(f"月球漫步帧数: {len(moonwalk_frames)}")
    
    print("\n测试跳跃...")
    jump_frames = otto.jump(steps=1, T=2000)
    print(f"跳跃帧数: {len(jump_frames)}, 帧: {[f.to_list() for f in jump_frames]}")
    
    print("\n=== 测试完成 ===")
