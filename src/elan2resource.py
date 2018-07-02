import os
import sys
import pympi
import tempfile
import shutil
import math
from pygame import mixer
from functools import partial
from PyQt5.QtWidgets import QApplication, QFileDialog, QWidget, QLabel, QPushButton, \
    QGridLayout, QHBoxLayout, QLineEdit, QComboBox, QTableWidget, QHeaderView, \
    QTableWidgetItem, QCheckBox, QMainWindow, QMessageBox, QProgressBar, QFrame, \
    QAction, QStatusBar, QDialog
from PyQt5.QtGui import QIcon, QDesktopServices, QMouseEvent, QPixmap
from PyQt5.QtCore import Qt, QSize, QUrl, pyqtSignal
from moviepy.editor import AudioFileClip
from os.path import expanduser
from urllib.request import url2pathname
from typing import NewType, Union, List
from box import Box

MainWindow = NewType('MainWindow', QMainWindow)
ExportProgressBarWidget = NewType('ExportProgressBarWidget', QProgressBar)
ConverterWidget = NewType('ConverterWidget', QWidget)

TABLE_COLUMNS = {
    'Index': 0,
    'Transcription': 1,
    'Translation': 2,
    'Preview': 3,
    'Image': 4,
    'Include': 5,
}

MATCH_ERROR_MARGIN = 1  # Second
VERSION = '0.02'
REPO_LINK = 'https://github.com/nicklambourne/elan2resource'


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def open_folder_dialogue() -> str:
    file_dialogue = QFileDialog()
    file_dialogue.setOption(QFileDialog.ShowDirsOnly, True)
    file_name = file_dialogue.getExistingDirectory(file_dialogue,
                                                   'Choose an export folder',
                                                   expanduser('~'),
                                                   QFileDialog.ShowDirsOnly)
    return file_name


def open_file_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'ELAN Files (*.eaf)',
                                                 options=options)
    return file_name


def open_image_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'Image Files (*.png *.jpg)',
                                                 options=options)
    return file_name


def open_audio_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'Audio Files (*.wav *.mp3)',
                                                 options=options)
    return file_name


class Sample(object):
    def __init__(self,
                 index: int,
                 start: float,
                 end: float,
                 audio_file: AudioFileClip = None,
                 sample_path: str = None,
                 sample_object: AudioFileClip = None):
        self.index = index
        self.start = start
        self.end = end
        self.audio_file = audio_file
        self.sample_path = sample_path
        self.sample_object = sample_object

    def get_sample_file_path(self) -> Union[None, str]:
        if not self.sample_path:
            sample_file = self.audio_file.subclip(t_start=self.start,
                                                  t_end=self.end)
            self.sample_object = sample_file
            temporary_folder = tempfile.mkdtemp()
            sample_file_path = os.path.join(temporary_folder, f'{str(self.index)}.wav')
            sample_file.write_audiofile(sample_file_path)
            return sample_file_path
        return self.sample_path

    def get_sample_file_object(self) -> Union[None, AudioFileClip]:
        self.get_sample_file_path()
        return self.sample_object


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
                 media: AudioFileClip = None) -> None:
        self.index = index
        self.transcription = transcription
        self.translation = translation
        self.image = image
        self.sample = Sample(
            index=index,
            start=start,
            end=end,
            audio_file=media
        )

    def time_matches_translation(self, translation: Translation) -> bool:
        if abs(self.sample.start - translation.start) < MATCH_ERROR_MARGIN and \
                abs(self.sample.end - translation.end) < MATCH_ERROR_MARGIN:
            return True
        else:
            return False

    def __str__(self) -> str:
        return f'<{self.transcription} [{self.sample.start}-{self.sample.end}]>'


