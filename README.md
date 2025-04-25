# Elegoo Smart Car - Vision-Based Pedestrian Safety System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Specifications](#system-specifications)
3. [Hardware Requirements](#hardware-requirements)
4. [Software Architecture](#software-architecture)
//
5. [Installation Guide](#installation-guide)
6. [Operation Manual](#operation-manual)
7. [Technical Implementation](#technical-implementation)
8. [Development Process](#development-process)
9. [System Limitations](#system-limitations)
10. [License](#license)

## Project Overview

This system implements a computer vision-based safety mechanism for the Elegoo Smart Car v4.0 platform. The primary function is to detect pedestrians in the car's path using an onboard camera and automatically initiate stopping procedures when people are identified.

Key features:
- Real-time image processing at 3-5 FPS
- Custom-trained convolutional neural network
- WiFi-based control interface
- Configurable confidence threshold (default: 0.75)
- Robust connection management

## System Specifications

| Component               | Specification                           |
|-------------------------|----------------------------------------|
| Processing Unit         | External host computer (Python 3.8+)   |
| Detection Latency       | 250-350ms end-to-end                   |
| Camera Resolution       | 1600×1200 (MJPEG stream at 5 FPS)      |
| Model Input Resolution  | 224×224 pixels                         |
| Control Protocol        | JSON over TCP (Port 100)               |
| Heartbeat Interval      | 800ms                                  |
| Max Reconnection Attempts | 5 (with exponential backoff)         |

## Hardware Requirements

### Essential Components
1. Elegoo Smart Car v4.0 with:
   - Assembled chassis and motor assembly
   - ESP32-S3-Eye camera module
   - Fully charged 18650 battery pack

2. Host Computer:
   - Minimum: Intel Core i5 or equivalent
   - RAM: 8GB minimum
   - Operating System: Windows 10/11 or Linux
   - WiFi connectivity

### Connection Diagram
### Connection Diagram
```plaintext
[Laptop] ←WiFi→ [ESP32-S3-Eye]
                   │
                   ├─ Camera Stream (MJPEG)
                   └─ Motor Control (TCP Commands)
```

## Software Architecture

### Core Components

1. **Main Control System (main_control.py)**
   - Image acquisition and preprocessing
   - Model inference engine
   - Decision-making logic
   - Command transmission handler

Key implementation details:
```python
# Safety stop condition implementation
if ("person" in detected_class and 
    prediction_confidence > CONFIDENCE_THRESHOLD):
    send_emergency_stop()
```
2. ## Debug Interface (debug_interface.py)
   - Frame capture diagnostics
   - Model performance metrics
   - Command echo testing
   
3. ## Motor Test Utility (motor_test.py)
   - Basic movement validation
   - Connection testing

### Installation Guide

## Prerequisites
   - Python 3.8 or later
   - pip package manager
   - Git version control

## Set-up Instructions
   - 
