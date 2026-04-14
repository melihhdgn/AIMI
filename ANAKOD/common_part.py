import threading
import os
import subprocess
import uuid
import numpy as np
import time
import serial
from tensorflow.keras.preprocessing import image as keras_image

class SoundPlayer:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_process = None

    def play(self, text, speed=1.5, on_finish=None):
        with self.lock:
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
            temp_mp3 = f"temp_warning_{uuid.uuid4().hex}.mp3"
            t = threading.Thread(target=self._play, args=(text, speed, temp_mp3, on_finish), daemon=True)
            t.start()

    def _play(self, text, speed, temp_mp3, on_finish=None):
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='tr', slow=False)
            tts.save(temp_mp3)
            atempo_val = min(max(speed, 0.5), 2.0)
            self.current_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-af", f"atempo={atempo_val}", temp_mp3],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.current_process.wait()
        except Exception as e:
            print("Sesli uyarı hatası:", e)
        finally:
            try:
                os.remove(temp_mp3)
            except Exception:
                pass
            self.current_process = None
            if on_finish is not None:
                on_finish()

def siniflandir_resim(model, image_path):
    img = keras_image.load_img(image_path, target_size=(224, 224))
    img_array = keras_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    prediction = model.predict(img_array)
    class_index = np.argmax(prediction)
    return class_index  # 0: bulanık, 1: doğru, 2: hatalı

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
except Exception as e:
    print("Arduino bağlantısı kurulamadı:", e)
    arduino = None

def led_set(state):
    if arduino:
        try:
            arduino.write(state.encode())
        except Exception as e:
            print("LED komutu gönderilemedi:", e)

def servo_yolla():
    if arduino:
        try:
            arduino.write(b'C')
            arduino.flush()
            print("[PYTHON] Servo komutu (C) gönderildi.")
        except Exception as e:
            print("Servo komutu gönderilemedi:", e)

def get_cm_distance(lm1, lm2, WIDTH=640, HEIGHT=480, CM_PER_PIXEL=42):
    x1, y1 = int(lm1.x * WIDTH), int(lm1.y * HEIGHT)
    x2, y2 = int(lm2.x * WIDTH), int(lm2.y * HEIGHT)
    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance / CM_PER_PIXEL