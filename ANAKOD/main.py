# main.py

import sys
from PyQt6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout, QWidget, QPushButton
from tc_panel import TcPanel
from bodymap_panel import BodyMapPanel
from archive_panel import ArchivePanel
from style import APP_STYLE

class MainMenu(QWidget):
    def __init__(self, goto_archive, goto_bodymap):
        super().__init__()
        self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout()
        layout.addStretch()
        btn1 = QPushButton("Röntgen Arşivi")
        btn1.setFixedHeight(80)
        btn1.setStyleSheet("font-size:22px; background:#ececec; color:#1976d2; border-radius:16px;")
        btn1.clicked.connect(goto_archive)
        btn2 = QPushButton("Röntgen Çek")
        btn2.setFixedHeight(80)
        btn2.setStyleSheet("font-size:22px; background:#ececec; color:#1976d2; border-radius:16px;")
        btn2.clicked.connect(goto_bodymap)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addStretch()
        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIMI Vücut Haritası ve Röntgen Sistemi")
        self.setMinimumSize(1100, 950)
        self.setStyleSheet(APP_STYLE)

        self.stacked = QStackedWidget()
        self.tc_panel = TcPanel(self.tc_login_success)
        self.archive_panel = None  # Dinamik yaratılacak
        self.bodymap_panel = None  # Dinamik yaratılacak
        self.menu_panel = MainMenu(self.show_archive_panel, self.show_bodymap_panel)

        self.stacked.addWidget(self.tc_panel)      # 0
        self.stacked.addWidget(self.menu_panel)    # 1

        root = QVBoxLayout()
        root.addWidget(self.stacked)
        self.setLayout(root)

        self.show_tc_panel()

    def tc_login_success(self, tc, folder_path):
        self.tc = tc
        self.tc_folder = folder_path
        # ArchivePanel ve BodyMapPanel'i TC ile oluştur
        if self.archive_panel:
            self.stacked.removeWidget(self.archive_panel)
        if self.bodymap_panel:
            self.stacked.removeWidget(self.bodymap_panel)
        self.archive_panel = ArchivePanel(self.show_menu_panel, tc_kimlik=self.tc)
        self.bodymap_panel = BodyMapPanel(self.show_archive_panel, tc_kimlik=self.tc)
        self.stacked.addWidget(self.archive_panel) # 2
        self.stacked.addWidget(self.bodymap_panel) # 3
        self.show_menu_panel()

    def show_tc_panel(self):
        self.stacked.setCurrentIndex(0)

    def show_menu_panel(self):
        self.stacked.setCurrentIndex(1)

    def show_archive_panel(self):
        self.archive_panel.refresh_list()
        self.stacked.setCurrentWidget(self.archive_panel)

    def show_bodymap_panel(self):
        self.stacked.setCurrentWidget(self.bodymap_panel)

def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()