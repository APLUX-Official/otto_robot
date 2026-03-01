# OTTO Robot Actions Documentation

## 概述

本文档详细描述了 OTTO 机器人的所有可用动作及其参数。

### 舵机配置

OTTO 机器人使用 4 个舵机控制运动：

| 舵机 | 引脚 | 名称 | 说明 |
|------|------|------|------|
| YL | D3 | 左髋关节 | 控制左腿前后摆动 |
| YR | D5 | 右髋关节 | 控制右腿前后摆动 |
| RL | D6 | 左脚踝 | 控制左脚上下运动 |
| RR | D9 | 右脚踝 | 控制右脚上下运动 |

---

## 基础动作 (Basic Movements)

### 1. walk - 行走

**说明**: 前进或后退行走动作

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-10 | 步数 |
| T | int | 1000 | 600-1400 | 周期（毫秒），值越大速度越慢 |
| direction | int | 1 | 1, -1 | 方向：1=前进，-1=后退 |

**算法参数**:
- 振幅 A: [34, 26, 15, 15]
- 偏移量 O: [0, 0, 4, -4]
- 相位差: [0, 0, -90°, -90°]（根据方向调整）

**示例**:
```python
otto.walk(steps=3, T=800, direction=1)   # 快速前进3步
otto.walk(steps=2, T=1200, direction=-1) # 慢速后退2步
```

---

### 2. turn - 转向

**说明**: 左转或右转动作

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-10 | 步数 |
| T | int | 1000 | 500-1500 | 周期（毫秒） |
| direction | int | 1 | 1, -1 | 方向：1=左转，-1=右转 |

**算法参数**:
- 振幅 A: [30, 30, 15, 15]（根据方向调整：左转时左腿振幅增大到40，右转时右腿振幅增大到40）
- 偏移量 O: [0, 0, 4, -4]
- 相位差: [0, 0, -90°, -90°]

**示例**:
```python
otto.turn(steps=4, T=800, direction=1)   # 快速左转4步
otto.turn(steps=2, T=1000, direction=-1) # 右转2步
```

---

## 舞蹈动作 (Dance Moves)

### 3. bend - 侧弯

**说明**: 身体向左侧或右侧弯曲

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 1 | 1-5 | 弯曲次数 |
| T | int | 500 | 300-1000 | 周期（毫秒） |
| direction | int | 1 | 1, -1 | 方向：1=左弯，-1=右弯 |

**关键帧**:
- 左弯: [90, 90, 40, 35] → [90, 90, 40, 105] → HOME
- 右弯: [90, 90, 140, 80] → [90, 90, 75, 120] → HOME

**示例**:
```python
otto.bend(steps=2, T=600, direction=1)   # 向左侧弯2次
otto.bend(steps=1, T=500, direction=-1)  # 向右侧弯1次
```

---

### 4. shakeLeg - 摇腿

**说明**: 摇动左腿或右腿

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 1 | 1-5 | 摇动次数 |
| T | int | 1500 | 1000-2000 | 周期（毫秒） |
| direction | int | 1 | 1, -1 | 方向：1=左腿，-1=右腿 |

**关键帧**:
- 左腿: [90, 90, 40, 35] → [90, 90, 40, 120] → [90, 90, 70, 60] → HOME
- 右腿: [90, 90, 140, 35] → [90, 90, 40, 140] → [90, 90, 120, 58] → HOME

**示例**:
```python
otto.shakeLeg(steps=2, T=1200, direction=1)   # 摇左腿2次
otto.shakeLeg(steps=1, T=1500, direction=-1)  # 摇右腿1次
```

---

### 5. updown - 上下移动

**说明**: 身体上下振荡运动（类似跳跃前进）

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 跳跃次数 |
| T | int | 1500 | 800-2000 | 周期（毫秒） |
| height | int | 20 | 0-90 | 高度（度） |

**算法参数**:
- 振幅 A: [0, 0, height, height]
- 偏移量 O: [0, 0, height, -height]
- 相位差: [0, 0, -90°, 90°]

**示例**:
```python
otto.updown(steps=3, T=1000, height=25)  # 上下移动3次，高度25度
otto.updown(steps=2, T=1500, height=15)  # 缓慢上下移动2次
```

---

### 6. swing - 摆动

**说明**: 左右摇摆动作

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 摆动次数 |
| T | int | 1000 | 600-1500 | 周期（毫秒） |
| height | int | 20 | 0-50 | 摆动幅度（度） |

**算法参数**:
- 振幅 A: [0, 0, height, height]
- 偏移量 O: [0, 0, height/2, -height/2]
- 相位差: [0, 0, 0, 0]

