import os
import shutil
from box import Box
from datatypes import ConverterData, ConverterComponents
from widgets.table import TABLE_COLUMNS
from .files import make_file_if_not_extant


def get_opie_paths(base_export_location: str) -> Box:
    return Box({
        'transcription': make_file_if_not_extant(os.path.join(base_export_location, 'words')),
        'translation': make_file_if_not_extant(os.path.join(base_export_location, 'translations')),
        'sound': make_file_if_not_extant(os.path.join(base_export_location, 'sounds')),
        'image': make_file_if_not_extant(os.path.join(base_export_location, 'images')),
    })


def create_opie_files(row: int,
                      data: ConverterData,
                      components: ConverterComponents) -> None:
    export_paths = get_opie_paths(data.export_location)
    if data.transcriptions[row].sample:
        sound_file = data.transcriptions[row].sample.get_sample_file_object()
        sound_file.export(f'{export_paths.sound}/word{row}.wav', format='wav')
    image_path = data.transcriptions[row].image
    if image_path:
        image_name, image_extension = os.path.splitext(image_path)
        shutil.copy(image_path, f'{export_paths.image}/word{row}.{image_extension}')
    with open(f'{export_paths.transcription}/word{row}.txt', 'w') as file:
        file.write(f'{components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"])}')
    with open(f'{export_paths.translation}/word{row}.txt', 'w') as file:
        file.write(f'{components.table.get_cell_value(row, TABLE_COLUMNS["Translation"])}')


def create_dict_files(row: int,
                      data: ConverterData) -> None:
    pass


def create_lmf_files(row: int,
                     data: ConverterData) -> None:
    pass
