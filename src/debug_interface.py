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

# CONFIG
# ==============================================
#    Names propmted for better understanding of instatiated variables and where they are used in the code
#    Also to help with understanding of the code, what it does, and wha tvariables goes into the process 
MODEL_PATH = "C:/Users/YourUser/YourDownloads/converted_keras(1)/keras_model.h5" # <---Change to your converted_keras(1)keras_model.h5 filepath
LABELS_PATH = "C:/Users/YourUser/YourDownloads/converted_keras(1)/labels.txt"  # <---Change to your converted_keras(1).labels.txt filepath

# For the code below, to properly verify connection to the car's wifi, and in turn the camera, copy and paste
# the 'http://' link/address to ur browser. Once done, feed from the car's camera should stream to your host device 
ESP_CAMERA_IP = 'http://192.168.4.1:81/stream' 
CONTROL_HOST = "192.168.4.1"
CONTROL_PORT = 100
HEARTBEAT_INTERVAL = 2  
IMAGE_SIZE = (224, 224)

# INITIALIZATION
# ==============================================
# Load model 
try:
    model = load_model(MODEL_PATH, compile=False,
        custom_objects={"DepthwiseConv2D": CustomDepthwiseConv2D}
                      )
    print("Model loaded ")
except Exception as e:
    print(f"Failed to load model: {str(e)}") # <--- loading failure message
    exit(1)

# Load labels
try:
    with open(LABELS_PATH, "r") as f:
        class_names = [line.strip() for line in f.readlines()]
    print("Labels loaded successfully") 
except Exception as e:
    print(f"Failed to load labels: {str(e)}")
    exit(1)

# Initialize camera collector
basicConfig(level = INFO)
mjpeg_collector = MjpegCollector(address = ESP_CAMERA_IP)


# IMAGE PROCESSING
def get_image(mjpeg_collector):
    """Capture and preprocess image from camera"""
    try:
        test_sample = mjpeg_collector.collect_by_samples(num_samples=1)
        
        image = Image.open(io.BytesIO(test_sample[0])).convert("RGB")
        image = ImageOps.fit(image, IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        image_array = np.asarray(image, dtype=np.float32)
        normalized_image_array = (image_array / 127.5) - 1
        
        return np.expand_dims(normalized_image_array, axis=0)
        
    except Exception as e:
        print(f"Error capturing image: {str(e)}")
        return None

# MAIN CONTROL LOOP
# ===============================================
#     Command structure was taken from Elegoo Communication Protocol v4.0 (2023) 
#     {"N":3,"D1":direction,"D2":speed} - Motor movement command
#     D1 params: 1 = Turn left; 2 = Turn right; 3 = Forward; 4 = Backward
def main_control_loop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:        
        try:
            s.connect( ( CONTROL_HOST, CONTROL_PORT ) )
            # makes sure host (you) are connected to the port (car)
            print(f"Connected to {CONTROL_HOST} : {CONTROL_PORT}")
            
            last_heartbeat = time.time()
            
            while True:
                if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                    s.sendall(b"{Heartbeat}")
                    last_heartbeat = time.time()
                    print("Sent heartbeat")
                
                # Capture and process image
                print("Capturing image...")
                image_data = get_image(mjpeg_collector)
                if image_data is None:
                    continue
                
                # Makes prediction
                prediction = model.predict(image_data)
                index = np.argmax(prediction)
                class_name = class_names[index]
                confidence = prediction[0][index]

                # More model-error/model-prediction verfications/debugging messages
                print(f"Predicted: {class_name} (Confidence: {confidence:.2f})")
                
                # More Control logic:
                # Command structure was taken from Elegoo Communication Protocol v4.0 (2023) 
                # {"N":3,"D1":direction,"D2":speed} - Motor movement command
                # D1 params: 1 = Turn left; 2 = Turn right; 3 = Forward; 4 = Backward
                # D2 params: 0-255; (its PWM so the range goes from 0-255)
                if "people" in class_name.lower() and confidence > 0.7:  # <---Confidence minimum
                    print("Person detected - taking action")
                    s.sendall(b'{"N":100}') # <---Stopping command
                    time.sleep(1) 
                elif "allow" in class_name.lower() and confidence > 0.7:                    
                    print("Allowed object - moving forward") # <--- model/image verfiication (if it predicted the correct object)
                    s.sendall(b'{"N":3,"D1":3,"D2":140}')  # <---Move forward (can be altered to params above) 
                    time.sleep(3)
                    s.sendall(b'{"N":3,"D1":3,"D2":140}')  
                    time.sleep(3)

                time.sleep(0.5)  # <--- Small break between cycles
                
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Error in control loop: {str(e)}")
        finally:
            print("Connection closed")

# Main Ouput
if __name__ == "__main__":
    print("Starting Smart Car Control System")
    try:
        # testing, image capturing, and error debuggin messages
        test_data = get_image(mjpeg_collector)
        if test_data is not None:
            print("Camera test successful")
            main_control_loop()
        else:
            print("Failed initial camera test")
    except Exception as e:
        print(f"Fatal error: {str(e)}")


