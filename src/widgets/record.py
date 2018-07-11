from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt
from typing import NewType


FilterTable = NewType('FilterTable', QWidget)


class RecordWindow(QDialog):
    def __init__(self,
                 parent: FilterTable):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Record')
        self.setMinimumWidth(200)
        instruction_label = QLabel('Click and hold the button below to record.\n'
                                   'Releasing the button will stop the recording.')
        instruction_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instruction_label, 0, 0, 1, 3)
        record_button = QPushButton()
        record_button.setStyleSheet('QPushButton{background-color: red;'
                                    '            border-radius: 50%;'
                                    '            height: 100px;'
                                    '            width: 100px;}\n'
                                    'QPushButton:hover {border: 5px solid darkred}'
                                    'QPushButton:pressed {background-color: darkred}')
        self.layout.addWidget(record_button, 1, 1, 1, 1)
        self.setLayout(self.layout)

    def on_click_record(self):
        pass
