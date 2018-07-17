from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QWidget, QLayout
from PyQt5.QtCore import Qt
from utilities.record import SimpleAudioRecorder
from datatypes import Transcription, ConverterData, AppSettings
from typing import Callable


class RecordWindow(QDialog):
    def __init__(self,
                 parent: QWidget,
                 transcription: Transcription,
                 data: ConverterData,
                 update_button: Callable,
                 settings: AppSettings) -> None:
        super().__init__(parent)
        self.update_button = update_button
        self.transcription = transcription
        self.data = data
        self.settings = settings
        self.layout = QGridLayout()
        self.init_ui()
        self.recorder = None
        self.output = None

    def init_ui(self) -> None:
        self.setWindowTitle('Record')
        self.setMinimumWidth(200)
        instruction_text = f'<html>Click and hold the button below to record.<br/>' \
                           f'Releasing the button will stop the recording.<br/>'
        if self.transcription.transcription:
            instruction_text += f'<br/><strong>Word: {self.transcription.transcription}</strong><br/></html>'
        instruction_label = QLabel(instruction_text)
        instruction_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instruction_label, 0, 0, 1, 9)
        record_button = QPushButton()
        record_button.setStyleSheet('QPushButton{background-color: red;'
                                    '            border-radius: 50%;'
                                    '            height: 100px;'
                                    '            width: 100px;'
                                    '            max-width: 100px;}\n'
                                    'QPushButton:hover {border: 5px solid darkred}'
                                    'QPushButton:pressed {background-color: darkred}')
        record_button.pressed.connect(self.on_press_record)
        record_button.released.connect(self.on_release_record)
        self.layout.addWidget(record_button, 1, 0, 1, 9)
        self.layout.setAlignment(record_button, Qt.AlignCenter)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 2, 7, 1, 1)
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 2, 8, 1, 1)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.layout)

    def on_press_record(self) -> None:
        self.recorder = SimpleAudioRecorder(data=self.data,
                                            transcription=self.transcription,
                                            settings=self.settings)
        self.recorder.start_recording()

    def on_release_record(self) -> None:
        self.output = self.recorder.stop_recording()

    def on_click_save(self) -> None:
        try:
            if self.output:
                self.transcription.set_blank_sample()
                self.transcription.sample.set_sample(self.output)
                self.update_button()
        except Exception:
            pass
        self.close()

    def on_click_cancel(self) -> None:
        self.close()
