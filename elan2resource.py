import os
import sys
import pympi
import tempfile
import shutil
from pygame import mixer
from functools import partial
from PyQt5.QtWidgets import QApplication, QFileDialog, QWidget, QLabel, QPushButton, \
    QGridLayout, QHBoxLayout, QLineEdit, QComboBox, QTableWidget, QHeaderView, \
    QTableWidgetItem, QCheckBox, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QSize, QUrl, pyqtSignal
from moviepy.editor import AudioFileClip
from os.path import expanduser

TABLE_COLUMNS = {
    'Index': 0,
    'Transcription': 1,
    'Translation': 2,
    'Preview': 3,
    'Image': 4,
    'Include': 5,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Language Resource Creator'
        self.converter = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.converter = Converter(parent=self)
        self.setCentralWidget(self.converter)
        self.statusBar().showMessage('Ready!')


class Converter(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.elan_file = None
        self.elan_file_field = None
        self.export_location_field = None
        self.export_location = None
        self.transcription_menu = None
        self.translation_menu = None
        self.transcription_data = None
        self.translation_data = None
        self.filter_field = None
        self.image_data = None
        self.eaf_object = None
        self.trans_table = None
        self.init_ui()

    def init_ui(self):
        self.setMinimumWidth(600)
        self.load_inital_widgets()
        self.setLayout(self.layout)
        self.show()

    def load_inital_widgets(self):
        # First Row (ELAN File Field)
        self.elan_file_field = QLineEdit('Load an ELAN (*.eaf) file.')
        self.elan_file_field.setReadOnly(True)
        self.layout.addWidget(self.elan_file_field, 0, 0, 1, 7)
        load_button = QPushButton('Load')
        load_button.clicked.connect(self.on_click_load)
        self.layout.addWidget(load_button, 0, 7)

    def load_second_stage_widgets(self):
        self.eaf_object = pympi.Elan.Eaf(self.elan_file)
        # Second Row (Tier Selection)
        transcription_label = QLabel('Transcription Tier:')
        self.layout.addWidget(transcription_label, 2, 0, 1, 2)
        self.transcription_menu = QComboBox()
        self.transcription_menu.addItems(self.eaf_object.get_tier_names())
        self.layout.addWidget(self.transcription_menu, 2, 2, 1, 2)
        translation_label = QLabel('Translation Tier:')
        self.layout.addWidget(translation_label, 2, 4, 1, 2)
        self.translation_menu = QComboBox()
        self.translation_menu.addItems(self.eaf_object.get_tier_names())
        self.layout.addWidget(self.translation_menu, 2, 6, 1, 2)
        # Third Row (Import Button)
        import_button = QPushButton('Import')
        import_button.clicked.connect(self.on_click_import)
        self.layout.addWidget(import_button, 3, 0, 1, 8)

    def load_third_stage_widgets(self):
        transcription_tier = self.transcription_menu.currentText()
        translation_tier = self.translation_menu.currentText()
        self.transcription_menu.setDisabled(True)
        self.translation_menu.setDisabled(True)
        # Fifth Row (Filter & Selector)
        filter_label = QLabel('Filter Results:')
        self.layout.addWidget(filter_label, 4, 0, 1, 1)
        self.filter_field = QLineEdit('')
        self.layout.addWidget(self.filter_field, 4, 1, 1, 2)
        filter_clear_button = QPushButton('Clear')
        self.layout.addWidget(filter_clear_button, 4, 3, 1, 1)
        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(self.on_click_select_all)
        self.layout.addWidget(select_all_button, 4, 7, 1, 1)
        # Sixth Row (Table)
        self.trans_table = TranslationTable(len(self.eaf_object.get_annotation_data_for_tier(transcription_tier)))
        self.populate_table(transcription_tier, translation_tier)
        self.layout.addWidget(self.trans_table, 5, 0, 1, 8)
        # Seventh Row (Export Location)
        self.export_location_field = QLineEdit('Choose an export location')
        self.export_location_field.setReadOnly(True)
        self.layout.addWidget(self.export_location_field, 6, 0, 1, 7)
        choose_export_button = QPushButton('Choose')
        choose_export_button.clicked.connect(self.on_click_choose_export)
        self.layout.addWidget(choose_export_button, 6, 7, 1, 1)

    def load_fourth_stage_widgets(self):
        # Eighth Row (Export Button)
        export_button = QPushButton('Export')
        export_button.clicked.connect(self.export_resources)
        self.layout.addWidget(export_button, 7, 0, 1, 8)

    def populate_table(self, transcription_tier, translation_tier):
        self.transcription_data = self.eaf_object.get_annotation_data_for_tier(transcription_tier)
        self.translation_data = self.eaf_object.get_annotation_data_for_tier(translation_tier)
        self.image_data = [None for _ in self.translation_data]
        for row in range(len(self.transcription_data)):
            self.trans_table.setItem(row, TABLE_COLUMNS['Index'], TableIndex(row))
            self.trans_table.setItem(row, TABLE_COLUMNS['Transcription'],
                                     QTableWidgetItem(self.transcription_data[row][2]))
            self.trans_table.setItem(row, TABLE_COLUMNS['Translation'], QTableWidgetItem(self.translation_data[row][2]))
            # Add Preview Button
            preview_button = PreviewButton(self, row)
            self.trans_table.setCellWidget(row, TABLE_COLUMNS['Preview'], preview_button)
            # Add Image Button
            image_button = ImageButton(self, row)
            self.trans_table.setCellWidget(row, TABLE_COLUMNS['Image'], image_button)
            # Add Inclusion Selector
            include_widget = SelectorWidget()
            self.trans_table.setCellWidget(row, TABLE_COLUMNS['Include'], include_widget)

    def on_click_load(self):
        file_name = self.open_file_dialogue()
        if file_name:
            self.elan_file = file_name
            self.elan_file_field.setText(file_name)
            self.load_second_stage_widgets()
            self.transcription_menu.setEnabled(True)
            self.translation_menu.setEnabled(True)

    def on_click_import(self):
        if not self.image_data:
            self.load_third_stage_widgets()
        else:
            warning_message = QMessageBox()
            choice = warning_message.question(warning_message, 'Warning',
                                              'Warning: Any unsaved work will be overwritten. Proceed?',
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Warning)
            if choice == QMessageBox.Yes:
                self.load_third_stage_widgets()

    def on_click_image(self, row):
        image_path = self.open_image_dialogue()
        if image_path:
            self.image_data[row] = image_path
            self.trans_table.cellWidget(row, TABLE_COLUMNS['Image']).swap_icon_yes()

    def on_click_choose_export(self):
        self.export_location = self.open_folder_dialogue()
        self.export_location_field.setText(self.export_location)
        if self.export_location:
            self.load_fourth_stage_widgets()

    def on_click_select_all(self):
        if self.all_selected():
            for row in range(self.trans_table.rowCount()):
                self.trans_table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(False)
        else:
            for row in range(self.trans_table.rowCount()):
                self.trans_table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(True)

    def all_selected(self):
        for row in range(self.trans_table.rowCount()):
            if not self.trans_table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked():
                return False
        return True

    @staticmethod
    def open_folder_dialogue():
        file_dialogue = QFileDialog()
        file_dialogue.setOption(QFileDialog.ShowDirsOnly, True)
        file_name = file_dialogue.getExistingDirectory(file_dialogue,
                                                       'Choose an export folder',
                                                       expanduser('~'),
                                                       QFileDialog.ShowDirsOnly)
        return file_name

    @staticmethod
    def open_file_dialogue():
        file_dialogue = QFileDialog()
        options = QFileDialog.Options()
        file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                     'QFileDialog.getOpenFileName()',
                                                     '',
                                                     'ELAN Files (*.eaf)',
                                                     options=options)
        return file_name

    @staticmethod
    def open_image_dialogue():
        file_dialogue = QFileDialog()
        options = QFileDialog.Options()
        file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                     'QFileDialog.getOpenFileName()',
                                                     '',
                                                     'Image Files (*.png *.jpg)',
                                                     options=options)
        return file_name

    def export_resources(self):
        self.parent.statusBar().showMessage('Exporting')
        transcription_path = make_file_if_not_exists(os.path.join(self.export_location, 'words'))
        translation_path = make_file_if_not_exists(os.path.join(self.export_location, 'translations'))
        sound_file_path = make_file_if_not_exists(os.path.join(self.export_location, 'sounds'))
        image_file_path = make_file_if_not_exists(os.path.join(self.export_location, 'images'))
        audio_file = self.get_audio_file()
        for row in range(self.trans_table.rowCount()):
            if self.trans_table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked():
                sound_file = audio_file.subclip(t_start=self.transcription_data[row][0] / 1000,
                                                t_end=self.transcription_data[row][1] / 1000)
                sound_file.write_audiofile(f'{sound_file_path}/word{str(row)}.wav')
                image_path = self.image_data[row]
                if image_path:
                    image_name, image_extension = os.path.splitext(image_path)
                    shutil.copy(self.image_data[row], f'{image_file_path}/word{row}.{image_extension}')
                with open(f'{transcription_path}/word{row}.txt', 'w') as file:
                    file.write(f'{self.transcription_data[row]}')
                with open(f'{translation_path}/word{row}.txt', 'w') as file:
                    file.write(f'{self.translation_data[row]}')
        export_url = QUrl.fromLocalFile(self.export_location)
        QDesktopServices().openUrl(export_url)

    def get_audio_file(self):
        linked_files = self.eaf_object.get_linked_files()
        relative_file_path = '/'.join(self.elan_file.split('/')[:-1])
        media_file = os.path.join(relative_file_path, linked_files[0]['RELATIVE_MEDIA_URL'][2:])
        audio_data = AudioFileClip(media_file)
        return audio_data

    def sample_sound(self, row):
        audio_file = self.get_audio_file()
        sound_file = audio_file.subclip(t_start=self.transcription_data[row][0] / 1000,
                                        t_end=self.transcription_data[row][1] / 1000)
        temporary_file = tempfile.mkdtemp()
        sound_file_path = os.path.join(temporary_file, f'{str(row)}.wav')
        sound_file.write_audiofile(sound_file_path)
        mixer.init()
        sound = mixer.Sound(sound_file_path)
        sound.play()


