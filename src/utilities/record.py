import os
from typing import Union
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMultimedia, QAudioEncoderSettings, QVideoEncoderSettings, QAudioRecorder
from datatypes import AppSettings, Transcription, ConverterData


class SimpleAudioRecorder(QAudioRecorder):
    def __init__(self,
                 data: ConverterData,
                 transcription: Transcription,
                 app_settings: AppSettings) -> None:
        super().__init__()
        self.app_settings = app_settings
        self.temp = data.get_temp_file()
        self.transcription = transcription
        self.file_path = os.path.join(self.temp, f'{self.transcription.id}.wav')
        self.settings = QAudioEncoderSettings()

    def start_recording(self) -> None:
        self.settings.setCodec('audio/pcm')
        self.settings.setChannelCount(1)
        self.settings.setBitRate(96000)
        self.settings.setSampleRate(44100)
        self.settings.setQuality(self.app_settings.audio_quality)
        self.settings.setEncodingMode(QMultimedia.ConstantQualityEncoding)
        container = 'audio/x-wav'
        self.setEncodingSettings(self.settings, QVideoEncoderSettings(), container)
        self.setOutputLocation(QUrl.fromLocalFile(self.file_path))
        self.record()

    def stop_recording(self) -> Union[str, None]:
        self.stop()
        return self.file_path
