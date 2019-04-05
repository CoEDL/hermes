from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QWidget, QLayout, QAbstractButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
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
        self.record_button = QPushButton()
        self.recording = False
        self.init_ui()
        self.recorder = SimpleAudioRecorder(self.data,
                                            self.transcription,
                                            self.settings)
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
        self.record_button.setStyleSheet(
                                    'QPushButton {border-radius: 50px}'
                                    'QPushButton:pressed {background-color: darkred}')
        self.record_button.setFlat(True)
        self.record_button.setIcon(QIcon('./img/icon-record-96.png'))
        self.record_button.setIconSize(QSize(96, 96))
        # self.record_button.pressed.connect(self.on_press_record)
        # self.record_button.released.connect(self.on_release_record)
        self.record_button.clicked.connect(self.on_click_record)
        self.layout.addWidget(self.record_button, 1, 0, 1, 9)
        self.layout.setAlignment(self.record_button, Qt.AlignCenter)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 3, 7, 1, 1)
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 3, 8, 1, 1)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.layout)

    def on_click_record(self) -> None:
        """Record after clicking record button once, again to stop."""
        if not self.recording:
            self.recording = True
            self.recorder.start_recording()
            self.record_button.setIcon(QIcon('./img/icon-stop-96_3.png'))
            self.record_button.setIconSize(QSize(96, 96))
        else:
            self.recording = False
            self.recorder.stop_recording()
            self.record_button.setIcon(QIcon('./img/icon-record-96.png'))
            self.record_button.setIconSize(QSize(96, 96))
            try:
                self.output = self.recorder.file_path
            except FileNotFoundError:
                self.output = None

    def on_press_record(self) -> None:
        """Functionality not hooked up, for 'hold down button' to record"""
        self.recorder.start_recording()

    def on_release_record(self) -> None:
        """Functionality not hooked up, for 'release button' to stop recording"""
        self.recorder.stop_recording()
        try:
            self.output = self.recorder.file_path
        except FileNotFoundError:
            self.output = None

    def on_click_save(self) -> None:
        if self.output:
            self.transcription.set_blank_sample()
            try:
                self.transcription.sample.set_sample(self.output)
            except FileNotFoundError:
                self.transcription.sample = None
            self.update_button()
        self.close()

    def on_click_cancel(self) -> None:
        self.close()

