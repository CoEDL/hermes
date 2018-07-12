import os
import shutil
import pympi
from box import Box
from PyQt5.QtWidgets import QStatusBar, QProgressBar, QWidget, QGridLayout, QMainWindow, \
    QMessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from typing import NewType, List, Union
from pydub import AudioSegment
from urllib.request import url2pathname
from datatypes import OperationMode, Transcription, Translation
from utilities import make_file_if_not_extant, open_audio_dialogue
from widgets.mode import ModeSelection
from widgets.elan_import import ELANFileField, TierSelector
from widgets.table import TABLE_COLUMNS, FilterTable
from widgets.export import ExportLocationField, ExportButton
from widgets.warning import WarningMessage


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


class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__()
        self.parent = parent
        self.components = ConverterComponents(
            progress_bar=self.parent.progress_bar,
            status_bar=self.parent.statusBar()
        )
        self.data = ConverterData()
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        self.setMinimumWidth(650)
        self.layout.setVerticalSpacing(0)
        self.load_mode_choice()
        self.setLayout(self.layout)

    def load_mode_choice(self):
        self.components.status_bar.showMessage('Choose a mode to begin')
        self.components.mode_select = ModeSelection(self)
        self.layout.addWidget(self.components.mode_select, 0, 0, 1, 8)

    def load_initial_widgets(self) -> None:
        # First Row (ELAN File Field)
        self.components.status_bar.showMessage('Load an ELAN file to get started')
        self.components.elan_file_field = ELANFileField(self)
        self.components.mode_select.hide()
        self.layout.removeWidget(self.components.mode_select)
        self.layout.addWidget(self.components.elan_file_field, 0, 0, 1, 8)

    def load_second_stage_widgets(self,
                                  components: ConverterComponents,
                                  data: ConverterData) -> None:
        components.status_bar.showMessage('Select transcription and translation tiers, then click import')
        data.eaf_object = pympi.Elan.Eaf(data.elan_file)
        components.tier_selector = TierSelector(self)
        components.tier_selector.populate_tiers(list(data.eaf_object.get_tier_names()))
        self.layout.addWidget(components.tier_selector, 1, 0, 1, 8)

    def load_third_stage_widgets(self,
                                 components: ConverterComponents,
                                 data: ConverterData) -> None:
        if self.data.mode == OperationMode.ELAN:
            data.audio_file = self.get_audio_file()
            transcription_tier = components.tier_selector.get_transcription_tier()
            translation_tier = components.tier_selector.get_translation_tier()
            self.extract_elan_data(transcription_tier, translation_tier)
        else:
            self.components.mode_select.hide()
            self.data.transcriptions.append(Transcription(index=0,
                                                          transcription=""))
        # Sixth Row (Filter & Selector)
        self.components.filter_table = FilterTable(self.data, self.components.status_bar)
        self.layout.addWidget(self.components.filter_table, 2, 0, 1, 8)
        self.components.table = self.components.filter_table.table
        # Eighth Row (Export Location)
        components.export_location_field = ExportLocationField(self)
        self.layout.addWidget(components.export_location_field, 3, 0, 1, 8)
        components.status_bar.showMessage('Select words to include and choose an export location')

    def load_fourth_stage_widgets(self) -> None:
        # Ninth Row (Export Button)
        export_button = ExportButton(self)
        self.layout.addWidget(export_button, 4, 0, 1, 8)
        self.components.status_bar.showMessage('Press the export button to begin the process')

    def extract_translations(self, translation_tier) -> List[Translation]:
        elan_translations = self.data.eaf_object.get_annotation_data_for_tier(translation_tier)
        self.components.progress_bar.show()
        self.components.status_bar.showMessage('Processing translations...')
        translations = []
        translation_count = len(elan_translations)
        completed_count = 0
        for index in range(translation_count):
            self.components.progress_bar.update_progress(completed_count / translation_count)
            translation = Translation(index=index,
                                      start=int(elan_translations[index][0]),
                                      end=int(elan_translations[index][1]),
                                      translation=elan_translations[index][2])
            translations.append(translation)
            completed_count += 1
        self.components.progress_bar.hide()
        return translations

    def extract_transcriptions(self,
                               transcription_tier,
                               audio_file) -> List[Transcription]:
        completed_count = 0
        elan_transcriptions = self.data.eaf_object.get_annotation_data_for_tier(transcription_tier)
        self.components.status_bar.showMessage('Processing transcriptions...')
        transcription_count = len(elan_transcriptions)
        transcriptions = []
        for index in range(transcription_count):
            self.components.progress_bar.update_progress(completed_count / transcription_count)
            transcription = Transcription(index=index,
                                          transcription=elan_transcriptions[index][2],
                                          start=int(elan_transcriptions[index][0]),
                                          end=int(elan_transcriptions[index][1]),
                                          media=audio_file)
            transcription.translation = self.match_translations(transcription, self.data.translations)
            transcriptions.append(transcription)
            completed_count += 1
        self.components.progress_bar.hide()
        return transcriptions

    def extract_elan_data(self,
                          transcription_tier: str,
                          translation_tier: str) -> None:
        if translation_tier != 'None':
            self.data.translations = self.extract_translations(translation_tier)
        else:
            self.data.translations = []
        audio_file = self.get_audio_file()
        self.data.transcriptions = self.extract_transcriptions(transcription_tier, audio_file)

    @staticmethod
    def match_translations(transcription: Transcription,
                           translations: List[Translation]) -> Union[None, str]:
        for translation in translations:
            if transcription.time_matches_translation(translation):
                return translation.translation
        return None

    def get_export_paths(self) -> Box:
        return Box({
            'transcription': make_file_if_not_extant(os.path.join(self.data.export_location, 'words')),
            'translation': make_file_if_not_extant(os.path.join(self.data.export_location, 'translations')),
            'sound': make_file_if_not_extant(os.path.join(self.data.export_location, 'sounds')),
            'image': make_file_if_not_extant(os.path.join(self.data.export_location, 'images')),
        })

    def create_output_files(self,
                            row: int) -> None:
        export_paths = self.get_export_paths()
        if self.data.transcriptions[row].sample:
            sound_file = self.data.transcriptions[row].sample.get_sample_file_object()
            sound_file.export(f'{export_paths.sound}/word{row}.wav', format='wav')
        image_path = self.data.transcriptions[row].image
        if image_path:
            image_name, image_extension = os.path.splitext(image_path)
            shutil.copy(image_path, f'{export_paths.image}/word{row}.{image_extension}')
        with open(f'{export_paths.transcription}/word{row}.txt', 'w') as file:
            file.write(f'{self.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"])}')
        with open(f'{export_paths.translation}/word{row}.txt', 'w') as file:
            file.write(f'{self.components.table.get_cell_value(row, TABLE_COLUMNS["Translation"])}')

    def export_resources(self) -> None:
        self.components.status_bar.clearMessage()
        self.components.progress_bar.show()
        export_count = self.components.table.get_selected_count()
        completed_count = 0
        for row in range(self.components.table.rowCount()):
            if self.components.table.row_is_checked(row) and \
                    self.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"]):
                self.components.status_bar.showMessage(f'Exporting file {completed_count + 1} of {export_count}')
                self.create_output_files(row)
                completed_count += 1
                self.components.progress_bar.update_progress(completed_count / export_count)
        self.components.progress_bar.hide()
        self.components.status_bar.showMessage(f'Exported {str(completed_count)} valid words to '
                                               f'{self.data.export_location}')
        QDesktopServices().openUrl(QUrl().fromLocalFile(self.data.export_location))

    def get_audio_file(self) -> AudioSegment:
        if self.data.audio_file:
            return self.data.audio_file
        linked_files = self.data.eaf_object.get_linked_files()
        absolute_path_media_file = url2pathname(linked_files[0]['MEDIA_URL'])
        relative_path_media_file = os.path.join('/'.join(self.data.elan_file.split('/')[:-1]),
                                                linked_files[0]['RELATIVE_MEDIA_URL'])
        if os.path.isfile(absolute_path_media_file):
            audio_data = AudioSegment.from_wav(absolute_path_media_file)
        elif os.path.isfile(relative_path_media_file):
            audio_data = AudioSegment.from_wav(relative_path_media_file)
        else:
            warning_message = WarningMessage(self)
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