from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMultimedia, QAudioEncoderSettings, QVideoEncoderSettings, QAudioRecorder
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QGridLayout
import sys
import os


class SimpleAudioRecorder(QAudioRecorder):
    def __init__(self):
        super().__init__()

    def start_recording(self):
        settings = QAudioEncoderSettings()
        settings.setCodec('audio/pcm')
        settings.setChannelCount(1)
        settings.setBitRate(96000)
        settings.setSampleRate(44100)
        settings.setQuality(QMultimedia.VeryHighQuality)
        settings.setEncodingMode(QMultimedia.ConstantQualityEncoding)
        container = 'audio/x-wav'

        self.setEncodingSettings(settings, QVideoEncoderSettings(), container)

        file_path = os.path.join(os.getcwd(), 'test.wav')

        print(file_path)

        self.setOutputLocation(QUrl.fromLocalFile(file_path))
        self.record()
        print('Started Recording')

    def stop_recording(self):
        self.stop()
        print('Stopped Recording')


class Content(QWidget):
    def __init__(self, recorder):
        super().__init__()
        self.layout = QGridLayout()
        self.recorder = recorder
        self.init_ui()

    def init_ui(self):
        start_button = QPushButton('Start')
        start_button.clicked.connect(self.recorder.start_recording)
        self.layout.addWidget(start_button, 0, 0)
        stop_button = QPushButton('Stop')
        stop_button.clicked.connect(self.recorder.stop_recording)
        self.layout.addWidget(stop_button, 0, 1)
        self.setLayout(self.layout)
        self.show()


if __name__ == '__main__':
    App = QApplication(sys.argv)
    Main = QMainWindow()
    Main.show()
    recorder = SimpleAudioRecorder()
    content = Content(recorder)
    Main.setCentralWidget(content)

    sys.exit(App.exec_())