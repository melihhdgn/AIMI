DARK_BG = "#030D1B"
LIGHT_CARD = "#F5F7FA"
SOFT_BLUE = "#2196F3"
SOFT_BLUE_LIGHT = "#42A5F5"
SOFT_BORDER = "#2A2D34"
WHITE = "#FFFFFF"
LIGHT_TEXT = "#E0E0E0"
BUTTON_BG = "#F0F3FA"
BUTTON_BG_HOVER = "#2196F350"
BUTTON_TEXT = "#181A20"
SELECTED = SOFT_BLUE

APP_STYLE = f"""
    QWidget {{
        background-color: {DARK_BG};
        color: {WHITE};
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 16px;
    }}
    QLabel, QLineEdit {{
        color: {WHITE};
    }}
    QPushButton {{
        background-color: {BUTTON_BG};
        color: {BUTTON_TEXT};
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        margin: 4px;
    }}
    QPushButton:hover {{
        background-color: {BUTTON_BG_HOVER};
        color: {SOFT_BLUE};
    }}
    QLineEdit {{
        background-color: {LIGHT_CARD};
        border: 1px solid {SOFT_BORDER};
        border-radius: 6px;
        padding: 8px;
        color: {DARK_BG};
    }}
    QGroupBox {{
        border: 1px solid {SOFT_BORDER};
        border-radius: 8px;
        margin-top: 12px;
    }}
    QRadioButton {{
        color: {LIGHT_TEXT};
    }}
    QScrollArea {{
        background: transparent;
    }}
"""