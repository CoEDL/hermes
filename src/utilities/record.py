import os
from datetime import datetime
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMultimedia, QAudioEncoderSettings, QVideoEncoderSettings, QAudioRecorder
from datatypes import AppSettings, Transcription, ConverterData


class SimpleAudioRecorder(QAudioRecorder):
    def __init__(self,
                 data: ConverterData,
                 transcription: Transcription,
                 app_settings: AppSettings = None) -> None:
        super().__init__()
        self.app_settings = app_settings
        self.temp = data.get_temp_file()
        self.transcription = transcription
        self.file_path = None
        self.start_time = datetime.now()

    def start_recording(self) -> None:
        settings = QAudioEncoderSettings()
        settings.setCodec('audio/pcm')
        settings.setChannelCount(1)
        settings.setBitRate(96000)
        settings.setSampleRate(44100)
        settings.setQuality(self.app_settings.audio_quality)
        settings.setEncodingMode(QMultimedia.ConstantQualityEncoding)
        container = 'audio/x-wav'

        self.setEncodingSettings(settings, QVideoEncoderSettings(), container)

        self.file_path = os.path.join(self.temp, f'{self.transcription.id}.wav')
        self.setOutputLocation(QUrl.fromLocalFile(self.file_path))

        self.record()

    def stop_recording(self) -> None:
        self.stop()
        return self.file_path
