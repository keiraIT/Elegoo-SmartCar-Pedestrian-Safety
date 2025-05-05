import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # Disable OneDNN optimizations for compatibility

import io
import time
import socket
import numpy as np
from logging import basicConfig, INFO
from PIL import Image, ImageOps
from everywhereml.data.collect import MjpegCollector
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import DepthwiseConv2D

# FIX FOR COMPATIBILITY
class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        kwargs.pop("groups", None)  
        super().__init__(*args, **kwargs)

# CONFIGS
MODEL_PATH = "C:/Users/YourUser/YourDownloads/converted_keras(1)/keras_model.h5" # <---Change to your keras_model.h5 filepath
LABELS_PATH = "C:/Users/YourUser/YourDownloads/converted_keras(1)/labels.txt"  # <---Change to your labels.txt filepath
# For the code below, toproperly verify connection car/connection to the car's wifi, go to this link/paste 
# this link to the browser and feed from the car's camera should stream to your host device 
ESP_CAMERA_IP = 'http://192.168.4.1:81/stream' 
CONTROL_HOST = "192.168.4.1"
CONTROL_PORT = 100
HEARTBEAT_INTERVAL = 2  
IMAGE_SIZE = (224, 224)

# Core Functions 
# =============================================
# Loads all main components here; the model and its components; Handles getting the image from the camera and if it fails
def load_components():
    """Safe initialization of ML components"""
    try:
        model = load_model(MODEL_PATH, compile=False, custom_objects={"DepthwiseConv2D": CustomDepthwiseConv2D})
        with open(LABELS_PATH, "r") as f:
            class_names = [line.strip() for line in f.readlines()]
        return model, class_names
    except Exception as e:
        print(f"! Critical load error: {str(e)}")
        exit(1)

def get_image(mjpeg_collector):
    """image capturing with error recovery""" # <---basically what this section does
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


# Main Control Loop
def main_control_loop():
    model, class_names = load_components()
    mjpeg_collector = MjpegCollector(address = ESP_CAMERA_IP)
    basicConfig(level = INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    reconnect_attempts = 0
    last_heartbeat = time.time()
    s = create_socket()

    while reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
        try:
            # Connection handler
            if not is_socket_connected(s):
                s.close()
                s = create_socket()
                s.connect((CONTROL_HOST, CONTROL_PORT))
                reconnect_attempts = 0
                print("Connection established")

            # Heartbeat management
            if time.time() - last_heartbeat > MIN_HEARTBEAT_INTERVAL:
                if not safe_send(s, b"{Heartbeat}"):
                    raise ConnectionError("Heartbeat failed")
                last_heartbeat = time.time()

            # Image processing
            image_data = get_image(mjpeg_collector)
            if image_data is None:
                continue

            # Predicting the image
            prediction = model.predict(image_data, verbose=0)
            index = np.argmax(prediction)
            confidence = prediction[0][index]
            
            if confidence < CONFIDENCE_THRESHOLD:
                print(f"! Low confidence ({confidence:.2f}) - ignoring prediction")
                continue

            # Command execution
            class_name = class_names[index].lower()
            if "people" in class_name:
                print("PERSON detected - STOPPING") # <---lists predicted label/object for debugging
                safe_send(s, b'{"N":100}') # <---command protocol to stop car
            elif "allow" in class_name:
                # this class includes any objects that aren't considered "people"
                print("ALLOWED object - MOVING")  # <---lists predicted label/object for debugging
                safe_send(s, b'{"N":3,"D1":3,"D2":100}') # <---command protocol for moving the car (can change to above params)
                time.sleep(1)

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


# Main Output
if __name__ == "__main__":
    print("Elegoo Smart Car Controller v2.0")
    print(f"• Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"• Max reconnect attempts: {MAX_RECONNECT_ATTEMPTS}")
    
    try:
        # Initial system check
        test_img = get_image(MjpegCollector(address = ESP_CAMERA_IP))
        if test_img is not None:
            print("starting control loop")
            main_control_loop()
        else:
            print("! Camera initialization failed")
    except Exception as e:
        print(f"! Fatal startup error: {str(e)}")
    finally:
        print("System shutdown complete")