**示例**:
```python
otto.swing(steps=3, T=800, height=25)   # 快速摆动3次
otto.swing(steps=2, T=1200, height=15)  # 缓慢小幅度摆动2次
```

---

### 7. tiptoeSwing - 踮脚摆动

**说明**: 踮起脚尖左右摇摆

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 摆动次数 |
| T | int | 1000 | 600-1500 | 周期（毫秒） |
| height | int | 20 | 0-50 | 摆动幅度（度） |

**算法参数**:
- 振幅 A: [0, 0, height, height]
- 偏移量 O: [0, 0, height, -height]
- 相位差: [0, 0, 0, 0]

**示例**:
```python
otto.tiptoeSwing(steps=3, T=800, height=20)   # 踮脚摆动3次
otto.tiptoeSwing(steps=2, T=1000, height=15)  # 踮脚摆动2次
```

---

### 8. jitter - 抖动

**说明**: 快速小幅度抖动（类似打颤）

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 抖动次数 |
| T | int | 1000 | 400-1200 | 周期（毫秒） |
| height | int | 20 | 5-25 | 抖动幅度（度） |

**算法参数**:
- 振幅 A: [height, height, 0, 0]
- 偏移量 O: [0, 0, 0, 0]
- 相位差: [-90°, 90°, 0, 0]

**示例**:
```python
otto.jitter(steps=4, T=600, height=15)   # 快速抖动4次
otto.jitter(steps=2, T=800, height=20)   # 抖动2次
```

---

### 9. ascendingTurn - 上升旋转

**说明**: 边上升边旋转

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 旋转次数 |
| T | int | 1000 | 600-1500 | 周期（毫秒） |
| height | int | 50 | 5-15 | 高度（度） |

**算法参数**:
- 振幅 A: [height, height, height, height]
- 偏移量 O: [0, 0, height+4, -height+4]
- 相位差: [-90°, 90°, -90°, 90°]

**示例**:
```python
otto.ascendingTurn(steps=2, T=1000, height=10)   # 上升旋转2次
otto.ascendingTurn(steps=3, T=800, height=12)    # 快速上升旋转3次
```

---

### 10. moonwalker - 月球漫步

**说明**: 迈克尔·杰克逊风格的滑步动作

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 3 | 1-6 | 步数 |
| T | int | 1000 | 800-1500 | 周期（毫秒） |
| height | int | 25 | 15-40 | 抬腿高度（度） |
| direction | int | 1 | 1, -1 | 方向：1=向左滑，-1=向右滑 |

**算法参数**:
- 振幅 A: [0, 0, height, height]
- 偏移量 O: [0, 0, height/2+2, -height/2-2]
- 相位差: [0, 0, φ, -60°×direction+φ]，其中 φ = -direction×90°

**示例**:
```python
otto.moonwalker(steps=4, T=900, height=25, direction=1)   # 向左滑4步
otto.moonwalker(steps=3, T=1000, height=30, direction=-1) # 向右滑3步
```

---

### 11. crusaito - 滑翔

**说明**: 月球漫步与行走的混合动作（侧向滑步）

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 步数 |
| T | int | 1000 | 800-1500 | 周期（毫秒） |
| height | int | 20 | 20-50 | 抬腿高度（度） |
| direction | int | 1 | 1, -1 | 方向：1=向左，-1=向右 |

**算法参数**:
- 振幅 A: [25, 25, height, height]
- 偏移量 O: [0, 0, height/2+4, -height/2-4]
- 相位差: [90°, 90°, 0, -60°×direction]

**示例**:
```python
otto.crusaito(steps=3, T=900, height=25, direction=1)   # 向左滑翔3步
otto.crusaito(steps=2, T=1000, height=20, direction=-1) # 向右滑翔2步
```

---

### 12. flapping - 拍打

**说明**: 翅膀拍打动作（双脚交替抬起）

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 2 | 1-5 | 拍打次数 |
| T | int | 1000 | 600-1500 | 周期（毫秒） |
| height | int | 20 | 10-30 | 拍打幅度（度） |
| direction | int | 1 | 1, -1 | 方向：1=向前，-1=向后 |

**算法参数**:
- 振幅 A: [12, 12, height, height]
- 偏移量 O: [0, 0, height-10, -height+10]
- 相位差: [0, 180°, -90°×direction, 90°×direction]

**示例**:
```python
otto.flapping(steps=3, T=800, height=20, direction=1)   # 向前拍打3次
otto.flapping(steps=2, T=1000, height=15, direction=-1) # 向后拍打2次
```

---

### 13. jump - 跳跃

**说明**: 原地跳跃动作

