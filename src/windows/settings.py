from box import Box
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton, QComboBox, \
    QMainWindow
from PyQt5.QtMultimedia import QAudioRecorder
from widgets.converter import ConverterWidget
from datatypes import AppSettings, AUDIO_QUALITY_REV, AUDIO_QUALITY, OUTPUT_MODE_NAMES, OUTPUT_MODES_REV, OutputMode
from utilities.settings import save_system_settings


class SettingsWindow(QDialog):
    def __init__(self,
                 parent: QMainWindow,
                 converter: ConverterWidget = None) -> None:
        super().__init__(parent)
        self.converter = converter
        self.settings = converter.settings
        self.layout = QGridLayout()
        self.widgets = Box()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle('Settings')
        self.setMinimumWidth(300)

        export_mode_label = QLabel('Export Mode:')
        self.layout.addWidget(export_mode_label, 0, 0, 1, 1)
        self.widgets.export_mode_selector = QComboBox()
        self.widgets.export_mode_selector.addItems([output_mode for output_mode in OUTPUT_MODE_NAMES.values()])
        self.widgets.export_mode_selector.setCurrentIndex(self.settings.output_format.value)
        self.layout.addWidget(self.widgets.export_mode_selector, 0, 1, 1, 7)

        audio_device_label = QLabel('Audio Device')
        self.layout.addWidget(audio_device_label, 1, 0, 1, 1)
        self.widgets.audio_device_selector = QComboBox()
        self.widgets.audio_device_selector.addItems(QAudioRecorder().audioInputs())
        self.widgets.audio_device_selector.setCurrentText(self.settings.microphone)
        self.layout.addWidget(self.widgets.audio_device_selector, 1, 1, 1, 7)

        sound_quality_label = QLabel('Sound Quality:')
        self.layout.addWidget(sound_quality_label, 2, 0, 1, 1)
        self.widgets.sound_quality_selector = QComboBox()
        self.widgets.sound_quality_selector.addItems([k for k in AUDIO_QUALITY.keys()])
        self.widgets.sound_quality_selector.setCurrentText(AUDIO_QUALITY_REV[self.settings.audio_quality])
        self.layout.addWidget(self.widgets.sound_quality_selector, 2, 1, 1, 7)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 3, 7, 1, 1)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 3, 6, 1, 1)
        self.setLayout(self.layout)

    def on_click_save(self) -> None:
        self.settings = AppSettings(output_format=list(OutputMode)[OUTPUT_MODES_REV[self.widgets.export_mode_selector.currentText()]],
                                    microphone=self.widgets.audio_device_selector.currentText(),
                                    audio_quality=self.widgets.sound_quality_selector.currentText())
        save_system_settings(self.settings)
        self.close()

    def on_click_cancel(self) -> None:
        self.close()

    def load_settings(self) -> None:
        pass
