import os
import shutil
import csv
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
        shutil.copy(image_path, f'{export_paths.image}/word{row}{image_extension}')
    with open(f'{export_paths.transcription}/word{row}.txt', 'w') as file:
        file.write(f'{components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"])}')
    with open(f'{export_paths.translation}/word{row}.txt', 'w') as file:
        file.write(f'{components.table.get_cell_value(row, TABLE_COLUMNS["Translation"])}')


def create_dict_files(row: int,
                      data: ConverterData) -> None:
    transcription = data.transcriptions[row]
    with open(os.path.join(data.export_location, 'dictionary.csv'), 'a') as file:
        writer = csv.writer(file)
        row_data = [
            transcription.transcription,
            transcription.translation
        ]
        if transcription.sample:
            sound_export_path = make_file_if_not_extant(os.path.join(data.export_location, 'sounds'))
            sound_file = data.transcriptions[row].sample.get_sample_file_object()
            sound_file_path = f'{sound_export_path}/{transcription.transcription}-{row}.wav'
            sound_file.export(sound_file_path, format='wav')
            row_data.append(sound_file_path)
        else:
            row_data.append('')
        if transcription.image:
            image_export_path = make_file_if_not_extant(os.path.join(data.export_location, 'images'))
            _, image_extension = os.path.splitext(transcription.image)
            image_file_path = os.path.join(image_export_path,
                                           f'{transcription.transcription}-{row}{image_extension}')
            shutil.copy(transcription.image, image_file_path)
            row_data.append(image_file_path)
        else:
            row_data.append('')
        writer.writerow(row_data)


def create_lmf_files(row: int,
                     data: ConverterData) -> None:
    pass