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

mobilenet_model = load_model('/home/melih/Desktop/AIMI/model-veriseti/oblik/sınıfobli/oblik.h5')
MODEL_PATH = "/home/melih/Desktop/AIMI/model-veriseti/oblik/train3/weights/best.pt"
SAVE_DIR = "/home/melih/Desktop/veritabani2"
CONFIDENCE_THRESHOLD = 0.75
WIDTH = 640
HEIGHT = 480
CLASS_NAMES = ["dogru", "hatali"]
CM_PER_PIXEL = 42

SES_TEXT1 = "Baş ve işaret parmağınızı yakınlaştırın."
SES_TEXT2 = "Orta, yüzük ve serçe parmaklarınızı tamamen ayırın."
SES_TEXT3 = "Tüm pozisyonlar yanlış!"
SES_BASLANGIC = "Röntgen çekimi için elinizi getirin."
SES_DOGRU = "Pozisyon doğru. Çekime hazırsınız."

mp_hands = mp.solutions.hands
sound_player = SoundPlayer()

def is_wrong_thumb_index(hand_landmarks, threshold=1.3):
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    cm_distance = get_cm_distance(thumb_tip, index_tip, WIDTH, HEIGHT, CM_PER_PIXEL)
    return cm_distance > threshold

def is_wrong_finger_pose(lm12, lm16, lm20, WIDTH=640, HEIGHT=480, CM_PER_PIXEL=42, threshold1=0.9, threshold2=1.6):
    d1 = get_cm_distance(lm12, lm16, WIDTH, HEIGHT, CM_PER_PIXEL)  # orta-yüzük arası
    d2 = get_cm_distance(lm16, lm20, WIDTH, HEIGHT, CM_PER_PIXEL)  # yüzük-serçe arası
    # debug için yazdırabilirsin:
    # print(f"d1: {d1:.2f} cm, d2: {d2:.2f} cm")

    if d1 < threshold1 or d2 < threshold2:
        return True  # Hatalı pozisyon, gif göster
    return False

class YoloMediapipeApp(QWidget):
    def __init__(self, app, tc_kimlik=None, archive_panel_callback=None, scale_factor=1.4):
        super().__init__()
        self.setWindowTitle("Röntgen Kontrol (Oblik)")
        self.tc_kimlik = str(tc_kimlik) if tc_kimlik else ""
        self.archive_panel_callback = archive_panel_callback
        global WIDTH, HEIGHT
        WIDTH = int(640 * scale_factor)
        HEIGHT = int(480 * scale_factor)

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
        # Sesi üst üste bindirme, aynı sesi tekrarlama engeli
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

        # Kutuları çiz, yüzdeyle doğruluk yazısı ekle
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                b = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf.cpu().numpy())
                class_id = int(box.cls.cpu().numpy())
                class_name = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else str(class_id)
                label = f"{class_name}: {conf*100:.1f}%"
                color = (0, 255, 0) if class_id == 0 else (0, 0, 255)
                cv2.rectangle(display_frame, (b[0], b[1]), (b[2], b[3]), color, 2)
                cv2.putText(display_frame, label, (b[0], max(b[1] - 10, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                if class_id == 0 and conf >= CONFIDENCE_THRESHOLD:
                    found_dogru = True
                    dogru_conf = conf
                elif class_id == 1:
                    found_hatali = True

        now = time.time()
        if found_dogru and dogru_conf >= CONFIDENCE_THRESHOLD:
            led_set('B')
            if self.last_dogru_time is None:
                self.last_dogru_time = now
                self.dogru_kare_sayaci = 1
                self.servo_sent = False
            else:
                self.dogru_kare_sayaci += 1
            # 3 sn boyunca doğruysa
            if now - self.last_dogru_time >= 3 and not self.servo_sent:
                self.show_and_say("Pozisyon doğru. Çekime hazırsınız.", SES_DOGRU)
                send_error_code(0, "oblik")  # Panelde sağ gif kapansın
                QTimer.singleShot(2000, servo_yolla)
                self.servo_sent = True
            if self.last_pose_type != 0:
                send_error_code(0, "oblik")
                self.last_pose_type = 0
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
            self.last_pose_type = None
            self.last_speech_code = None
            self.update_display(display_frame)

    def run_mediapipe_on_frame(self, frame, display_frame):
        results = self.mp_hands_instance.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        thumb_index_wrong = False
        other_three_wrong = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style()
                )
                thumb_index_wrong = is_wrong_thumb_index(hand_landmarks, threshold=1.3)
                lm12 = hand_landmarks.landmark[12]
                lm16 = hand_landmarks.landmark[16]
                lm20 = hand_landmarks.landmark[20]
                other_three_wrong = is_wrong_finger_pose(lm12, lm16, lm20, WIDTH, HEIGHT, CM_PER_PIXEL, threshold1=0.9, threshold2=1.6)

        pose_type = None
        if thumb_index_wrong and other_three_wrong:
            pose_type = 3
        elif thumb_index_wrong:
            pose_type = 1
        elif other_three_wrong:
            pose_type = 2

        if pose_type and pose_type != self.last_pose_type:
            if pose_type == 1:
                self.show_and_say("Baş ve işaret parmağınızı yakınlaştırın.", SES_TEXT1)
                send_error_code(1, "oblik")
            elif pose_type == 2:
                self.show_and_say("Orta, yüzük ve serçe parmaklarınızı tamamen ayırın.", SES_TEXT2)
                send_error_code(2, "oblik")
            else:
                self.show_and_say("Tüm pozisyonlar yanlış!", SES_TEXT3)
                send_error_code(3, "oblik")
            self.last_pose_type = pose_type
        elif not pose_type:
            self.last_pose_type = None

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
                        self.show_and_say("Doğru görüntü!", "Doğru görüntü,Geçmiş olsun!")
                        if self.cap:
                            self.cap.release()
                            self.cap = None
                        if self.timer.isActive():
                            self.timer.stop()
                    else:
                        if os.path.exists(save_path):
                            os.remove(save_path)
                        if predicted_class == 2:
                            self.show_and_say("Hatalı Görüntü! Tekrar Deneyiniz.", "Hatalı Görüntü! Tekrar Deneyiniz")
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YoloMediapipeApp(app)
    window.show()
    sys.exit(app.exec())