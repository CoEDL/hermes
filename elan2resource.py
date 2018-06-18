from PyQt5.QtWidgets import QApplication, QFileDialog, QWidget, QLabel, QPushButton, \
     QGridLayout, QLineEdit, QComboBox, QTableWidget
from PyQt5.QtGui import QIcon, QStandardItemModel
import sys
import pympi


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Language Resource Creator'
        self.layout = QGridLayout()
        self.elan_file = ''
        self.elan_file_field = None
        self.transcription_menu = None
        self.translation_menu = None
        self.eaf_object = None
        self.trans_table = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('edit-language.png'))
        self.setMinimumWidth(600)
        self.load_inital_widgets()
        self.setLayout(self.layout)
        self.show()

    def load_inital_widgets(self):
        self.elan_file_field = QLineEdit('Load an ELAN (*.eaf) file.')
        self.elan_file_field.setReadOnly(True)
        self.layout.addWidget(self.elan_file_field, 0, 0, 1, 7)
        load_button = QPushButton('Load')
        load_button.clicked.connect(self.on_click_load)
        self.layout.addWidget(load_button, 0, 7)

    def load_second_stage_widgets(self):
        self.eaf_object = pympi.Elan.Eaf(self.elan_file)
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
        import_button = QPushButton('Import')
        import_button.clicked.connect(self.on_click_import)
        self.layout.addWidget(import_button, 3, 0, 1, 8)

    def load_third_stage_widgets(self):
        transcription_tier = self.transcription_menu.currentText()
        translation_tier = self.translation_menu.currentText()
        self.transcription_menu.setDisabled(True)
        self.translation_menu.setDisabled(True)
        self.trans_table = QTableWidget(2, 5)
        self.trans_table.setHorizontalHeaderLabels(['Transcription', 'Translation', 'Preview', 'Image', 'Include'])
        self.layout.addWidget(self.trans_table, 4, 0, 5, 8)


    def on_click_load(self):
        file_name = self.open_file_dialogue()
        if file_name:
            self.elan_file = file_name
            self.elan_file_field.setText(file_name)
            self.load_second_stage_widgets()

    def on_click_import(self):
        self.load_third_stage_widgets()

    def open_file_dialogue(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                   "ELAN Files (*.eaf)", options=options)
        return file_name


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())
