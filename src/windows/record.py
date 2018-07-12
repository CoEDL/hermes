from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt
from utilities.recorder import SimpleAudioRecorder
from datatypes import Transcription, ConverterData
from typing import Callable


class RecordWindow(QDialog):
    def __init__(self,
                 parent: QWidget,
                 transcription: Transcription,
                 data: ConverterData,
                 update_button: Callable):
        super().__init__(parent)
        self.update_button = update_button
        self.transcription = transcription
        self.data = data
        self.layout = QGridLayout()
        self.init_ui()
        self.recorder = None

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
        record_button.pressed.connect(self.on_press_record)
        record_button.released.connect(self.on_release_record)
        self.layout.addWidget(record_button, 1, 1, 1, 1)
        self.setLayout(self.layout)

    def on_press_record(self):
        self.recorder = SimpleAudioRecorder(data=self.data,
                                            transcription=self.transcription)
        self.recorder.start_recording()

    def on_release_record(self):
        output = self.recorder.stop_recording()
        self.transcription.set_blank_sample()
        self.transcription.sample.set_sample(output)
        self.update_button()
