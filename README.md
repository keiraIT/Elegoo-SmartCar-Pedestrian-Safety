# 🚦 Elegoo Smart Car - Vision-Based Pedestrian Safety System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

*A real-time vision-based system that safely stops when pedestrians are detected*

![System Demo GIF](./docs/media/demo.gif)

## 📌 Table of Contents
- [Project Focus](#-project-focus)
- [System Characteristics](#-system-characteristics)
- [Hardware Setup](#-hardware-setup)
- [Software Components](#-software-components)
- [Installation](#-installation)
- [Usage](#-usage)
- [Technical Details](#-technical-details)
- [Development Phases](#-development-phases)
- [Limitations](#-limitations)
- [License](#-license)

## 🔍 Project Focus
This system demonstrates a safety-critical application of computer vision on embedded hardware:
- **Pedestrian Detection**: Uses custom-trained CNN to identify humans in camera feed
- **Automatic Stopping**: Triggers immediate stop when person detected (confidence > 0.75)
- **Host-Vehicle Communication**: WiFi-based control protocol between laptop and car
- **Reliable Operation**: Robust error handling and reconnection logic

**Key Innovation**: Cost-effective implementation of collision prevention using off-the-shelf educational hardware.

## 📋 System Characteristics
| Component            | Specification                           |
|----------------------|----------------------------------------|
| **Processing**       | External host computer (Python 3.8+)   |
| **Detection Latency**| ~300ms (from capture to decision)      |
| **Camera Input**     | ESP32-S3-Eye (1600×1200, MJPEG stream) |
| **Model Input Size** | 224×224 pixels (normalized to [-1, 1]) |
| **Control Protocol** | Custom JSON over TCP (Port 100)        |
| **Heartbeat**        | 0.8s interval                          |

## 🛠️ Hardware Setup
### Required Components
1. **Elegoo Smart Car v4.0** with:
   - Assembled chassis and motors
   - ESP32-S3-Eye camera module
   - 18650 battery pack

2. **Host Computer**:
   - WiFi-capable laptop/PC
   - Minimum specs: Core i5, 8GB RAM
  
## 💻 Software Components

### 1. Main Control System (`main_control.py`)
- **Core Functionality**:
  - Continuous camera feed analysis
  - Pedestrian detection via CNN
  - Safety stop command triggering
  - Connection reliability features

### Connection Diagram
```plaintext
[Laptop] ←WiFi→ [ESP32-S3-Eye]
                   │
                   ├─ Camera Stream (MJPEG)
                   └─ Motor Control (TCP Commands)
