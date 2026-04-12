import sys
import cv2
import os
import time
import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer
from ultralytics import YOLO
import mediapipe as mp
from tensorflow.keras.models import load_model
from send_error import send_error_code
from common_part import SoundPlayer, siniflandir_resim, led_set, servo_yolla, get_cm_distance

mobilenet_model = load_model('/home/melih/Desktop/AIMI/model-veriseti/el-bilek/sınıfelap/elpa.h5')
MODEL_PATH = "/home/melih/Desktop/AIMI/model-veriseti/el-bilek/train2/weights/best.pt"
SAVE_DIR = "/home/melih/Desktop/veritabani2"
SES_TEXT1 = "Lütfen parmaklarınızı açın."
SES_TEXT2 = "Lütfen parmaklarınızı ayırın."
SES_TEXT3 = "El kadraj dışında lütfen kamerayı ortalayın."
SES_BASLANGIC = "Röntgen çekimi için elinizi getirin."
SES_DOGRU = "Pozisyon doğru. Çekime hazırsınız."
CONFIDENCE_THRESHOLD = 0.92
WIDTH = int(640 * 1.4)
HEIGHT = int(480 * 1.4)
CLASS_NAMES = ["dogru", "hatali"]
CM_PER_PIXEL = 42

mp_hands = mp.solutions.hands
sound_player = SoundPlayer()

def are_adjacent_fingers_too_close(hand_landmarks, width, height, cm_per_pixel, threshold_cm=1.5):
    adjacent_pairs = [(8, 12), (12, 16), (16, 20)]
    for i1, i2 in adjacent_pairs:
        x1, y1 = int(hand_landmarks.landmark[i1].x * width), int(hand_landmarks.landmark[i1].y * height)
        x2, y2 = int(hand_landmarks.landmark[i2].x * width), int(hand_landmarks.landmark[i2].y * height)
        distance_pixels = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        distance_cm = distance_pixels / cm_per_pixel
        if distance_cm < threshold_cm:
            return True
    return False

def is_hand_closed(hand_landmarks):
    closed_fingers = 0
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            closed_fingers += 1
    return closed_fingers == 4

