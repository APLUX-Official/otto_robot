# OttoControlWebVoice

一个基于 Arduino UNO Q 开发板的双足机器人控制系统，支持Web界面控制、语音指令、音乐同步舞蹈等功能。

## 项目概述

本项目实现了一个功能完整的 Otto 机器人控制系统，具有以下特点：

- **Web 界面控制**：通过浏览器实时控制机器人动作
- **语音指令**：支持语音控制机器人执行预设动作
- **音乐同步**：机器人可以跟随音乐节拍跳舞
- **丰富的动作库**：包含行走、转弯、跳跃、月球漫步等多种动作
- **自定义动作序列**：支持创建和执行自定义舞蹈序列

## 硬件组件

| 组件 | 数量 | 型号 | 用途 |
|------|------|------|------|
| 舵机 | 4 | DS3115 | 控制机器人腿部运动（左髋、右髋、左脚踝、右脚踝） |
| 拓展板 | 1 | 自定义 | 连接电池供电，拓展舵机连接IO口等其他连接和供电 |
| 开发板 | 1 | Arduino UNO Q | 核心控制器，运行机器人控制代码 |
| USB 线缆 | 1 | USB-C® to USB-A | 连接开发板与计算机 |
| 超声波传感器 | 1 | HC-SR04 | 障碍物检测（可选） |
| 电池 | 1 | 12V 2800mAh锂电池 | 为机器人供电 |
| C to C数据线 | 1 | 自定义 | 连接拓展板和开发板 |
| 外壳 | 1 | 自定义 | 基于OTTO模型的全部打印件[上盖、下盖、开关、电池盖板、左髋、右髋、左脚踝、右脚踝] |
| 螺蛳 | * | 自定义 | 用于组装机器人全部零件 |

## 软件要求

- Arduino App Lab
- Python 3.13+
- 现代Web浏览器（Chrome、Firefox、Edge等）

## 核心算法

### 1. 双足机器人重心转移原理

Otto 机器人采用四舵机结构实现双足行走，核心原理是通过**重心转移**实现稳定运动：

- **髋关节控制**：通过左右髋关节（YL、YR）的交替摆动，实现腿部前后运动
- **踝关节控制**：通过左右踝关节（RL、RR）的上下运动，调整机器人重心
- **相位协调**：髋关节和踝关节运动存在相位差，确保行走时重心始终在支撑腿上方

**关键算法**：在 `otto_core.py` 中通过 `_execute_oscillation` 方法实现，使用正弦波控制舵机运动轨迹。

### 2. 振荡器算法生成平滑舞蹈动作曲线

项目使用**正弦振荡器**生成平滑的周期性运动，确保动作自然流畅：

```python
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
```

**工作原理**：
- 使用正弦函数生成平滑的周期性运动轨迹
- 通过调整振幅、偏移量和相位差，实现不同类型的动作
- 采用固定采样率（30ms）确保动作流畅度

### 3. Otto 库文件深度解析

#### 核心功能模块

1. **基础动作**：行走、转弯、归位等基本运动
2. **舞蹈动作**：摆动、抖动、月球漫步等复杂动作
3. **动作序列**：支持组合多个动作形成舞蹈
4. **舵机控制**：精确控制四个舵机的角度

#### 自定义动作序列

通过 `create_action_sequence` 函数可以创建自定义动作序列：

```python
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
```

**使用示例**：

```python
# 自定义舞蹈序列
custom_sequence = [
    {'action': 'walk', 'steps': 2, 'T': 1000, 'direction': 1},
    {'action': 'swing', 'steps': 3, 'T': 800, 'height': 25},
    {'action': 'moonwalker', 'steps': 2, 'T': 900, 'height': 25, 'direction': 1},
    {'action': 'jump', 'steps': 1, 'T': 1500}
]

# 创建并执行序列
frames = create_action_sequence(custom_sequence)
```

### 4. Web 页面输出音符频率与动作节拍同步代码

项目支持音乐与动作同步，通过以下机制实现：

#### 音乐解析与节拍检测

在 `assets/app.js` 中，通过 `loadMusicFile` 函数加载音乐文件并解析节拍：

```javascript
function loadMusicFile(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioContext.decodeAudioData(e.target.result, function(buffer) {
            analyzeMusic(buffer);
        });
    };
    reader.readAsArrayBuffer(file);
}

function analyzeMusic(audioBuffer) {
    // 提取音频特征
    // 检测节拍点
    // 生成动作触发时间
}
```

#### 动作与音乐同步

通过 `syncActionWithMusic` 函数实现动作与音乐节拍的同步：

```javascript
function syncActionWithMusic(actionName, beatTimes) {
    beatTimes.forEach((beatTime, index) => {
        setTimeout(() => {
            executeAction(actionName);
        }, beatTime * 1000);
    });
}
```

