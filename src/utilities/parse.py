import os
from typing import List, Union
from pydub import AudioSegment
from urllib.request import url2pathname
from PyQt5.QtWidgets import QMessageBox
from utilities import open_audio_dialogue
from datatypes import Translation, Transcription, ConverterComponents, ConverterData
from widgets.warning import WarningMessage


def match_translations(transcription: Transcription,
                       translations: List[Translation]) -> Union[None, str]:
    for translation in translations:
        if transcription.time_matches_translation(translation):
            return translation.translation
    return None


def extract_translations(translation_tier: str,
                         components: ConverterComponents,
                         data: ConverterData) -> List[Translation]:
    elan_translations = data.eaf_object.get_annotation_data_for_tier(translation_tier)
    components.progress_bar.show()
    components.status_bar.showMessage('Processing translations...')
    translations = []
    translation_count = len(elan_translations)
    completed_count = 0
    for index in range(translation_count):
        components.progress_bar.update_progress(completed_count / translation_count)
        translation = Translation(index=index,
                                  start=int(elan_translations[index][0]),
                                  end=int(elan_translations[index][1]),
                                  translation=elan_translations[index][2])
        translations.append(translation)
        completed_count += 1
    components.progress_bar.hide()
    return translations


def extract_transcriptions(transcription_tier: str,
                           components: ConverterComponents,
                           data: ConverterData,
                           audio_file) -> List[Transcription]:
    completed_count = 0
    elan_transcriptions = data.eaf_object.get_annotation_data_for_tier(transcription_tier)
    components.status_bar.showMessage('Processing transcriptions...')
    transcription_count = len(elan_transcriptions)
    transcriptions = []
    for index in range(transcription_count):
        components.progress_bar.update_progress(completed_count / transcription_count)
        transcription = Transcription(index=index,
                                      transcription=elan_transcriptions[index][2],
                                      start=int(elan_transcriptions[index][0]),
                                      end=int(elan_transcriptions[index][1]),
                                      media=audio_file)
        transcription.translation = match_translations(transcription, data.translations)
        transcriptions.append(transcription)
        completed_count += 1
    components.progress_bar.hide()
    return transcriptions


def extract_elan_data(transcription_tier: str,
                      translation_tier: str,
                      data: ConverterData,
                      components: ConverterComponents) -> None:
    if translation_tier != 'None':
        data.translations = extract_translations(translation_tier, components, data)
    else:
        data.translations = []
    audio_file = get_audio_file(data)
    data.transcriptions = extract_transcriptions(transcription_tier, components, data, audio_file)


def get_audio_file(data: ConverterData) -> AudioSegment:
    if data.audio_file:
        return data.audio_file
    linked_files = data.eaf_object.get_linked_files()
    absolute_path_media_file = url2pathname(linked_files[0]['MEDIA_URL'])
    relative_path_media_file = os.path.join('/'.join(data.elan_file.split('/')[:-1]),
                                            linked_files[0]['RELATIVE_MEDIA_URL'])

    # TODO: Change all of this to AudioSegment.from_file(path, format)

    if os.path.isfile(absolute_path_media_file):
        audio_data = AudioSegment.from_wav(absolute_path_media_file)
    elif os.path.isfile(relative_path_media_file):
        audio_data = AudioSegment.from_wav(relative_path_media_file)
    else:
        warning_message = WarningMessage()
        choice = warning_message.warning(warning_message, 'Warning',
                                         f'Warning: Could not find media file {absolute_path_media_file}. '
                                         f'Would you like to locate it manually?',
                                         QMessageBox.No | QMessageBox.Yes)
        found_path_audio_file = None
        if choice == QMessageBox.Yes:
            found_path_audio_file = open_audio_dialogue()
        if found_path_audio_file:
            audio_data = AudioSegment.from_wav(found_path_audio_file)
        else:
            audio_data = None
    return audio_data
