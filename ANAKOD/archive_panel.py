import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

SAVE_DIR = "/home/melih/Desktop/veritabani2"

class ArchivePanel(QWidget):
    def __init__(self, goto_menu_callback, tc_kimlik=None):
        super().__init__()
        self.goto_menu_callback = goto_menu_callback
        self.tc_kimlik = tc_kimlik  # Giriş yapan kişinin TC kimlik numarası
        layout = QVBoxLayout()

        self.header = QLabel("Röntgen Arşivi")
        self.header.setStyleSheet("font-size:20px; font-weight:bold; margin-bottom:8px")
        layout.addWidget(self.header)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(self.refresh_btn)

        self.back_btn = QPushButton("Geri")
        self.back_btn.clicked.connect(self.goto_menu_callback)
        btn_layout.addWidget(self.back_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.current_tc = None  # Şu anda hangi TC'nin fotoğraflarını gösteriyoruz
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        # Giriş yapan TC kimlik varsa, sadece o klasörü göster
        if self.tc_kimlik:
            user_dir = os.path.join(SAVE_DIR, str(self.tc_kimlik))
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            files = [f for f in os.listdir(user_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if not files:
                item = QListWidgetItem("Bu kullanıcıya ait arşiv yok.")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.list_widget.addItem(item)
            else:
                for filename in sorted(files, reverse=True):
                    item = QListWidgetItem(filename)
                    item.setData(Qt.ItemDataRole.UserRole, os.path.join(user_dir, filename))
                    self.list_widget.addItem(item)
            self.current_tc = self.tc_kimlik
        else:
            # TC yoksa hiçbir klasörü gösterme!
            item = QListWidgetItem("Giriş yapmadan arşiv görüntülenemez.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(item)
            self.current_tc = None

    def on_item_double_clicked(self, item):
        if self.current_tc:
            filepath = item.data(Qt.ItemDataRole.UserRole)
            if filepath and os.path.exists(filepath):
                self.show_image(filepath, os.path.basename(filepath))
            else:
                QMessageBox.warning(self, "Hata", "Dosya bulunamadı.")

    def show_image(self, filepath, title):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(700, 700)
        layout = QVBoxLayout()
        label = QLabel()
        pixmap = QPixmap(filepath)
        label.setPixmap(pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()