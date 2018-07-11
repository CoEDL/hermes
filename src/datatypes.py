import os
import tempfile
from enum import Enum, unique
from pydub import AudioSegment
from typing import NewType, Union, List, Callable


MATCH_ERROR_MARGIN = 1  # Second

@unique
class OperationMode(Enum):
    ELAN = 0
    SCRATCH = 1


class Sample(object):
    def __init__(self,
                 index: int,
                 start: float,
                 end: float,
                 audio_file: AudioSegment = None,
                 sample_path: str = None,
                 sample_object: AudioSegment = None):
        self.index = index
        self.start = start
        self.end = end
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

    def __str__(self) -> str:
        return f'<{self.transcription} {self.sample}>'