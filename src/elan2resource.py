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
    QAction, QStatusBar, QDialog, QDesktopWidget, QLayout
from PyQt5.QtGui import QIcon, QDesktopServices, QMouseEvent, QPixmap
from PyQt5.QtCore import Qt, QSize, QUrl, pyqtSignal
from moviepy.editor import AudioFileClip
from os.path import expanduser
from urllib.request import url2pathname
from typing import NewType, Union, List, Callable
from box import Box
from enum import Enum, unique

MainWindow = NewType('MainWindow', QMainWindow)
ProgressBarWidget = NewType('ProgressBarWidget', QProgressBar)
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


@unique
class OperationMode(Enum):
    ELAN = 0
    SCRATCH = 1


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
            self.sample_path = os.path.join(temporary_folder, f'{str(self.index)}.wav')
            sample_file.write_audiofile(self.sample_path)
            return self.sample_path
        return self.sample_path

    def get_sample_file_object(self) -> Union[None, AudioFileClip]:
        self.get_sample_file_path()
        return self.sample_object

    def __str__(self):
        return f'[{self.start}-{self.end}]'


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

    def row_is_checked(self, row) -> bool:
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


class ModeButton(QPushButton):
    def __init__(self, icon_path: str, text: str, on_click: Callable) -> None:
        super().__init__()
        self.icon_path = icon_path
        self.text = text
        self.on_click = on_click
        self.init_ui()

    def init_ui(self) -> None:
        self.setText(self.text)
        pixmap = QPixmap(resource_path(self.icon_path))
        icon = QIcon(pixmap)
        self.clicked.connect(self.on_click)
        self.setIcon(icon)
        self.setIconSize(QSize(100, 100))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("QPushButton {border-radius: 11px;"
                           "             background-color: whitesmoke;"
                           "             border: 1px solid lightgrey;"
                           "             padding: 5px;}\n"
                           "QPushButton:hover {background-color: lightgrey;}\n"
                           "QPushButton:pressed {background-color: grey;"
                           "                     color: whitesmoke}")


class ModeSelection(QWidget):
    def __init__(self, parent: ConverterWidget) -> None:
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        elan_button = ModeButton('./img/elan.png',
                                 'Import ELAN File',
                                 on_click=self.on_click_elan)
        self.layout.addWidget(elan_button, 0, 0, 1, 1)
        scratch_button = ModeButton('./img/scratch.png',
                                    'Start From Scratch',
                                    on_click=self.on_click_scratch)
        self.layout.addWidget(scratch_button, 0, 1, 1, 1)
        self.setLayout(self.layout)

    def on_click_elan(self) -> None:
        self.parent.data.mode = OperationMode.ELAN
        self.parent.load_initial_widgets()

    def on_click_scratch(self) -> None:
        self.parent.data.mode = OperationMode.SCRATCH
        self.parent.load_third_stage_widgets(self.parent.components, self.parent.data)


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
        if self.parent.components.table:
            warning_message = WarningMessage(self.parent)
            choice = warning_message.warning(warning_message, 'Warning',
                                             'Warning: Any unsaved work will be overwritten. Proceed?',
                                             QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.No:
                return
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
        if self.data.mode == OperationMode.ELAN:
            self.layout.addWidget(HorizontalLineWidget(), 0, 0, 1, 8)
        filter_label = QLabel('Filter Results:')
        self.layout.addWidget(filter_label, 1, 0, 1, 1)
        self.setLayout(self.layout)
        self.filter_field = FilterFieldWidget('', self.table)
        self.layout.addWidget(self.filter_field, 1, 1, 1, 2)
        filter_clear_button = FilterClearButtonWidget('Clear', self.filter_field)
        self.layout.addWidget(filter_clear_button, 1, 3, 1, 1)
        add_row_button = QPushButton('Add Row')
        add_row_button.setToolTip('Left click to add a new blank row to the table')
        add_row_button.clicked.connect(self.add_blank_row)
        self.layout.addWidget(add_row_button, 1, 6, 1, 1)
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
        PreviewButtonWidget(self, row, self.table, transcription=self.data.transcriptions[row])
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

    def all_selected(self) -> bool:
        for row in range(self.table.rowCount()):
            if not self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked() \
                    and not self.table.isRowHidden(row):
                return False
        return True

    def add_blank_row(self):
        new_row_index = self.table.rowCount()
        self.table.insertRow(new_row_index)
        self.data.transcriptions.append(Transcription(index=new_row_index,
                                                      transcription=""))
        self.populate_table_row(self.table.rowCount() - 1)


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
                 parent: ConverterWidget) -> None:
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        export_button = QPushButton('Export')
        export_button.clicked.connect(self.on_click_export)
        self.layout.addWidget(export_button, 0, 0, 1, 8)
        self.setLayout(self.layout)

    def on_click_export(self) -> None:
        if self.parent.components.table.get_selected_count() == 0:
            warning_message = WarningMessage(self.parent)
            warning_message.warning(warning_message, 'Warning',
                                    f'You have not selected any items to export.\n'
                                    f'Please select at least one item to continue.',
                                    QMessageBox.Yes)
        else:
            if not self.export_directory_empty():
                warning_message = WarningMessage(self.parent)
                decision = warning_message.warning(warning_message, 'Warning',
                                                   f'There are already files in the selected output folder.\n'
                                                   f'Existing files will be overwritten.\n'
                                                   f'Are you sure you want to continue.',
                                                   QMessageBox.Yes | QMessageBox.No)
                if decision == QMessageBox.Yes:
                    self.parent.export_resources()
            else:
                self.parent.export_resources()

    def export_directory_empty(self) -> bool:
        if os.listdir(self.parent.data.export_location):
            return False
        return True


