import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import io
import time
import socket
import numpy as np
from logging import basicConfig, INFO
from PIL import Image, ImageOps
from everywhereml.data.collect import MjpegCollector
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import DepthwiseConv2D

# =============================================
# CUSTOM LAYER FIX
# =============================================
class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(*args, **kwargs)

# =============================================
# CONFIGURATION (ADJUST THESE)
# =============================================
MODEL_PATH = "C:/Users/kemcg/Downloads/converted_keras(1)/keras_model.h5"
LABELS_PATH = "C:/Users/kemcg/Downloads/converted_keras(1)/labels.txt"
ESP_CAMERA_IP = 'http://192.168.4.1:81/stream'
CONTROL_HOST = "192.168.4.1"
CONTROL_PORT = 100
IMAGE_SIZE = (224, 224)
MAX_RECONNECT_ATTEMPTS = 5                
BASE_RECONNECT_DELAY = 1                 
MIN_HEARTBEAT_INTERVAL = 0.8              
COMMAND_DELAY = 0.3                       
CONFIDENCE_THRESHOLD = 0.75               

# =============================================
# NETWORK UTILITIES
# =============================================
def create_socket():
    """Create configured socket with timeout"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)  # Shorter timeout than default
    return sock

def is_socket_connected(sock):
    """Robust connection check"""
    try:
        # Test 1: Check peer name
        sock.getpeername()
        # Test 2: Send zero-byte ping
        sock.send(b'')
        return True
    except (socket.error, OSError, AttributeError):
        return False

def safe_send(sock, command, max_retries=2):
    """Reliable command transmission with retries"""
    for attempt in range(max_retries):
        try:
            sock.sendall(command)
            return True
        except (socket.error, BrokenPipeError) as e:
            if attempt == max_retries - 1:
                print(f"! Send failed after {max_retries} attempts: {str(e)}")
                return False
            time.sleep(0.1 * (attempt + 1))
    return False

# =============================================
# CORE FUNCTIONS
# =============================================
def load_components():
    """Safe initialization of ML components"""
    try:
        model = load_model(
            MODEL_PATH,
            compile=False,
            custom_objects={"DepthwiseConv2D": CustomDepthwiseConv2D}
        )
        with open(LABELS_PATH, "r") as f:
            class_names = [line.strip() for line in f.readlines()]
        return model, class_names
    except Exception as e:
        print(f"! Critical load error: {str(e)}")
        exit(1)

def get_image(mjpeg_collector):
    """Robust image capture with error recovery"""
    for attempt in range(3):  # Retry up to 3 times
        try:
            test_sample = mjpeg_collector.collect_by_samples(num_samples=1)
            image = Image.open(io.BytesIO(test_sample[0])).convert("RGB")
            image = ImageOps.fit(image, IMAGE_SIZE, Image.Resampling.LANCZOS)
            image_array = np.asarray(image, dtype=np.float32)
            return np.expand_dims((image_array / 127.5) - 1, axis=0)
        except Exception as e:
            print(f"! Image capture failed (attempt {attempt + 1}): {str(e)}")
            time.sleep(0.5)
    return None

# =============================================
# MAIN CONTROL LOOP
# =============================================
def main_control_loop():
    model, class_names = load_components()
    mjpeg_collector = MjpegCollector(address=ESP_CAMERA_IP)
    basicConfig(level=INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    reconnect_attempts = 0
    last_heartbeat = time.time()
    s = create_socket()

    while reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        try:
            # Connection management
            if not is_socket_connected(s):
                s.close()
                s = create_socket()
                s.connect((CONTROL_HOST, CONTROL_PORT))
                reconnect_attempts = 0
                print("✓ Connection established")

            # Heartbeat management
            if time.time() - last_heartbeat > MIN_HEARTBEAT_INTERVAL:
                if not safe_send(s, b"{Heartbeat}"):
                    raise ConnectionError("Heartbeat failed")
                last_heartbeat = time.time()

            # Image processing
            image_data = get_image(mjpeg_collector)
            if image_data is None:
                continue

            # Prediction
            prediction = model.predict(image_data, verbose=0)
            index = np.argmax(prediction)
            confidence = prediction[0][index]
            
            if confidence < CONFIDENCE_THRESHOLD:
                print(f"! Low confidence ({confidence:.2f}) - ignoring prediction")
                continue

            # Command execution
            class_name = class_names[index].lower()
            if "people" in class_name:
                print("→ PERSON detected - STOPPING")
                safe_send(s, b'{"N":100}')
            elif "allow" in class_name:
                print("→ ALLOWED object - MOVING")
                safe_send(s, b'{"N":3,"D1":3,"D2":100}')
                time.sleep(1)
                # safe_send(s, b'{"N":100}')

            time.sleep(COMMAND_DELAY)

        except ConnectionError as e:
            reconnect_attempts += 1
            delay = min(BASE_RECONNECT_DELAY * (2 ** reconnect_attempts), 10)
            print(f"! Connection error: {e} - Retrying in {delay}s...")
            time.sleep(delay)
            s = create_socket()

        except KeyboardInterrupt:
            print("\n! Controlled shutdown initiated")
            safe_send(s, b'{"N":100}')
            break

        except Exception as e:
            print(f"! Unexpected error: {str(e)}")
            safe_send(s, b'{"N":100}')
            time.sleep(1)

    if reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
        print("! Maximum reconnection attempts reached - shutting down")

# =============================================
# ENTRY POINT
# =============================================
if __name__ == "__main__":
    print("🚀 Elegoo Smart Car Controller v2.0")
    print(f"• Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"• Max reconnect attempts: {MAX_RECONNECT_ATTEMPTS}")
    
    try:
        # Initial system check
        test_img = get_image(MjpegCollector(address=ESP_CAMERA_IP))
        if test_img is not None:
            print("✓ All systems nominal - starting control loop")
            main_control_loop()
        else:
            print("! Camera initialization failed")
    except Exception as e:
        print(f"! Fatal startup error: {str(e)}")
    finally:
        print("System shutdown complete")
