import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QButtonGroup, QRadioButton, QMessageBox, QApplication
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QMouseEvent
from PyQt6.QtCore import Qt, QPoint
from style import APP_STYLE, SOFT_BLUE

# --- Burada ilgili panelleri import ediyoruz ---
from el_pa import YoloMediapipeApp as ElPaPanel
from lateral import YoloMediapipeApp as LateralPanel
from oblik import YoloMediapipeApp as OblikPanel

REGIONS_FILE = "regions.json"
BODY_IMAGE_PATH = "vücut.png"
CLICK_RADIUS = 30

REGION_OPTIONS = {
    "EL": ["AP", "LATERAL", "OBLİK"],
}

class BodyLabel(QLabel):
    def __init__(self, on_region_selected):
        super().__init__()
        self.on_region_selected = on_region_selected
        self.setMouseTracking(True)
        self.selected_region = None
        self.load_regions()
        self.body_pixmap = QPixmap(BODY_IMAGE_PATH)
        self.setPixmap(self.body_pixmap)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def load_regions(self):
        try:
            with open(REGIONS_FILE, "r", encoding="utf-8") as f:
                self.regions = json.load(f)
        except FileNotFoundError:
            self.regions = {}

    def mousePressEvent(self, event: QMouseEvent):
        clicked_point = event.position().toPoint()
        label_size = self.size()
        scale_x = self.BASE_WIDTH / label_size.width()
        scale_y = self.BASE_HEIGHT / label_size.height()
        scaled_point = QPoint(int(clicked_point.x() * scale_x), int(clicked_point.y() * scale_y))
        for name, (x, y) in self.regions.items():
            if (QPoint(x, y) - scaled_point).manhattanLength() < CLICK_RADIUS:
                self.selected_region = name
                self.on_region_selected(name)
                self.update()
                break
    BASE_WIDTH = 355
    BASE_HEIGHT = 702

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.pixmap():
            return
        painter = QPainter(self)
        label_size = self.size()
        scale_x = label_size.width() / self.BASE_WIDTH
        scale_y = label_size.height() / self.BASE_HEIGHT
        font = painter.font()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)
        for name, (x, y) in self.regions.items():
            draw_x = int(x * scale_x)
            draw_y = int(y * scale_y)
            if name == self.selected_region:
                painter.setBrush(QColor(33, 150, 243, 180))
                painter.setPen(QPen(QColor(60, 120, 220), 2))
            else:
                painter.setBrush(QColor(255, 255, 255, 60))
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(draw_x, draw_y), int(20*scale_x), int(20*scale_y))
            if name == self.selected_region:
                painter.setPen(QColor(33, 150, 243))
                painter.drawText(QPoint(draw_x - 25, draw_y - 35), name.upper())

class BodyMapPanel(QWidget):
    def __init__(self, goto_archive_callback, tc_kimlik):
        super().__init__()
        self.setStyleSheet(APP_STYLE)
        self.selected_region = None
        self.tc_kimlik = tc_kimlik

        self.body_label = BodyLabel(self.region_clicked)
        self.right_panel = QVBoxLayout()
        self.right_widget = QWidget()
        self.right_widget.setLayout(self.right_panel)

        self.header = QLabel("Röntgen Çekimi")
        self.header.setStyleSheet("font-size:20px; font-weight:bold; margin-bottom:8px")

        self.region_label = QLabel("")
        self.region_label.setStyleSheet("font-size:18px; color:#42A5F5; font-weight:bold;")
        self.selection_group = QButtonGroup(self)
        self.options_box = QGroupBox()
        self.options_layout = QVBoxLayout()
        self.options_box.setLayout(self.options_layout)
        self.options_box.hide()
        self.confirm_btn = QPushButton("Kaydet")
        self.confirm_btn.clicked.connect(self.save_selection)
        self.confirm_btn.hide()

        self.archive_btn = QPushButton("Arşiv")
        self.archive_btn.setStyleSheet("margin-top:32px; font-weight:bold;")
        self.archive_btn.clicked.connect(goto_archive_callback)

        self.right_panel.addWidget(self.header)
        self.right_panel.addWidget(self.region_label)
        self.right_panel.addWidget(self.options_box)
        self.right_panel.addWidget(self.confirm_btn)
        self.right_panel.addStretch()
        self.right_panel.addWidget(self.archive_btn)

        layout = QHBoxLayout()
        self.body_label.setFixedSize(int(500*1.3), int(800*1.3))
        layout.addWidget(self.body_label, 3)
        layout.addWidget(self.right_widget, 2)
        self.setLayout(layout)

        # --- Pencere referansları tutulsun (kapanmasın diye) ---
        self.el_pa_window = None
        self.lateral_window = None
        self.oblik_window = None

    def region_clicked(self, region_name):
        self.selected_region = region_name
        self.region_label.setText(region_name.upper())

        self.options_box.hide()
        self.confirm_btn.hide()
        for i in reversed(range(self.options_layout.count())):
            self.options_layout.itemAt(i).widget().deleteLater()
        self.selection_group = QButtonGroup(self)

        options = REGION_OPTIONS.get(region_name.upper(), [])
        if options:
            for i, opt in enumerate(options):
                btn = QRadioButton(opt)
                self.selection_group.addButton(btn, i)
                self.options_layout.addWidget(btn)
            self.options_box.show()
            self.confirm_btn.show()
        else:
            self.options_box.hide()
            self.confirm_btn.hide()

    def save_selection(self):
        checked_btn = self.selection_group.checkedButton()
        if checked_btn is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir çekim türü seçiniz.")
            return
        selection = checked_btn.text()
        QMessageBox.information(self, "Kayıt", f"{self.selected_region} için {selection} seçildi.")

        # EL için AP, LATERAL, OBLİK seçimlerinde ilgili pencereyi aç
        if self.selected_region.upper() == "EL":
            if selection == "AP":
                self.el_pa_window = ElPaPanel(QApplication.instance(), self.tc_kimlik, archive_panel_callback=None, scale_factor=1.4)
                self.el_pa_window.show()
            elif selection == "LATERAL":
                self.lateral_window = LateralPanel(QApplication.instance(), self.tc_kimlik, archive_panel_callback=None, scale_factor=1.4)
                self.lateral_window.show()
            elif selection == "OBLİK":
                self.oblik_window = OblikPanel(QApplication.instance(), self.tc_kimlik, archive_panel_callback=None, scale_factor=1.4)
                self.oblik_window.show()