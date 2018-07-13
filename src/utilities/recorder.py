import os
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMultimedia, QAudioEncoderSettings, QVideoEncoderSettings, QAudioRecorder
from datatypes import AppSettings, Transcription
from widgets.converter import ConverterData


class SimpleAudioRecorder(QAudioRecorder):
    def __init__(self,
                 data: ConverterData,
                 transcription: Transcription,
                 settings: AppSettings = None):
        super().__init__()
        self.settings = settings
        self.temp = data.get_temp_file()
        self.transcription = transcription
        self.file_path = None

    def start_recording(self):
        settings = QAudioEncoderSettings()
        settings.setCodec('audio/pcm')
        settings.setChannelCount(1)
        settings.setBitRate(96000)
        settings.setSampleRate(44100)
        settings.setQuality(self.settings.audio_quality)
        settings.setEncodingMode(QMultimedia.ConstantQualityEncoding)
        container = 'audio/x-wav'

        self.setEncodingSettings(settings, QVideoEncoderSettings(), container)

        self.file_path = os.path.join(self.temp, f'{self.transcription.id}.wav')
        self.setOutputLocation(QUrl.fromLocalFile(self.file_path))

        self.record()

    def stop_recording(self):
        self.stop()
        return self.file_path
