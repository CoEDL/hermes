import os
import sys
import pympi
import shutil
import math
from PyQt5.QtWidgets import QApplication, QWidget, \
    QGridLayout, QMainWindow, QMessageBox, QProgressBar, \
    QAction, QLayout
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import QSize, QUrl
from urllib.request import url2pathname
from box import Box
from typing import NewType, Union, List
from pydub import AudioSegment
from datatypes import Transcription, Translation, OperationMode
from utilities import resource_path, open_audio_dialogue, make_file_if_not_extant
from widgets.converter import ConverterComponents, ConverterData
from widgets.mode import ModeSelection
from widgets.elan_import import ELANFileField, TierSelector
from widgets.table import FilterTable, TABLE_COLUMNS
from widgets.about import AboutWindow
from widgets.export import ExportButton, ExportLocationField
from widgets.warning import WarningMessage
from widgets.settings import SettingsWindow


MainWindow = NewType('MainWindow', QMainWindow)
ProgressBarWidget = NewType('ProgressBarWidget', QProgressBar)
ConverterWidget = NewType('ConverterWidget', QWidget)

VERSION = '0.03'
REPO_LINK = 'https://github.com/nicklambourne/elan2resource'


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

        self.table_menu = self.bar.addMenu('Table')
        add_row_menu_item = QAction('Add Row', self)
        add_row_menu_item.setShortcut('Ctrl+N')
        add_row_menu_item.triggered.connect(self.on_click_add_row)
        self.table_menu.addAction(add_row_menu_item)

        help_menu = self.bar.addMenu('Help')
        about_menu_item = QAction('About', self)
        about_menu_item.setShortcut('Ctrl+H')
        about_menu_item.triggered.connect(self.on_click_about)
        help_menu.addAction(about_menu_item)

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


if __name__ == '__main__':
    App = QApplication(sys.argv)
    App.setWindowIcon(ApplicationIcon())
    Main = MainWindow(App)
    Main.show()
    sys.exit(App.exec_())