class TranslationTable(QTableWidget):
    def __init__(self, num_rows):
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

    def sort_by_index(self):
        self.setSortingEnabled(True)
        self.sortByColumn(TABLE_COLUMNS['Index'], Qt.AscendingOrder)


class SelectorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.selector = QCheckBox()
        self.layout.addWidget(self.selector)
        self.setLayout(self.layout)


class PreviewButton(QPushButton):
    def __init__(self, parent, row):
        super().__init__()
        self.parent = parent
        self.row = row
        image_icon = QIcon('img/play.png')
        self.setIcon(image_icon)
        self.clicked.connect(partial(self.parent.sample_sound, row))
        self.setToolTip('Left click to hear a preview of the audio for this word')


class ImageButton(QPushButton):
    rightClick = pyqtSignal()

    def __init__(self, parent, row):
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

    def swap_icon_yes(self):
        self.setIcon(self.image_icon_yes)

    def swap_icon_no(self):
        self.setIcon(self.image_icon_no)

    def mousePressEvent(self, event):
        QPushButton.mousePressEvent(self, event)

        if event.button() == Qt.RightButton:
            self.rightClick.emit()

    def remove_image(self):
        self.parent.image_data[self.row] = None
        self.swap_icon_no()


class ApplicationIcon(QIcon):
    def __init__(self):
        super().__init__()
        self.addFile('img/language-48.png', QSize(48, 48))
        self.addFile('img/language-96.png', QSize(96, 96))
        self.addFile('img/language-192.png', QSize(192, 192))
        self.addFile('img/language-256.png', QSize(256, 256))


class LockedLineEdit(QLineEdit):
    def __init__(self, string):
        super().__init__(string)
        self.setReadOnly()

    def mousePressEvent(self, QMouseEvent):
        pass


class TableIndex(QTableWidgetItem):
    def __init__(self, value):
        super().__init__()
        self.setTextAlignment(Qt.AlignCenter)
        self.setData(Qt.EditRole, value + 1)


def make_file_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(ApplicationIcon())
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
