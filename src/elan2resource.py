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
    QAction, QStatusBar
from PyQt5.QtGui import QIcon, QDesktopServices, QMouseEvent
from PyQt5.QtCore import Qt, QSize, QUrl, pyqtSignal
from moviepy.editor import AudioFileClip
from os.path import expanduser
from urllib.request import url2pathname
from typing import Union, List
from box import Box

TABLE_COLUMNS = {
    'Index': 0,
    'Transcription': 1,
    'Translation': 2,
    'Preview': 3,
    'Image': 4,
    'Include': 5,
}

MATCH_ERROR_MARGIN = 1  # Second


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


class Translation(object):
    def __init__(self,
                 index: int,
                 translation: str,
                 start: float,
                 end: float):
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
        self.sound = Box({
            'start': start,
            'end': end,
            'audio_file': media,
            'sample_path': None,
            'sample_object': None,
        })

    def get_sample_file_path(self) -> Union[None, str]:
        if not self.sound.sample_path:
            sample_file = self.sound.audio_file.subclip(t_start=self.sound.start,
                                                        t_end=self.sound.end)
            self.sound.sample_object = sample_file
            temporary_folder = tempfile.mkdtemp()
            sample_file_path = os.path.join(temporary_folder, f'{str(self.index)}.wav')
            sample_file.write_audiofile(sample_file_path)
            return sample_file_path
        return self.sound.sample_path

    def get_sample_file_object(self) -> Union[None, AudioFileClip]:
        self.get_sample_file_path()
        return self.sound.sample_object

    def time_matches_translation(self, translation: Translation) -> bool:
        if abs(self.sound.start - translation.start) < MATCH_ERROR_MARGIN and \
                abs(self.sound.end - translation.end) < MATCH_ERROR_MARGIN:
            print(f'{translation.start - MATCH_ERROR_MARGIN} <= {self.sound.start} <= {translation.start + MATCH_ERROR_MARGIN}\n'
                  f'{translation.end - MATCH_ERROR_MARGIN} <= {self.sound.end} <= {translation.end + MATCH_ERROR_MARGIN}')
            print(f'{self}\n{translation}')
            return True
        else:
            return False

    def __str__(self):
        return f'<{self.transcription} [{self.sound.start}-{self.sound.end}]>'


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


