from PyQt5.QtWidgets import QStatusBar, QProgressBar
from typing import NewType


ProgressBarWidget = NewType('ProgressBarWidget', QProgressBar)


class ConverterData(object):
    def __init__(self) -> None:
        self.elan_file = None
        self.export_location = None
        self.images = None
        self.eaf_object = None
        self.audio_file = None
        self.transcriptions = []
        self.translations = []
        self.temp_file = None
        self.mode = None


class ConverterComponents(object):
    def __init__(self, progress_bar: ProgressBarWidget, status_bar: QStatusBar):
        self.elan_file_field = None
        self.transcription_menu = None
        self.translation_menu = None
        self.filter_field = None
        self.filter_table = None
        self.table = None
        self.progress_bar = progress_bar
        self.status_bar = status_bar
        self.tier_selector = None
        self.mode_select = None