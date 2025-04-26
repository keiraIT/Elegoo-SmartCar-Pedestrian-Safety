# 🌐 System Architecture

## Key Components
| Component | Purpose |
|-----------|---------|
| `main_control.py` | Core detection & control logic |
| `keras_model.h5` | Trained pedestrian detection model |
| ESP32 Camera | Live video capture |

## Communication Protocol
```python
# Example Command Format
'{"N":3,"D1":3,"D2":200}'  # Move forward at speed 200
'{"N":100}'                 # Emergency stop
```