class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.
    """

    def __init__(self, parent: MainWindow) -> None:
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
            warning_message = WarningMessage(self)
            choice = warning_message.warning(warning_message, 'Warning',
                                             f'Warning: Could not find media file {absolute_path_media_file}. '
                                             f'Would you like to locate it manually?',
                                             QMessageBox.No | QMessageBox.Yes)
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

    def __init__(self,
                 row: int,
                 status_bar: QStatusBar,
                 table: TranslationTableWidget) -> None:
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
                                    f'valid items selected for export')


class PreviewButtonWidget(QPushButton):
    """
    Custom button for previewing an audio clip.
    """

    def __init__(self,
                 parent: FilterTable,
                 row: int,
                 table: TranslationTableWidget,
                 transcription: Transcription = None) -> None:
        super().__init__()
        self.parent = parent
        self.transcription = transcription
        if self.transcription and self.transcription.sample:
            image_icon = QIcon(resource_path('./img/play.png'))
        else:
            image_icon = QIcon(resource_path('./img/no_sample.png'))
        self.setIcon(image_icon)
        self.clicked.connect(partial(self.play_sample, self.transcription))
        self.setToolTip('Left click to hear a preview of the audio for this word')
        table.setCellWidget(row, TABLE_COLUMNS['Preview'], self)

    def play_sample(self, transcription: Transcription) -> None:
        if transcription.sample:
            sample_file_path = transcription.sample.get_sample_file_path()
            mixer.init()
            sound = mixer.Sound(sample_file_path)
            sound.play()
        else:
            self.parent.status_bar.showMessage('There is no audio for this transcription', 5000)


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
        self.clicked.connect(partial(self.on_click_image, row))
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

    def on_click_image(self, row: int) -> None:
        image_path = open_image_dialogue()
        if image_path:
            self.data.transcriptions[row].image = image_path
            self.parent.table.cellWidget(row, TABLE_COLUMNS['Image']).swap_icon_yes()


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
        self.setFlags(self.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsSelectable))


class ProgressBarWidget(QProgressBar):
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


class SettingsWindow(QDialog):
    def __init__(self,
                 parent: MainWindow = None,
                 converter: ConverterWidget = None
                 ) -> None:
        super().__init__(parent)
        self.converter = converter
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle('Settings')
        self.setMinimumWidth(300)
        export_mode_label = QLabel('Export Mode:')
        self.layout.addWidget(export_mode_label, 0, 0, 1, 1)
        export_mode_selector = QComboBox()
        export_mode_selector.addItems(['Traditional', 'Language Manifest File'])
        self.layout.addWidget(export_mode_selector, 0, 1, 1, 7)
        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 1, 7, 1, 1)
        cancel_button = QPushButton('Cancel')
        self.layout.addWidget(cancel_button, 1, 6, 1, 1)
        self.setLayout(self.layout)

    def on_click_save(self) -> None:
        pass

    def load_settings(self) -> None:
        pass


class AboutWindow(QDialog):
    def __init__(self, parent: MainWindow = None) -> None:
        super().__init__(parent)
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        logo_label = QLabel()
        logo_image = QPixmap(resource_path('./img/language-256.png')).scaledToHeight(100)
        logo_label.setPixmap(logo_image)
        self.layout.addWidget(logo_label, 0, 1, 1, 1)
        name_label = QLabel('<b>Language Resource Creator</b>')
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


class WarningMessage(QMessageBox):
    def __init__(self,
                 parent: ConverterWidget) -> None:
        super().__init__(parent=parent)
        self.init_ui()

    def init_ui(self) -> None:
        self.setIcon(QMessageBox.Warning)
        screen = QDesktopWidget().screenGeometry()
        this = self.sizeHint()
        self.move(screen.width() / 2 - this.width() / 2,
                  screen.height() / 2 - this.height() / 2)


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
        self.table_menu = None
        self.bar = self.menuBar()
        self.init_ui()
        self.init_menu()

    def init_ui(self) -> None:
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowTitle(self.title)
        self.progress_bar = ProgressBarWidget(self.app)
        self.converter = ConverterWidget(parent=self)
        self.setCentralWidget(self.converter)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def init_menu(self) -> None:
        file = self.bar.addMenu('File')

        settings_menu = QAction('Settings', self)
        settings_menu.triggered.connect(self.on_click_settings)
        settings_menu.setShortcut('Ctrl+B')
        file.addAction(settings_menu)

        reset_menu_item = QAction('Reset', self)
        reset_menu_item.triggered.connect(self.on_click_reset)
        reset_menu_item.setShortcut('Ctrl+R')
        file.addAction(reset_menu_item)

        quit_menu_item = QAction('Quit', self)
        quit_menu_item.setShortcut('Ctrl+Q')
        quit_menu_item.triggered.connect(self.close)
        file.addAction(quit_menu_item)

        help_menu = self.bar.addMenu('Help')
        about_menu_item = QAction('About', self)
        about_menu_item.setShortcut('Ctrl+H')
        about_menu_item.triggered.connect(self.on_click_about)
        help_menu.addAction(about_menu_item)

        self.table_menu = self.bar.addMenu('Table')
        add_row_menu_item = QAction('Add Row', self)
        add_row_menu_item.setShortcut('Ctrl+N')
        add_row_menu_item.triggered.connect(self.on_click_add_row)
        self.table_menu.addAction(add_row_menu_item)

    def on_click_about(self) -> None:
        about = AboutWindow(self)
        about.show()

    def on_click_settings(self) -> None:
        settings = SettingsWindow(self, self.converter)
        settings.show()

    def on_click_reset(self) -> None:
        self.init_ui()
        self.shrink()

    def on_click_add_row(self) -> None:
        if self.converter.components.table:
            self.converter.components.filter_table.add_blank_row()

    def shrink(self) -> None:
        self.resize(0, 0)


def make_file_if_not_extant(path: str) -> str:
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
