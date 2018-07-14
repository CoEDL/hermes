from typing import NewType
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QComboBox, \
    QMainWindow
from widgets.converter import ConverterWidget
from datatypes import AppSettings


class SettingsWindow(QDialog):
    def __init__(self,
                 parent: QMainWindow,
                 settings: AppSettings,
                 converter: ConverterWidget = None) -> None:
        super().__init__(parent)
        self.converter = converter
        self.settings = settings
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle('Settings')
        self.setMinimumWidth(300)
        export_mode_label = QLabel('Export Mode:')
        self.layout.addWidget(export_mode_label, 0, 0, 1, 1)
        export_mode_selector = QComboBox()
        export_mode_selector.addItems(['OPIE', 'Language Manifest File'])
        self.layout.addWidget(export_mode_selector, 0, 1, 1, 7)
        sound_quality_label = QLabel('Sound Quality:')
        self.layout.addWidget(sound_quality_label, 1, 0, 1, 1)
        sound_quality_selector = QComboBox()
        sound_quality_selector.addItems(['Very Low', 'Low', 'Normal', 'High', 'Very High'])
        self.layout.addWidget(sound_quality_selector, 1, 1, 1, 7)
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 2, 7, 1, 1)
        cancel_button = QPushButton('Cancel')
        self.layout.addWidget(cancel_button, 2, 6, 1, 1)
        self.setLayout(self.layout)

    def on_click_save(self) -> None:
        pass

    def load_settings(self) -> None:
        pass
