from PyQt5.QtWidgets import QDialog, QFileDialog, QGridLayout, QLabel, QLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from pygame import mixer
from pygame import error as pygerror
from utilities.files import resource_path
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
        self.preview_button = QPushButton('Play Audio')
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
        instruction_text = f'<html>Click record button below to start recording.<br/>' \
                           f'Click the record button again to stop recording.<br/>'
        if self.transcription.transcription:
            instruction_text += f'<hr/><strong><h3>Transcription: {self.transcription.transcription}</h3></strong></html>'
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
        self.record_button.setIcon(QIcon(resource_path('./img/icon-record-96.png')))
        self.record_button.setIconSize(QSize(96, 96))
        self.record_button.setToolTip("Record button: Click to start/stop recording.")
        # self.record_button.pressed.connect(self.on_press_record)
        # self.record_button.released.connect(self.on_release_record)
        self.record_button.clicked.connect(self.on_click_record)
        self.layout.addWidget(self.record_button, 1, 0, 1, 9)
        self.layout.setAlignment(self.record_button, Qt.AlignCenter)

        load_button = QPushButton('Load')
        load_button.setIcon(QIcon(resource_path('./img/icon-audio-file-32.png')))
        load_button.setIconSize(QSize(32, 32))
        load_button.setToolTip("Load a .wav audio file for this transcription.")
        load_button.clicked.connect(self.on_click_load_audio)
        self.layout.addWidget(load_button, 3, 3, 1, 1)

        save_button = QPushButton('Save')
        save_button.setIcon(QIcon(resource_path('./img/icon-save-close-32.png')))
        save_button.setIconSize(QSize(32, 32))
        save_button.setToolTip("Finish and save current audio sample for this transcription.")
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 3, 4, 1, 1)

        self.preview_button.setIcon(QIcon(resource_path('./img/icon-play-32.png')))
        self.preview_button.setIconSize(QSize(32, 32))
        self.preview_button.setToolTip("Playback the recorded or loaded audio file.")
        self.preview_button.clicked.connect(self.on_click_preview)
        if self.transcription.sample and self.transcription.sample.get_sample_file_path():
            self.output = self.transcription.sample.get_sample_file_path()
        else:
            self.preview_button.setEnabled(False)
        self.layout.addWidget(self.preview_button, 3, 5, 1, 1)

        cancel_button = QPushButton('Cancel')
        cancel_button.setIcon(QIcon(resource_path('./img/icon-cancel-32.png')))
        cancel_button.setIconSize(QSize(32, 32))
        cancel_button.setToolTip("Cancel without saving audio.")
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 3, 6, 1, 1)

        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.layout)

        LOG_RECORD_WINDOW.debug("Record Window initialised.")

    def on_click_record(self) -> None:
        """Record after clicking record button once, again to stop."""
        if not self.recording:
            self.recording = True
            self.recorder.start_recording()
            self.record_button.setIcon(QIcon(resource_path('./img/icon-stop-96_3.png')))
            self.record_button.setIconSize(QSize(96, 96))
        else:
            self.recording = False
            self.recorder.stop_recording()
            self.record_button.setIcon(QIcon(resource_path('./img/icon-record-96.png')))
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

    def on_click_load_audio(self) -> None:
        audio_path = QFileDialog().getOpenFileName(self, "Select Audio File to Load", "~", ".wav Audio Files (*.wav)")
        LOG_RECORD_WINDOW.debug(f"Attempt to load audio: {audio_path}")
        if audio_path:
            self.output = audio_path[0]
            self.__set_audio_sample(self.output)
            self.update_button()
            self.preview_button.setEnabled(True)
            LOG_RECORD_WINDOW.info(f"Audio file loaded: {audio_path}")

    def on_click_save(self) -> None:
        if self.output:
            self.__set_audio_sample(self.output)
            self.update_button()
        self.close()

    def __set_audio_sample(self, path: str) -> None:
        try:
            self.transcription.set_blank_sample()
            self.transcription.sample.set_sample(path)
            LOG_RECORD_WINDOW.info(f"Audio sample set from: {path}")
        except FileNotFoundError:
            self.transcription.sample = None
            LOG_RECORD_WINDOW.error(f"Could not load audio: {path} / {FileNotFoundError}")

    def on_click_preview(self) -> None:
        if self.output:
            try:
                LOG_RECORD_WINDOW.debug(f"Previewing Audio: {self.output}")
                mixer.init()
                sound = mixer.Sound(self.output)
                sound.play()
            except pygerror as e:
                LOG_RECORD_WINDOW.error(f"Error on previewing Audio: {e}")

    def on_click_cancel(self) -> None:
        self.close()
