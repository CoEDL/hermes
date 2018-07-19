import os
import tempfile
from datetime import datetime
from resizeimage import resizeimage
from enum import Enum, unique
from pydub import AudioSegment
from typing import Union
from uuid import uuid4
from tempfile import mkdtemp
from PIL import Image
from PyQt5.QtMultimedia import QMultimedia
from PyQt5.QtWidgets import QProgressBar, QStatusBar

MATCH_ERROR_MARGIN = 1  # Second

AUDIO_QUALITY = {
    "Very Low": QMultimedia.VeryLowQuality,
    "Low": QMultimedia.LowQuality,
    "Normal": QMultimedia.NormalQuality,
    "High": QMultimedia.HighQuality,
    "Very High": QMultimedia.VeryHighQuality
}

AUDIO_QUALITY_REV = {v: k for k, v in AUDIO_QUALITY.items()}


@unique
class OperationMode(Enum):
    ELAN = 0
    SCRATCH = 1


@unique
class OutputMode(Enum):
    OPIE = 0
    LMF = 1
    DICT = 2


OUTPUT_MODE_NAMES = {
    0: "OPIE File Structure",
    1: "Language Manifest File (JSON)",
    2: "Generic Dictionary (CSV)"
}

OUTPUT_MODES_REV = {v: k for k, v in OUTPUT_MODE_NAMES.items()}


def create_lmf(transcription_language: str,
               translation_language: str,
               author: str):
    return {
        "transcription-language": transcription_language,
        "translation-language": translation_language,
        "author": author,
        "created": str(datetime.now()),
        "words": []
    }


class Sample(object):
    def __init__(self,
                 index: int,
                 start: float = None,
                 end: float = None,
                 audio_file: AudioSegment = None,
                 sample_path: str = None,
                 sample_object: AudioSegment = None):
        self.index = index
        self.start = start
        self.end = end
        self.recorded = False
        self.audio_file = audio_file
        self.sample_path = sample_path
        self.sample_object = sample_object

    def get_sample_file_path(self) -> Union[None, str]:
        if not self.sample_path:
            sample_file = self.audio_file[self.start:self.end]
            self.sample_object = sample_file
            temporary_folder = tempfile.mkdtemp()
            self.sample_path = os.path.join(temporary_folder, f'{str(self.index)}.wav')
            sample_file.export(self.sample_path, format='wav')
            return self.sample_path
        return self.sample_path

    def get_sample_file_object(self) -> Union[None, AudioSegment]:
        self.get_sample_file_path()
        return self.sample_object

    def set_sample(self, path):
        self.sample_path = path
        self.sample_object = AudioSegment.from_wav(path)

    def __str__(self):
        return f'[{self.start/1000}-{self.end/1000}]'


class Translation(object):
    def __init__(self,
                 index: int,
                 translation: str,
                 start: float,
                 end: float) -> None:
        self.index = index
        self.translation = translation
        self.start = start
        self.end = end

    def __str__(self):
        return f'<{self.translation} [{self.start}-{self.end}]>'


class Transcription(object):
    def __init__(self,
                 index: int,
                 transcription: str,
                 translation: str = None,
                 image: str = None,
                 start: float = None,
                 end: float = None,
                 media: AudioSegment = None) -> None:
        self.index = index
        self.transcription = transcription
        self.translation = translation
        self.image = image
        self.preview_image = None
        self.id = uuid4()
        self.temp_file = None

        if not (media and start and end):
            self.sample = None
        else:
            self.sample = Sample(
                index=index,
                start=start,
                end=end,
                audio_file=media
            )

    def time_matches_translation(self, translation: Translation) -> bool:
        if not self.sample:
            return False
        if abs(self.sample.start - translation.start) < MATCH_ERROR_MARGIN and \
                abs(self.sample.end - translation.end) < MATCH_ERROR_MARGIN:
            return True
        else:
            return False

    def set_image(self, path_to_image):
        image = Image.open(path_to_image)
        new_image_path = self.get_temp_file() + self.id + '.png'
        image.save(new_image_path, 'PNG')

    def set_blank_sample(self):
        self.sample = Sample(index=self.index)

    def refresh_preview_image(self):
        preview_path = os.path.join(self.get_temp_file(), f'{self.id}.{self.image.format}')
        with open(self.image, 'r+b') as file:
            with Image.open(file) as image:
                preview = resizeimage.resize_contain(image, [250, 250])
                if image.format == 'RBG':
                    preview.convert('RGBA')
                preview.save(preview_path, 'PNG')
                self.preview_image = preview_path
                return self.preview_image

    def get_preview_image(self):
        if self.image and not self.preview_image:
            self.refresh_preview_image()
        return self.preview_image

    def get_temp_file(self):
        if not self.temp_file:
            self.temp_file = mkdtemp()
        return self.temp_file

    def __str__(self) -> str:
        return f'<{self.transcription} {self.sample}>'


class ConverterData(object):
    def __init__(self) -> None:
        self.elan_file = None
        self.export_location = None
        self.eaf_object = None
        self.audio_file = None
        self.transcriptions = []
        self.translations = []
        self.temp_file = None
        self.mode = None
        self.lmf = dict()

    def get_temp_file(self):
        if not self.temp_file:
            self.temp_file = mkdtemp()
        return self.temp_file


class ConverterComponents(object):
    def __init__(self, progress_bar: QProgressBar, status_bar: QStatusBar):
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


class AppSettings(object):
    def __init__(self,
                 output_format: str = OUTPUT_MODE_NAMES[0],
                 microphone: str = 'Default',
                 audio_quality: str = 'Normal'):
        self.output_format = list(OutputMode)[OUTPUT_MODES_REV[output_format]]
        self.microphone = microphone
        self.audio_quality = AUDIO_QUALITY[audio_quality]

    def __str__(self):
        return '\n'.join([f'{key}: {value}' for key, value in self.__dict__.items()])
