from typing import NewType
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QComboBox, \
    QMainWindow
from widgets.converter import ConverterWidget


class SettingsWindow(QDialog):
    def __init__(self,
                 parent: QMainWindow = None,
                 converter: ConverterWidget = None
                 ) -> None:
        super().__init__(parent)
        self.converter = converter
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
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 1, 7, 1, 1)
        cancel_button = QPushButton('Cancel')
        self.layout.addWidget(cancel_button, 1, 6, 1, 1)
        self.setLayout(self.layout)

    def on_click_save(self) -> None:
        pass

    def load_settings(self) -> None:
        pass
