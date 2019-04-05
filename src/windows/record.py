from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QWidget, QLayout, QAbstractButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from pygame import mixer
from utilities.record import SimpleAudioRecorder
from utilities.logger import setup_custom_logger
from datatypes import Transcription, ConverterData, AppSettings
from typing import Callable


LOG_RECORD_WINDOW = setup_custom_logger("Record Window")


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
        self.output = None
        self.init_ui()
        self.recorder = SimpleAudioRecorder(self.data,
                                            self.transcription,
                                            self.settings)

    def init_ui(self) -> None:
        self.setWindowTitle('Record Audio')
        self.setMinimumWidth(200)

        # Header
        instruction_text = f'<html>Click button below to start recording.<br/>' \
                           f'Click the button again to stop recording.<br/>'
        if self.transcription.transcription:
            instruction_text += f'<br/><strong>Word: {self.transcription.transcription}</strong><br/></html>'
        instruction_label = QLabel(instruction_text)
        instruction_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(instruction_label, 0, 0, 1, 9)

        # Buttons
        self.record_button.setStyleSheet('QPushButton{border-radius: 50%;'
                                         '            height: 100px;'
                                         '            width: 100px;'
                                         '            max-width: 100px;}\n'
                                         'QPushButton:pressed {background-color: silver}')
        self.record_button.setFlat(True)
        self.record_button.setIcon(QIcon('./img/icon-record-96.png'))
        self.record_button.setIconSize(QSize(96, 96))
        # self.record_button.pressed.connect(self.on_press_record)
        # self.record_button.released.connect(self.on_release_record)
        self.record_button.clicked.connect(self.on_click_record)
        self.layout.addWidget(self.record_button, 1, 0, 1, 9)
        self.layout.setAlignment(self.record_button, Qt.AlignCenter)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 3, 6, 1, 1)

        self.preview_button = QPushButton('Preview')
        self.preview_button.clicked.connect(self.on_click_preview)
        if self.transcription.sample and self.transcription.sample.get_sample_file_path():
            self.output = self.transcription.sample.get_sample_file_path()
        else:
            self.preview_button.setEnabled(False)
        self.layout.addWidget(self.preview_button, 3, 7, 1, 1)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 3, 8, 1, 1)

        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.layout)

        LOG_RECORD_WINDOW.debug("Record Window initialised.")

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
                self.preview_button.setEnabled(True)
            except FileNotFoundError:
                self.output = None
                LOG_RECORD_WINDOW.error(f"Error on recording: {FileNotFoundError}")

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

    def on_click_preview(self) -> None:
        print(self.output)
        if self.output:
            print(self.output)
            mixer.init()
            sound = mixer.Sound(self.output)
            sound.play()