class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.
    """

    def __init__(self, parent: QMainWindow) -> None:
        super().__init__()
        self.parent = parent
        self.components = self.init_components()
        self.data = self.init_data()
        self.layout = QGridLayout()
        self.init_ui()

    @staticmethod
    def init_data() -> Box:
        return Box({
            'elan_file': None,
            'export_location': None,
            'images': None,
            'eaf_object': None,
            'audio_file': None,
            'transcriptions': [],
            'translations': [],
        })

    def init_components(self) -> Box:
        return Box({
            'elan_file_field': None,
            'transcription_menu': None,
            'translation_menu': None,
            'filter_field': None,
            'table': None,
            'progress_bar': self.parent.progress_bar,
            'status_bar': self.parent.statusBar(),
        })

    def init_ui(self) -> None:
        self.setMinimumWidth(600)
        self.load_initial_widgets(self.components)
        self.setLayout(self.layout)
        self.show()

    def load_initial_widgets(self, components: Box) -> None:
        # First Row (ELAN File Field)
        components.elan_file_field = QLineEdit('Load an ELAN (*.eaf) file.')
        components.elan_file_field.setReadOnly(True)
        self.layout.addWidget(components.elan_file_field, 0, 0, 1, 7)
        load_button = QPushButton('Load')
        load_button.clicked.connect(self.on_click_load)
        self.layout.addWidget(load_button, 0, 7, 1, 1)

    def load_second_stage_widgets(self, components: Box, data: Box) -> None:
        data.eaf_object = pympi.Elan.Eaf(data.elan_file)
        # Second Row (Tier Selection)
        components.transcription_label = QLabel('Transcription Tier:')
        self.layout.addWidget(components.transcription_label, 2, 0, 1, 2)
        components.transcription_menu = QComboBox()
        components.transcription_menu.addItems(data.eaf_object.get_tier_names())
        self.layout.addWidget(components.transcription_menu, 2, 2, 1, 2)
        components.translation_label = QLabel('Translation Tier:')
        self.layout.addWidget(components.translation_label, 2, 4, 1, 2)
        components.translation_menu = QComboBox()
        components.translation_menu.addItems(data.eaf_object.get_tier_names())
        self.layout.addWidget(components.translation_menu, 2, 6, 1, 2)
        # Third Row (Import Button)
        import_button = QPushButton('Import')
        import_button.clicked.connect(self.on_click_import)
        self.layout.addWidget(import_button, 3, 0, 1, 8)

    def load_third_stage_widgets(self, components: Box, data: Box) -> None:
        data.audio_file = self.get_audio_file()
        transcription_tier = components.transcription_menu.currentText()
        translation_tier = components.translation_menu.currentText()
        self.extract_elan_data(transcription_tier, translation_tier)
        self.layout.addWidget(HorizontalLineWidget(), 4, 0, 1, 8)
        # Sixth Row (Filter & Selector)
        filter_label = QLabel('Filter Results:')
        self.layout.addWidget(filter_label, 5, 0, 1, 1)
        components.table = TranslationTableWidget(len(data.eaf_object.get_annotation_data_for_tier(transcription_tier)))
        components.filter_field = FilterFieldWidget('', components.table)
        self.layout.addWidget(components.filter_field, 5, 1, 1, 2)
        filter_clear_button = FilterClearButtonWidget('Clear', self.components.filter_field)
        self.layout.addWidget(filter_clear_button, 5, 3, 1, 1)
        select_all_button = QPushButton('Select All')
        select_all_button.setToolTip('Select/Deselect all currently shown transcriptions\n'
                                     'Note: has no effect on filtered (hidden) results')
        select_all_button.clicked.connect(self.on_click_select_all)
        self.layout.addWidget(select_all_button, 5, 7, 1, 1)
        # Seventh Row (Table)
        self.populate_table(self.components.table)
        self.layout.addWidget(components.table, 6, 0, 1, 8)
        # Eighth Row (Export Location)
        components.export_location_field = QLineEdit('Choose an export location')
        components.export_location_field.setReadOnly(True)
        self.layout.addWidget(components.export_location_field, 7, 0, 1, 7)
        choose_export_button = QPushButton('Choose')
        choose_export_button.clicked.connect(self.on_click_choose_export)
        self.layout.addWidget(choose_export_button, 7, 7, 1, 1)

    def load_fourth_stage_widgets(self) -> None:
        # Ninth Row (Export Button)
        export_button = QPushButton('Export')
        export_button.clicked.connect(self.export_resources)
        self.layout.addWidget(export_button, 8, 0, 1, 8)

    def extract_elan_data(self, transcription_tier: str, translation_tier: str) -> None:
        self.data.transcriptions = []
        elan_translations = self.data.eaf_object.get_annotation_data_for_tier(translation_tier)
        self.components.progress_bar.show()
        self.components.status_bar.showMessage('Processing translations...')
        translation_count = len(elan_translations)
        completed_count = 0
        for index in range(translation_count):
            self.components.progress_bar.update_progress(completed_count / translation_count)
            translation = Translation(index=index,
                                      start=int(elan_translations[index][0])/1000,
                                      end=int(elan_translations[index][1])/1000,
                                      translation=elan_translations[index][2])
            self.data.translations.append(translation)
            completed_count += 1
        completed_count = 0
        elan_transcriptions = self.data.eaf_object.get_annotation_data_for_tier(transcription_tier)
        audio_file = self.get_audio_file()
        self.components.status_bar.showMessage('Processing transcriptions...')
        transcription_count = len(elan_transcriptions)
        for index in range(transcription_count):
            self.components.progress_bar.update_progress(completed_count / transcription_count)
            transcription = Transcription(index=index,
                                          transcription=elan_transcriptions[index][2],
                                          start=int(elan_transcriptions[index][0])/1000,
                                          end=int(elan_transcriptions[index][1])/1000,
                                          media=audio_file)
            transcription.translation = self.match_translations(transcription, self.data.translations)
            self.data.transcriptions.append(transcription)
            completed_count += 1
        self.components.progress_bar.hide()

    @staticmethod
    def match_translations(transcription: Transcription, translations: List[Translation]) -> Union[None, str]:
        for translation in translations:
            if transcription.time_matches_translation(translation):
                return translation.translation
        return None

    def populate_table_row(self, row: int, table: TranslationTableWidget) -> None:
        table.setItem(row, TABLE_COLUMNS['Index'], TableIndexCell(row))
        table.setItem(row, TABLE_COLUMNS['Transcription'],
                      QTableWidgetItem(self.data.transcriptions[row].transcription))
        table.setItem(row, TABLE_COLUMNS['Translation'], QTableWidgetItem(self.data.transcriptions[row].translation))
        PreviewButtonWidget(self, row, table)
        ImageButtonWidget(self, row, table)
        SelectorCellWidget(row, self.components.status_bar, table)

    def populate_table(self, table: TranslationTableWidget) -> None:
        for row in range(len(self.data.transcriptions)):
            self.populate_table_row(row, table)
        table.sort_by_index()
        self.parent.statusBar().showMessage(f'Imported {len(self.data.transcriptions)} transcriptions')

    def on_click_load(self) -> None:
        file_name = open_file_dialogue()
        if file_name:
            self.data.elan_file = file_name
            self.components.elan_file_field.setText(file_name)
            self.load_second_stage_widgets(self.components, self.data)
            self.components.transcription_menu.setEnabled(True)
            self.components.translation_menu.setEnabled(True)

    def on_click_import(self) -> None:
        warning_message = QMessageBox()
        choice = warning_message.question(warning_message, 'Warning',
                                          'Warning: Any unsaved work will be overwritten. Proceed?',
                                          QMessageBox.Yes | QMessageBox.No | QMessageBox.Warning)
        if choice == QMessageBox.Yes:
            self.load_third_stage_widgets(self.components, self.data)

    def on_click_image(self, row: int) -> None:
        image_path = open_image_dialogue()
        if image_path:
            self.data.transcriptions[row].image = image_path
            self.components.table.cellWidget(row, TABLE_COLUMNS['Image']).swap_icon_yes()

    def on_click_choose_export(self) -> None:
        self.data.export_location = open_folder_dialogue()
        self.components.export_location_field.setText(self.data.export_location)
        if self.data.export_location:
            self.load_fourth_stage_widgets()

    def on_click_select_all(self) -> None:
        if self.all_selected():
            for row in range(self.components.table.rowCount()):
                if not self.components.table.isRowHidden(row):
                    self.components.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(False)
        else:
            for row in range(self.components.table.rowCount()):
                if not self.components.table.isRowHidden(row):
                    self.components.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(True)

    def all_selected(self) -> bool:
        for row in range(self.components.table.rowCount()):
            if not self.components.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked() \
                    and not self.components.table.isRowHidden(row):
                return False
        return True

    def get_export_paths(self) -> Box:
        return Box({
            'transcription': make_file_if_not_exists(os.path.join(self.data.export_location, 'words')),
            'translation': make_file_if_not_exists(os.path.join(self.data.export_location, 'translations')),
            'sound': make_file_if_not_exists(os.path.join(self.data.export_location, 'sounds')),
            'image': make_file_if_not_exists(os.path.join(self.data.export_location, 'images')),
        })

    def create_output_files(self, row: int) -> None:
        export_paths = self.get_export_paths()
        sound_file = self.data.transcriptions[row].get_sample_file_object()
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

    def sample_sound(self, row: int) -> None:
        sample_file_path = self.data.transcriptions[row].get_sample_file_path()
        mixer.init()
        sound = mixer.Sound(sample_file_path)
        sound.play()


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

    def __init__(self, parent: ConverterWidget, row: int, table: TranslationTableWidget):
        super().__init__()
        self.parent = parent
        image_icon = QIcon('img/play.png')
        self.setIcon(image_icon)
        self.clicked.connect(partial(self.parent.sample_sound, row))
        self.setToolTip('Left click to hear a preview of the audio for this word')
        table.setCellWidget(row, TABLE_COLUMNS['Preview'], self)


class ImageButtonWidget(QPushButton):
    """
    Custom button for adding and removing images related to particular translations. For inclusion in rows of the
    TranslationTable.
    """
    rightClick = pyqtSignal()

    def __init__(self, parent: ConverterWidget, row: int, table: TranslationTableWidget) -> None:
        super().__init__()
        self.parent = parent
        self.row = row
        self.image_icon_no = QIcon('img/image-no.png')
        self.image_icon_yes = QIcon('img/image-yes.png')
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
        self.addFile('./img/language-48.png', QSize(48, 48))
        self.addFile('./img/language-96.png', QSize(96, 96))
        self.addFile('./img/language-192.png', QSize(192, 192))
        self.addFile('./img/language-256.png', QSize(256, 256))


class LockedLineEdit(QLineEdit):
    """
    Not currently used.
    """

    def __init__(self, string: str) -> None:
        super().__init__(string)
        self.setReadOnly(True)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pass


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
        reset.setShortcut('Ctrl+R')
        file.addAction(reset)

        quit = QAction('Quit', self)
        quit.setShortcut('Ctrl+Q')
        quit.triggered.connect(self.close)
        file.addAction(quit)

        help = self.bar.addMenu('Help')
        about = QAction('About', self)
        about.setShortcut('Ctrl+A')
        help.addAction(about)


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