class TranslationTableWidget(QTableWidget):
    """
    A table containing transcriptions, translations and buttons for live previews, adding images and selectors for
    inclusion in the export process.
    """

    def __init__(self, num_rows: int) -> None:
        super().__init__(num_rows, 6)
        self.setMinimumHeight(200)
        self.setHorizontalHeaderLabels([''] + [column_name for column_name in list(TABLE_COLUMNS.keys())[1:]])
        self.horizontalHeader().setSectionResizeMode(TABLE_COLUMNS['Transcription'], QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(TABLE_COLUMNS['Translation'], QHeaderView.Stretch)
        self.setColumnWidth(TABLE_COLUMNS['Index'], 30)
        self.setColumnWidth(TABLE_COLUMNS['Preview'], 50)
        self.setColumnWidth(TABLE_COLUMNS['Image'], 50)
        self.setColumnWidth(TABLE_COLUMNS['Include'], 50)
        self.verticalHeader().hide()
        self.setSortingEnabled(False)

    def sort_by_index(self) -> None:
        self.sortByColumn(TABLE_COLUMNS['Index'], Qt.AscendingOrder)

    def show_all_rows(self) -> None:
        for row in range(self.rowCount()):
            self.showRow(row)

    def filter_rows(self, string: str) -> None:
        self.setSortingEnabled(False)
        self.show_all_rows()
        for row in range(self.rowCount()):
            if string not in self.get_cell_value(row, TABLE_COLUMNS['Transcription']) and \
                    string not in self.get_cell_value(row, TABLE_COLUMNS['Translation']):
                self.hideRow(row)

    def get_cell_value(self, row, column) -> str:
        return self.item(row, column).text()

    def get_selected_count(self) -> int:
        count = 0
        for row in range(self.rowCount()):
            count += 1 if self.row_is_checked(row) else 0
        return count

    def row_is_checked(self, row):
        return self.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked()


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


class ConverterComponents(object):
    def __init__(self, progress_bar: ExportProgressBarWidget, status_bar: QStatusBar):
        self.elan_file_field = None
        self.transcription_menu = None
        self.translation_menu = None
        self.filter_field = None
        self.table = None
        self.progress_bar = progress_bar
        self.status_bar = status_bar
        self.tier_selector = None


class ModeSelect(QFrame):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        elan_button = QPushButton()
        elan_button.setIcon(QIcon(QPixmap(resource_path('./img/elan.png'))))
        self.layout.addWidget(elan_button, 0, 0)


class ELANFileField(QWidget):
    def __init__(self, parent: ConverterWidget) -> None:
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.field = QLineEdit()
        self.init_ui()

    def init_ui(self) -> None:
        self.field.setReadOnly(True)
        self.field.setText('Load an ELAN (*.eaf) file.')
        self.layout.addWidget(self.field, 0, 0, 1, 7)
        load_button = QPushButton('Load')
        load_button.clicked.connect(self.on_click_load)
        self.layout.addWidget(load_button, 0, 7, 1, 1)
        self.setLayout(self.layout)

    def on_click_load(self) -> None:
        file_name = open_file_dialogue()
        if file_name:
            self.parent.data.elan_file = file_name
            self.field.setText(file_name)
            self.parent.load_second_stage_widgets(self.parent.components, self.parent.data)


class TierSelector(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.transcription_menu = None
        self.translation_menu = None
        self.init_ui()

    def init_ui(self):
        transcription_label = QLabel('Transcription Tier:')
        self.layout.addWidget(HorizontalLineWidget(), 0, 0, 1, 8)
        self.layout.addWidget(transcription_label, 1, 0, 1, 2)
        self.transcription_menu = QComboBox()
        self.layout.addWidget(self.transcription_menu, 1, 2, 1, 2)
        translation_label = QLabel('Translation Tier:')
        self.layout.addWidget(translation_label, 1, 4, 1, 2)
        self.translation_menu = QComboBox()
        self.layout.addWidget(self.translation_menu, 1, 6, 1, 2)
        import_button = QPushButton('Import')
        import_button.clicked.connect(self.on_click_import)
        self.layout.addWidget(import_button, 2, 0, 1, 8)
        self.setLayout(self.layout)

    def populate_tiers(self, tiers: List[str]) -> None:
        self.transcription_menu.addItems(tiers)
        self.translation_menu.addItems(['None'] + tiers)

    def get_transcription_tier(self) -> None:
        return self.transcription_menu.currentText()

    def get_translation_tier(self) -> None:
        return self.translation_menu.currentText()

    def on_click_import(self) -> None:
        warning_message = QMessageBox()
        choice = warning_message.question(warning_message, 'Warning',
                                          'Warning: Any unsaved work will be overwritten. Proceed?',
                                          QMessageBox.Yes | QMessageBox.No | QMessageBox.Warning)
        if choice == QMessageBox.Yes:
            self.parent.load_third_stage_widgets(self.parent.components, self.parent.data)


class FilterTable(QWidget):
    def __init__(self,
                 data: ConverterData,
                 status_bar) -> None:
        super().__init__()
        self.status_bar = status_bar
        self.layout = QGridLayout()
        self.table = TranslationTableWidget(max(len(data.transcriptions),
                                                len(data.translations)))
        self.filter_field = None
        self.data = data
        self.init_ui()

    def init_ui(self) -> None:
        self.layout.addWidget(HorizontalLineWidget(), 0, 0, 1, 8)
        filter_label = QLabel('Filter Results:')
        self.layout.addWidget(filter_label, 1, 0, 1, 1)
        self.setLayout(self.layout)
        self.filter_field = FilterFieldWidget('', self.table)
        self.layout.addWidget(self.filter_field, 1, 1, 1, 2)
        filter_clear_button = FilterClearButtonWidget('Clear', self.filter_field)
        self.layout.addWidget(filter_clear_button, 1, 3, 1, 1)
        select_all_button = QPushButton('Select All')
        select_all_button.setToolTip('Select/Deselect all currently shown transcriptions\n'
                                     'Note: has no effect on filtered (hidden) results')
        select_all_button.clicked.connect(self.on_click_select_all)
        self.layout.addWidget(select_all_button, 1, 7, 1, 1)
        self.populate_table(self.data.transcriptions)
        self.layout.addWidget(self.table, 2, 0, 1, 8)
        self.setLayout(self.layout)

    def populate_table_row(self, row: int) -> None:
        self.table.setItem(row, TABLE_COLUMNS['Index'], TableIndexCell(row))
        self.table.setItem(row, TABLE_COLUMNS['Transcription'],
                           QTableWidgetItem(self.data.transcriptions[row].transcription))
        self.table.setItem(row, TABLE_COLUMNS['Translation'],
                           QTableWidgetItem(self.data.transcriptions[row].translation))
        PreviewButtonWidget(self, row, self.table)
        ImageButtonWidget(self, row, self.table)
        SelectorCellWidget(row, self.status_bar, self.table)

    def populate_table(self, transcriptions: List[Transcription]) -> None:
        for row in range(len(transcriptions)):
            self.populate_table_row(row)
        self.table.sort_by_index()

    def on_click_select_all(self) -> None:
        if self.all_selected():
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(False)
        else:
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(True)

    def play_sample(self, row: int) -> None:
        sample_file_path = self.data.transcriptions[row].sample.get_sample_file_path()
        mixer.init()
        sound = mixer.Sound(sample_file_path)
        sound.play()

    def on_click_image(self, row: int) -> None:
        image_path = open_image_dialogue()
        if image_path:
            self.data.transcriptions[row].image = image_path
            self.table.cellWidget(row, TABLE_COLUMNS['Image']).swap_icon_yes()

    def all_selected(self) -> bool:
        for row in range(self.table.rowCount()):
            if not self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked() \
                    and not self.table.isRowHidden(row):
                return False
        return True


class ExportLocationField(QWidget):
    def __init__(self, parent: ConverterWidget) -> None:
        super().__init__()
        self.layout = QGridLayout()
        self.parent = parent
        self.data = parent.data
        self.export_location_field = None
        self.init_ui()

    def init_ui(self) -> None:
        self.export_location_field = QLineEdit('Choose an export location')
        self.export_location_field.setReadOnly(True)
        self.layout.addWidget(self.export_location_field, 0, 0, 1, 7)
        choose_export_button = QPushButton('Choose')
        choose_export_button.clicked.connect(self.on_click_choose_export)
        self.layout.addWidget(choose_export_button, 0, 7, 1, 1)
        self.setLayout(self.layout)

    def on_click_choose_export(self) -> None:
        self.data.export_location = open_folder_dialogue()
        if self.data.export_location:
            self.export_location_field.setText(self.data.export_location)
            self.parent.load_fourth_stage_widgets()


class ExportButton(QWidget):
    def __init__(self,
                 parent: ConverterWidget):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self):
        export_button = QPushButton('Export')
        export_button.clicked.connect(self.parent.export_resources)
        self.layout.addWidget(export_button, 0, 0, 1, 8)
        self.setLayout(self.layout)



class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.
    """

    def __init__(self, parent: QMainWindow) -> None:
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
        self.setMinimumWidth(600)
        self.layout.setVerticalSpacing(0)
        self.load_initial_widgets(self.components)
        self.setLayout(self.layout)
        self.show()

    def load_initial_widgets(self, components: ConverterComponents) -> None:
        # First Row (ELAN File Field)
        components.elan_file_field = ELANFileField(self)
        self.layout.addWidget(components.elan_file_field, 0, 0, 1, 8)

    def load_second_stage_widgets(self,
                                  components: ConverterComponents,
                                  data: ConverterData) -> None:
        data.eaf_object = pympi.Elan.Eaf(data.elan_file)
        components.tier_selector = TierSelector(self)
        components.tier_selector.populate_tiers(list(data.eaf_object.get_tier_names()))
        self.layout.addWidget(components.tier_selector, 1, 0, 1, 8)

    def load_third_stage_widgets(self,
                                 components: ConverterComponents,
                                 data: ConverterData) -> None:
        data.audio_file = self.get_audio_file()
        transcription_tier = components.tier_selector.get_transcription_tier()
        translation_tier = components.tier_selector.get_translation_tier()
        self.extract_elan_data(transcription_tier, translation_tier)
        # Sixth Row (Filter & Selector)
        filter_table = FilterTable(self.data, self.components.status_bar)
        self.layout.addWidget(filter_table, 2, 0, 1, 8)
        self.components.table = filter_table.table
        # Eighth Row (Export Location)
        components.export_location_field = ExportLocationField(self)
        self.layout.addWidget(components.export_location_field, 3, 0, 1, 8)

    def load_fourth_stage_widgets(self) -> None:
        # Ninth Row (Export Button)
        export_button = ExportButton(self)
        self.layout.addWidget(export_button, 4, 0, 1, 8)

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
                                      start=int(elan_translations[index][0]) / 1000,
                                      end=int(elan_translations[index][1]) / 1000,
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
                                          start=int(elan_transcriptions[index][0]) / 1000,
                                          end=int(elan_transcriptions[index][1]) / 1000,
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

    def populate_table_row(self,
                           row: int,
                           table: TranslationTableWidget) -> None:
        table.setItem(row, TABLE_COLUMNS['Index'], TableIndexCell(row))
        table.setItem(row, TABLE_COLUMNS['Transcription'],
                      QTableWidgetItem(self.data.transcriptions[row].transcription))
        table.setItem(row, TABLE_COLUMNS['Translation'],
                      QTableWidgetItem(self.data.transcriptions[row].translation))
        PreviewButtonWidget(self, row, table)
        ImageButtonWidget(self, row, table)
        SelectorCellWidget(row, self.components.status_bar, table)

    def populate_table(self,
                       table: TranslationTableWidget) -> None:
        for row in range(len(self.data.transcriptions)):
            self.populate_table_row(row, table)
        table.sort_by_index()
        self.parent.statusBar().showMessage(f'Imported {len(self.data.transcriptions)} transcriptions')

    def get_export_paths(self) -> Box:
        return Box({
            'transcription': make_file_if_not_exists(os.path.join(self.data.export_location, 'words')),
            'translation': make_file_if_not_exists(os.path.join(self.data.export_location, 'translations')),
            'sound': make_file_if_not_exists(os.path.join(self.data.export_location, 'sounds')),
            'image': make_file_if_not_exists(os.path.join(self.data.export_location, 'images')),
        })

    def create_output_files(self,
                            row: int) -> None:
        export_paths = self.get_export_paths()
        sound_file = self.data.transcriptions[row].sample.get_sample_file_object()
        sound_file.write_audiofile(f'{export_paths.sound}/word{str(row)}.wav')
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
            if self.components.table.row_is_checked(row):
                self.components.status_bar.showMessage(f'Exporting file {completed_count + 1} of {export_count}')
                self.create_output_files(row)
                completed_count += 1
                self.components.progress_bar.update_progress(completed_count / export_count)
        self.components.progress_bar.hide()
        self.components.status_bar.showMessage(f'Exported {str(export_count)} words to {self.data.export_location}')
        QDesktopServices().openUrl(QUrl().fromLocalFile(self.data.export_location))

    def get_audio_file(self) -> AudioFileClip:
        if self.data.audio_file:
            return self.data.audio_file
        linked_files = self.data.eaf_object.get_linked_files()
        absolute_path_media_file = url2pathname(linked_files[0]['MEDIA_URL'])
        relative_path_media_file = os.path.join('/'.join(self.data.elan_file.split('/')[:-1]),
                                                linked_files[0]['RELATIVE_MEDIA_URL'])
        if os.path.isfile(absolute_path_media_file):
            audio_data = AudioFileClip(absolute_path_media_file)
        elif os.path.isfile(relative_path_media_file):
            audio_data = AudioFileClip(relative_path_media_file)
        else:
            warning_message = QMessageBox()
            choice = warning_message.question(warning_message, 'Warning',
                                              f'Warning: Could not find media file {absolute_path_media_file}. '
                                              f'Would you like to locate it manually?',
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Warning)
            found_path_audio_file = None
            if choice == QMessageBox.Yes:
                found_path_audio_file = open_audio_dialogue()
            if found_path_audio_file:
                audio_data = AudioFileClip(found_path_audio_file)
            else:
                audio_data = None
        return audio_data


class SelectorCellWidget(QWidget):
    """
    A custom selector cell for inclusion in the TranslationTable.
    Uses a QCheckbox for selection and deselection.
    """

    def __init__(self, row: int, status_bar: QStatusBar, table: TranslationTableWidget) -> None:
        super().__init__()
        self.status_bar = status_bar
        self.table = table
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.selector = QCheckBox()
        self.selector.stateChanged.connect(self.update_select_count)
        self.layout.addWidget(self.selector)
        self.setLayout(self.layout)
        tooltip = 'Check to include in export\nUncheck to exclude from export'
        self.setToolTip(tooltip)
        self.selector.setToolTip(tooltip)
        self.table.setCellWidget(row, TABLE_COLUMNS['Include'], self)

    def update_select_count(self) -> None:
        self.status_bar.showMessage(f'{self.table.get_selected_count()} '
                                    f'items selected for export')


class PreviewButtonWidget(QPushButton):
    """
    Custom button for previewing an audio clip.
    """

    def __init__(self,
                 parent: FilterTable,
                 row: int,
                 table: TranslationTableWidget) -> None:
        super().__init__()
        self.parent = parent
        image_icon = QIcon(resource_path('./img/play.png'))
        self.setIcon(image_icon)
        self.clicked.connect(partial(self.parent.play_sample, row))
        self.setToolTip('Left click to hear a preview of the audio for this word')
        table.setCellWidget(row, TABLE_COLUMNS['Preview'], self)


class ImageButtonWidget(QPushButton):
    """
    Custom button for adding and removing images related to particular translations. For inclusion in rows of the
    TranslationTable.
    """
    rightClick = pyqtSignal()

    def __init__(self,
                 parent: FilterTable,
                 row: int,
                 table: TranslationTableWidget) -> None:
        super().__init__()
        self.parent = parent
        self.row = row
        self.image_icon_no = QIcon(resource_path('./img/image-no.png'))
        self.image_icon_yes = QIcon(resource_path('./img/image-yes.png'))
        self.setIcon(self.image_icon_no)
        self.clicked.connect(partial(self.parent.on_click_image, row))
        self.setToolTip('Left click to choose an image for this word\n'
                        'Right click to delete the existing image')
        self.rightClick.connect(self.remove_image)
        table.setCellWidget(row, TABLE_COLUMNS['Image'], self)

    def swap_icon_yes(self) -> None:
        self.setIcon(self.image_icon_yes)

    def swap_icon_no(self) -> None:
        self.setIcon(self.image_icon_no)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QPushButton.mousePressEvent(self, event)

        if event.button() == Qt.RightButton:
            self.rightClick.emit()

    def remove_image(self) -> None:
        self.parent.data.transcriptions[self.row].image = None
        self.swap_icon_no()


class ApplicationIcon(QIcon):
    """
    Custom icon for the application to appear in the task bar (and in the MainWindow header on Windows).
    """

    def __init__(self) -> None:
        super().__init__()
        self.addFile(resource_path('./img/language-48.png'), QSize(48, 48))
        self.addFile(resource_path('./img/language-96.png'), QSize(96, 96))
        self.addFile(resource_path('./img/language-192.png'), QSize(192, 192))
        self.addFile(resource_path('./img/language-256.png'), QSize(256, 256))


class FilterFieldWidget(QLineEdit):
    """
    Custom text input field connected to a table.
    Text input to the field will filter the entries in the table.
    """

    def __init__(self, string: str, table: TranslationTableWidget) -> None:
        super().__init__(string)
        self.table = table
        self.textChanged.connect(self.update_table)

    def update_table(self, p_str) -> None:
        if p_str == '':
            self.table.show_all_rows()
        else:
            self.table.filter_rows(p_str)


class FilterClearButtonWidget(QPushButton):
    """
    Custom button connected to a FilterFieldWidget which clears the field, triggering the associated table to show all
    rows.
    """

    def __init__(self, name: str, field: QLineEdit) -> None:
        super().__init__(name)
        self.field = field
        self.clicked.connect(self.clear_filter)
        self.setToolTip('Left click to clear filters and\n'
                        'show all imported transcriptions')

    def clear_filter(self) -> None:
        self.field.setText('')


class TableIndexCell(QTableWidgetItem):
    """
    Custom table cell widget for displaying the index of the given row (centred).
    """

    def __init__(self, value: int) -> None:
        super().__init__()
        self.setTextAlignment(Qt.AlignCenter)
        self.setData(Qt.EditRole, value + 1)


class ExportProgressBarWidget(QProgressBar):
    """
    Custom progress bar for showing the progress of exporting transcription/translation/image/sound files.
    """

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.setMaximum(100)
        self.setMinimum(0)
        self.setValue(0)

    def update_progress(self, value: Union[float, int]) -> None:
        self.setValue(math.ceil(value * 100))
        self.app.processEvents()


class HorizontalLineWidget(QFrame):
    """
    Horizontal separator for delineating separate sections of the interface.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class AboutWindow(QDialog):
    def __init__(self, parent: QMainWindow = None) -> None:
        super().__init__(parent)
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        logo_label = QLabel()
        logo_image = QPixmap(resource_path('./img/language-256.png')).scaledToHeight(100)
        logo_label.setPixmap(logo_image)
        self.layout.addWidget(logo_label, 0, 1, 1, 1)
        name_label = QLabel('<b>ELAN Resource Creator</b>')
        name_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(name_label, 1, 0, 1, 3)
        version_label = QLabel(f'Version {VERSION}')
        version_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(version_label, 2, 0, 1, 3)
        link_label = QLabel(f'<a href="{REPO_LINK}">Report Issues Here</a>')
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setTextFormat(Qt.RichText)
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_label.setOpenExternalLinks(True)
        self.layout.addWidget(link_label, 3, 0, 1, 3)
        self.setLayout(self.layout)
        self.show()


class MainWindow(QMainWindow):
    """
    The primary window for the application which houses the Converter, menus, statusbar and progress bar.
    """

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.title = 'Language Resource Creator'
        self.converter = None
        self.progress_bar = None
        self.bar = self.menuBar()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle(self.title)
        self.progress_bar = ExportProgressBarWidget(self.app)
        self.converter = ConverterWidget(parent=self)
        self.setCentralWidget(self.converter)
        self.statusBar().showMessage('Load an ELAN file to get started')
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
        self.init_menu()

    def init_menu(self) -> None:
        file = self.bar.addMenu('File')
        file.addAction('Preferences')

        reset = QAction('Reset', self)
        reset.triggered.connect(self.on_click_reset)
        reset.setShortcut('Ctrl+R')
        file.addAction(reset)

        quit = QAction('Quit', self)
        quit.setShortcut('Ctrl+Q')
        quit.triggered.connect(self.close)
        file.addAction(quit)

        help = self.bar.addMenu('Help')
        about = QAction('About', self)
        about.setShortcut('Ctrl+A')
        about.triggered.connect(self.on_click_about)
        help.addAction(about)

    def on_click_about(self) -> None:
        about = AboutWindow(self)
        about.show()

    def on_click_reset(self):
        self.init_ui()
        self.resize(0, 0)


def make_file_if_not_exists(path: str) -> str:
    """
    Creates a folder at the given location if one does not already exists and returns the now extant folder.
    :param path: a string representing a path to a folder that may or may not already exist.
    :return: the same folder path it was given (now definitely exists).
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path


if __name__ == '__main__':
    App = QApplication(sys.argv)
    App.setWindowIcon(ApplicationIcon())
    Main = MainWindow(App)
    Main.show()
    sys.exit(App.exec_())