class YoloMediapipeApp(QWidget):
    def __init__(self, app, tc_kimlik, archive_panel_callback=None, scale_factor=1.4):
        super().__init__()
        self.setWindowTitle("Röntgen Kontrol (El Bilek)")
        self.tc_kimlik = str(tc_kimlik)
        self.archive_panel_callback = archive_panel_callback
        global WIDTH, HEIGHT
        WIDTH = int(640 * scale_factor)
        HEIGHT = int(480 * scale_factor)

        self.setGeometry(100, 100, WIDTH, HEIGHT + 130)
        self.app = app

        layout = QVBoxLayout()
        self.label = QLabel("Kamera görüntüsü burada görünecek.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedSize(WIDTH, HEIGHT)
        layout.addWidget(self.label)
        self.info_label = QLabel("Röntgen çekimi için elinizi getirin.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(30)

        self.model = YOLO(MODEL_PATH)
        self.saved = False
        self.hatali_start_time = None
        self.mediapipe_mode = False
        self.last_pose_type = None
        self.last_speech_code = None
        self.last_dogru_time = None
        self.servo_sent = False
        self.dogru_kare_sayaci = 0
        self.sound_cooldown = 0
        self.mp_hands_instance = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7)
        self.current_frame = None

        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Açılışta giriş sesi ve yazısı
        self.show_and_say("Röntgen çekimi için elinizi getirin.", SES_BASLANGIC)

    def show_and_say(self, info_text, speech_text=None):
        self.info_label.setText(info_text)
        now = time.time()
        if speech_text and (self.last_speech_code != speech_text or now - self.sound_cooldown > 2):
            sound_player.play(speech_text, speed=1.5)
            self.last_speech_code = speech_text
            self.sound_cooldown = now

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.show_and_say("Kameradan görüntü alınamadı!")
            self.timer.stop()
            self.cap.release()
            return
        self.current_frame = frame.copy()
        results = self.model.predict(frame, verbose=False)
        boxes = results[0].boxes
        display_frame = frame.copy()
        found_dogru = False
        dogru_conf = 0.0
        found_hatali = False

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                b = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf.cpu().numpy())
                class_id = int(box.cls.cpu().numpy())
                color = (0, 255, 0) if class_id == 0 else (0, 0, 255)
                cv2.rectangle(display_frame, (b[0], b[1]), (b[2], b[3]), color, 2)
                if class_id == 0 and conf >= CONFIDENCE_THRESHOLD:
                    found_dogru = True
                    dogru_conf = conf
                elif class_id == 1:
                    found_hatali = True

        now = time.time()
        if not hasattr(self, 'dogru_kare_sayaci'):
            self.dogru_kare_sayaci = 0

        if found_dogru and dogru_conf >= CONFIDENCE_THRESHOLD:
            led_set('B')
            if self.last_dogru_time is None:
                self.last_dogru_time = now
                self.dogru_kare_sayaci = 1
                self.servo_sent = False
            else:
                self.dogru_kare_sayaci += 1
            if self.last_pose_type != 0:
                send_error_code(0, "elpa")
                self.last_pose_type = 0
            # 3 sn boyunca doğruysa
            if now - self.last_dogru_time >= 3 and not self.servo_sent:
                self.show_and_say("Pozisyon doğru. Çekime hazırsınız.", SES_DOGRU)
                send_error_code(0, "elpa")
                QTimer.singleShot(2000, servo_yolla)
                self.servo_sent = True
        else:
            self.last_dogru_time = None
            self.dogru_kare_sayaci = 0
            self.servo_sent = False

        if found_hatali:
            led_set('R')
            if self.hatali_start_time is None:
                self.hatali_start_time = now
            if not self.mediapipe_mode and now - self.hatali_start_time >= 2:
                self.mediapipe_mode = True
                self.show_and_say("Hatalı pozisyon")
            if self.mediapipe_mode:
                display_frame = self.run_mediapipe_on_frame(self.current_frame, display_frame)
                self.update_display(display_frame)
            else:
                self.update_display(display_frame)
        else:
            self.hatali_start_time = None
            self.mediapipe_mode = False
            if self.last_pose_type not in (None, 0):
                send_error_code(0, "elpa")
                self.last_pose_type = 0
            self.update_display(display_frame)

    def run_mediapipe_on_frame(self, frame, display_frame):
        results = self.mp_hands_instance.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        adjacent_close = False
        hand_closed = False
        hand_out_of_frame = True

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                if len(hand_landmarks.landmark) < 21:
                    hand_out_of_frame = True
                    continue
                else:
                    hand_out_of_frame = False
                adjacent_close = are_adjacent_fingers_too_close(
                    hand_landmarks, WIDTH, HEIGHT, CM_PER_PIXEL, threshold_cm=1.5
                )
                hand_closed = is_hand_closed(hand_landmarks)

        pose_type = None
        if hand_out_of_frame:
            pose_type = 3
        elif hand_closed:
            pose_type = 2
        elif adjacent_close:
            pose_type = 1

          # SESLİ UYARI EKLENDİ!!!
        if pose_type != self.last_pose_type:
            if pose_type == 1:
                self.show_and_say("Lütfen parmaklarınızı açın.", SES_TEXT1)
                send_error_code(1, "elpa")
                self.last_pose_type = 1
            elif pose_type == 2:
                self.show_and_say("Lütfen parmaklarınızı ayırın.", SES_TEXT2)
                send_error_code(2, "elpa")
                self.last_pose_type = 2
            elif pose_type == 3:
                self.show_and_say("El kadraj dışında lütfen kamerayı ortalayın.", SES_TEXT3)
                send_error_code(3, "elpa")
                self.last_pose_type = 3
            else:
                send_error_code(0, "elpa")
                self.last_pose_type = 0

        return display_frame

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Control:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_dir = os.path.join(SAVE_DIR, self.tc_kimlik)
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    save_path = os.path.join(save_dir, f"manual_{now}.jpg")
                    cv2.imwrite(save_path, frame)
                    predicted_class = siniflandir_resim(mobilenet_model, save_path)
                    if predicted_class == 1:
                        self.show_and_say("Doğru röntgen görüntüsü, Geçmiş olsun!", "Doğru röntgen görüntüsü, Geçmiş olsun!")
                        send_error_code(0, "elpa")
                        if self.cap:
                            self.cap.release()
                            self.cap = None
                        if self.timer.isActive():
                            self.timer.stop()
                    else:
                        if os.path.exists(save_path):
                            os.remove(save_path)
                        if predicted_class == 2:
                            self.show_and_say("Hatalı görüntü!", "Hatalı Görüntü! Tekrar Deneyiniz.")
                        else:
                            self.show_and_say("Bulanık veya algılanmadı.", "Görüntü Bulanık, Tekrar deneyin!")
            else:
                print("Kamera açık değil.")

    def update_display(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        led_set('O')
        event.accept()