#### 音符频率输出

Web 界面可以显示当前播放音符的频率，并根据频率变化触发不同动作：

```javascript
function updateNoteFrequency(frequency) {
    document.getElementById('note-frequency').textContent = `当前频率: ${Math.round(frequency)}Hz`;
    
    // 根据频率范围选择动作
    if (frequency > 800) {
        // 高频：快速动作
        executeAction('jitter', { steps: 1, T: 400, height: 15 });
    } else if (frequency > 400) {
        // 中频：中等速度动作
        executeAction('swing', { steps: 1, T: 800, height: 20 });
    } else {
        // 低频：缓慢动作
        executeAction('updown', { steps: 1, T: 1200, height: 15 });
    }
}
```

## 项目结构

```
OttoControlWebVoice/
├── assets/            # 前端资源
│   ├── index.html     # 主页面
│   ├── app.js         # 前端逻辑
│   ├── style.css      # 样式文件
│   ├── music/         # 音乐文件
│   └── img/           # 图片资源
├── python/            # Python 后端
│   ├── main.py        # 主程序
│   ├── otto_core.py   # 核心算法
│   └── otto_controller.py # 控制器
├── sketch/            # Arduino 代码
│   └── sketch.ino     # 主草图
├── app.yaml           # 应用配置
├── OTTO_ACTIONS.md    # 动作文档
└── README.md          # 项目说明
```

## 快速开始

### 1. 硬件连接

1. 将 4 个 DS3115 舵机连接到 Arduino UNO Q 开发板：
   - 左髋关节 (YL) → D3
   - 右髋关节 (YR) → D5
   - 左脚踝 (RL) → D6
   - 右脚踝 (RR) → D9

2. 连接 USB 线缆到开发板和计算机

### 2. 软件设置

1. 打开 Arduino App Lab
2. 加载项目文件夹 `OttoControlWebVoice`
3. 编译并上传 Arduino 草图到开发板
4. 点击Run按钮运行程序：


### 3. 访问控制界面

1. 打开浏览器，访问 `http://localhost:8000`
2. 点击 "连接" 按钮连接到机器人
3. 使用 "快速动作" 按钮测试基本动作
4. 使用内置音乐文件测试音乐同步功能

## 动作列表

| 动作名称 | 描述 | 参数 |
|---------|------|------|
| walk | 行走 | steps, T, direction |
| turn | 转向 | steps, T, direction |
| bend | 侧弯 | steps, T, direction |
| shakeLeg | 摇腿 | steps, T, direction |
| updown | 上下移动 | steps, T, height |
| swing | 摆动 | steps, T, height |
| tiptoeSwing | 踮脚摆动 | steps, T, height |
| jitter | 抖动 | steps, T, height |
| ascendingTurn | 上升旋转 | steps, T, height |
| moonwalker | 月球漫步 | steps, T, height, direction |
| crusaito | 滑翔 | steps, T, height, direction |
| flapping | 拍打 | steps, T, height, direction |
| jump | 跳跃 | steps, T |
| home | 归位 | 无 |

## 预设舞蹈

### happy - 快乐舞蹈
- 摇摆 → 前进 → 后退 → 踮脚摇摆 → 归位

### dance - 舞蹈
- 左滑步 → 右滑步 → 左滑翔 → 右滑翔 → 拍打 → 归位

### greeting - 问候
- 摇摆 → 左弯 → 右弯 → 前进 → 归位

## 技术细节

### 通信协议

- **前端 → 后端**：WebSocket (Socket.IO) 实时通信
- **后端 → 硬件**：通过 Arduino_RouterBridge 发送舵机控制命令

### 安全特性

- 舵机角度自动限制在 0-180 度范围
- 动作参数范围检查，防止过度运动
- 线程安全设计，避免动作冲突

### 性能优化

- 动作帧预计算，减少实时计算负担
- 固定采样率确保动作流畅度
- 舵机角度变化小于 2 度时不发送命令，减少通信量

## 扩展功能

### 语音控制

项目支持通过 Web Speech API 实现语音控制：

1. 点击 "语音控制" 按钮
2. 说出预设指令，如 "行走"、"跳跃"、"停止"
3. 机器人将执行对应动作

### 自定义音乐舞蹈

1. 上传音乐文件（支持 MP3 格式）
2. 点击 "分析音乐" 按钮检测节拍
3. 选择动作映射方案
4. 点击 "开始同步" 按钮启动音乐舞蹈

## 故障排除

### 常见问题

1. **舵机不响应**：检查接线是否正确，确保电源充足
2. **动作不协调**：可能需要校准舵机中立位置
3. **Web 界面无响应**：检查 Python 后端是否运行，网络连接是否正常
4. **音乐不同步**：尝试使用节奏明显的音乐，确保音量适中

---

**享受控制你的 Otto 机器人！** 🤖🎵