**参数**:

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| steps | int | 1 | 1-5 | 跳跃次数 |
| T | int | 2000 | 1000-3000 | 周期（毫秒） |

**关键帧**:
- 起跳: [90, 90, 150, 30]
- 落地: HOME_POSITION [90, 90, 90, 90]

**示例**:
```python
otto.jump(steps=2, T=1500)  # 跳跃2次
otto.jump(steps=1, T=2000)  # 单次跳跃
```

---

## 预设舞蹈序列 (Dance Presets)

### happy - 快乐舞蹈

```python
sequence = [
    {'action': 'swing', 'steps': 3, 'T': 700, 'height': 20},
    {'action': 'home'},
    {'action': 'walk', 'steps': 3, 'T': 900, 'direction': 1},
    {'action': 'walk', 'steps': 3, 'T': 900, 'direction': -1},
    {'action': 'tiptoeSwing', 'steps': 3, 'T': 500, 'height': 20},
    {'action': 'home'}
]
```

**描述**: 摇摆 → 前进 → 后退 → 踮脚摇摆 → 归位

---

### dance - 舞蹈

```python
sequence = [
    {'action': 'moonwalker', 'steps': 4, 'T': 900, 'height': 25, 'direction': 1},
    {'action': 'moonwalker', 'steps': 4, 'T': 900, 'height': 25, 'direction': -1},
    {'action': 'crusaito', 'steps': 3, 'T': 900, 'height': 20, 'direction': 1},
    {'action': 'crusaito', 'steps': 3, 'T': 900, 'height': 20, 'direction': -1},
    {'action': 'flapping', 'steps': 3, 'T': 900, 'height': 20, 'direction': 1},
    {'action': 'home'}
]
```

**描述**: 左滑步 → 右滑步 → 左滑翔 → 右滑翔 → 拍打 → 归位

---

### greeting - 问候

```python
sequence = [
    {'action': 'swing', 'steps': 2, 'T': 700, 'height': 30},
    {'action': 'bend', 'steps': 2, 'T': 500, 'direction': 1},
    {'action': 'bend', 'steps': 2, 'T': 500, 'direction': -1},
    {'action': 'walk', 'steps': 3, 'T': 900, 'direction': 1},
    {'action': 'home'}
]
```

**描述**: 摇摆 → 左弯 → 右弯 → 前进 → 归位

---

## 辅助功能

### home - 归位

**说明**: 所有舵机回到中心位置（90度）

**返回值**: ServoAngles(90, 90, 90, 90)

---

### stop_action - 停止动作

**说明**: 设置停止标志，中断当前正在执行的动作

---

### reset_stop_flag - 重置停止标志

**说明**: 在开始新动作前重置停止标志

---

## 参数建议表

### 速度参考

| 动作类型 | 慢速(T) | 中速(T) | 快速(T) |
|----------|---------|---------|---------|
| walk | 1200 | 1000 | 800 |
| turn | 1200 | 1000 | 800 |
| swing | 1200 | 1000 | 800 |
| moonwalker | 1200 | 1000 | 900 |
| jump | 2500 | 2000 | 1500 |

### 幅度参考

| 动作类型 | 小幅度 | 中幅度 | 大幅度 |
|----------|--------|--------|--------|
| swing | 10-15 | 20-25 | 30-40 |
| updown | 10-15 | 20-25 | 30-40 |
| moonwalker | 15-20 | 25-30 | 35-40 |
| flapping | 10-15 | 20-25 | 30 |

---

## 使用示例

### 基础使用

```python
from otto_controller import get_controller

otto = get_controller()

# 执行单个动作
otto.walk(steps=3, T=1000, direction=1)
otto.turn(steps=2, T=800, direction=-1)
otto.jump(steps=1, T=2000)
```

### 执行舞蹈序列

```python
# 执行预设舞蹈
result = otto.execute_dance_sequence("happy")
print(f"完成步数: {result['completed_steps']}")

# 自定义序列
from otto_core import create_action_sequence

custom_sequence = [
    {'action': 'walk', 'steps': 2, 'T': 1000, 'direction': 1},
    {'action': 'swing', 'steps': 3, 'T': 800, 'height': 25},
    {'action': 'jump', 'steps': 1, 'T': 1500},
]

frames = create_action_sequence(custom_sequence)
```

---

## 注意事项

1. **舵机保护**: 所有角度自动限制在 0-180 度范围内
2. **防抖处理**: 角度变化小于 2 度时不会发送命令
3. **动作中断**: 可通过 `stop_action()` 随时中断当前动作
4. **自动归位**: 大多数动作执行后会自动调用 `go_home()`
5. **线程安全**: 动作在独立线程中执行，避免阻塞主程序
