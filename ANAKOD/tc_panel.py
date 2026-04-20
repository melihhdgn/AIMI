import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from style import APP_STYLE

class TcPanel(QWidget):
    def __init__(self, on_success_callback, tc_folder_base="patient_data"):
        super().__init__()
        self.on_success_callback = on_success_callback
        self.tc_folder_base = tc_folder_base
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(APP_STYLE)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 80, 40, 80)
        main_layout.setSpacing(55)

        # ------- Sol: Giriş Kutusu (Dikey Ortalanmış) ---------
        left_layout = QVBoxLayout()
        left_layout.setSpacing(18)

        self.title = QLabel("TC Kimlik No ile Giriş")
        self.title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom:12px")
        left_layout.addWidget(self.title)

        self.tc_box = QFrame()
        self.tc_box.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f2f8ff, stop:1 #b3d8ff);
                border: 2px solid #2196f3;
                border-radius: 12px;
                padding: 18px 12px;
            }
        """)
        tc_box_layout = QVBoxLayout(self.tc_box)
        tc_box_layout.setSpacing(10)
        tc_box_layout.setContentsMargins(15, 10, 15, 10)

        self.tc_label = QLabel("TC Kimlik Giriniz")
        self.tc_label.setStyleSheet("font-size:17px; font-weight:bold; color:#1565c0;")
        tc_box_layout.addWidget(self.tc_label)

        self.tc_input = QLineEdit()
        self.tc_input.setPlaceholderText("TC Kimlik No (11 haneli)")
        self.tc_input.setMaxLength(11)
        self.tc_input.returnPressed.connect(self.try_login)
        tc_box_layout.addWidget(self.tc_input)

        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.clicked.connect(self.try_login)
        tc_box_layout.addWidget(self.login_btn)

        left_layout.addWidget(self.tc_box)

        # Dikey ortalamak için bir dış layout ile üst-alt stretch ekle
        left_outer_layout = QVBoxLayout()
        left_outer_layout.addStretch(2)
        left_outer_layout.addLayout(left_layout)
        left_outer_layout.addStretch(3)

        # ------- Sağ: aimi.png Fotoğrafı (Dikey Ortada) ---------
        right_layout = QVBoxLayout()
        right_layout.addStretch(1)
        self.aimi_label = QLabel()
        pix = QPixmap("aimi.png")
        # İsteğe göre genişlik ayarlanabilir:
        # pix = pix.scaledToWidth(220, Qt.TransformationMode.SmoothTransformation)
        self.aimi_label.setPixmap(pix)
        self.aimi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.aimi_label)
        right_layout.addStretch(1)

        main_layout.addLayout(left_outer_layout, 2)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    def try_login(self):
        tc = self.tc_input.text().strip()
        if len(tc) == 11 and tc.isdigit():
            folder_path = os.path.join(self.tc_folder_base, tc)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            self.on_success_callback(tc, folder_path)
        else:
            QMessageBox.warning(self, "Hata", "Geçersiz TC Kimlik No! Lütfen 11 haneli sayısal bir değer girin.")