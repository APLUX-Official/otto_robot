// SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
//
// SPDX-License-Identifier: MPL-2.0

#include <Arduino_RouterBridge.h>
#include <Servo.h>


struct PinEntry { const char* name; uint8_t pin; };

static const PinEntry kPins[] = {
  {"D21", D21}, {"D20", D20}, {"D13", D13}, {"D12", D12},
  {"D10", D10}, {"D9",  D9 }, {"D8",  D8 },{"D11",  D11 },
  {"D7",  D7 }, {"D6",  D6 }, {"D5",  D5 }, {"D4",  D4 },
  {"D3",  D3 }, {"D2",  D2 }, {"D1",  D1 }, {"D0",  D0 },
  {"A0",  A0 }, {"A1",  A1 }, {"A2",  A2 }, {"A3",  A3 },
  {"A4",  A4 }, {"A5",  A5 },
  {"LED3_R", LED_BUILTIN}, {"LED3_G", LED_BUILTIN + 1}, {"LED3_B", LED_BUILTIN + 2},
  {"LED4_R", LED_BUILTIN + 3}, {"LED4_G", LED_BUILTIN + 4}, {"LED4_B", LED_BUILTIN + 5},
};


Servo leftLeg;
Servo rightLeg;
Servo leftFoot;
Servo rightFoot;

static inline int findIndex(const char* n) {
  for (size_t i = 0; i < sizeof(kPins)/sizeof(kPins[0]); ++i) {
    if (strcmp(kPins[i].name, n) == 0) return (int)i;
  }
  return -1;
}

// Generic setter: name + bool
void set_pin_by_name(String name, bool s) {
  int idx = findIndex(name.c_str());
  if (idx < 0) return;             
  digitalWrite(kPins[idx].pin, s ? HIGH : LOW);   
}

// Servo state tracking to avoid unnecessary writes
static int lastD3Angle = -1;
static int lastD5Angle = -1;
static int lastD6Angle = -1;
static int lastD9Angle = -1;

void set_servo_angle(String pinName, int angle) {
  // Clamp angle to valid range
  if (angle < 0) angle = 0;
  if (angle > 180) angle = 180;

  // Only write if angle has changed (prevents jitter)
  if (pinName == "D3") {
    if (angle != lastD3Angle) {
      leftLeg.write(angle);
      lastD3Angle = angle;
    }
  } else if (pinName == "D5") {
    if (angle != lastD5Angle) {
      rightLeg.write(angle);
      lastD5Angle = angle;
    }
  } else if (pinName == "D6") {
    if (angle != lastD6Angle) {
      leftFoot.write(angle);
      lastD6Angle = angle;
    }
  } else if (pinName == "D9") {
    if (angle != lastD9Angle) {
      rightFoot.write(angle);
      lastD9Angle = angle;
    }
  }
}

int get_servo_angle(String pinName) {
  if (pinName == "D3") {
    return leftLeg.read();
  } else if (pinName == "D5") {
    return rightLeg.read();
  } else if (pinName == "D6") {
    return leftFoot.read();
  } else if (pinName == "D9") {
    return rightFoot.read();
  }
  return -1;
}

void setup()
{
    // 初始化所有引脚
    for (auto &e : kPins) pinMode(e.pin, OUTPUT);
    
    // 初始化 LED
    digitalWrite(LED_BUILTIN, HIGH);
    digitalWrite(LED_BUILTIN + 1, HIGH);
    digitalWrite(LED_BUILTIN + 2, HIGH);
    digitalWrite(LED_BUILTIN + 3, HIGH);
    digitalWrite(LED_BUILTIN + 4, HIGH);
    digitalWrite(LED_BUILTIN + 5, HIGH);
    
    // 初始化舵机
    leftLeg.attach(D3);
    delay(20);
    rightLeg.attach(D5);
    delay(20);
    leftFoot.attach(D6);
    delay(20);
    rightFoot.attach(D9);
    delay(20);
    
    // 设置舵机初始位置
    leftLeg.write(90);
    rightLeg.write(90);
    leftFoot.write(90);
    rightFoot.write(90);
    // 启动 Bridge
    Bridge.begin();
    
    // 注册 Bridge 服务
    Bridge.provide("set_pin_by_name", set_pin_by_name);
    Bridge.provide("set_servo_angle", set_servo_angle);
    Bridge.provide("get_servo_angle", get_servo_angle);
}

void loop() {}
