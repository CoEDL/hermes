from box import Box
from PyQt5.QtWidgets import QMessageBox, QGridLayout, QLabel, QLineEdit, QPushButton, QMainWindow, QWidget, QDialog
from datatypes import ConverterData, create_lmf


class ManifestWindow(QDialog):
    def __init__(self,
                 parent: QMainWindow,
                 data: ConverterData):
        super().__init__(parent)
        self.data = data
        self.layout = QGridLayout()
        self.widgets = Box()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Enter Manifest Details')
        self.setMinimumWidth(300)
        transcription_language_label = QLabel('Transcription Language:')
        self.layout.addWidget(transcription_language_label, 0, 0, 1, 1)
        self.widgets.transcription_language_field = QLineEdit()
        self.layout.addWidget(self.widgets.transcription_language_field, 0, 1, 1, 7)

        translation_language_label = QLabel('Translation Language:')
        self.layout.addWidget(translation_language_label, 1, 0, 1, 1)
        self.widgets.translation_language_field = QLineEdit()
        self.widgets.translation_language_field
        self.layout.addWidget(self.widgets.translation_language_field, 1, 1, 1, 7)

        author_name_label = QLabel('Author Name:')
        self.layout.addWidget(author_name_label, 2, 0, 1, 1)
        self.widgets.author_name_field = QLineEdit()
        self.layout.addWidget(self.widgets.author_name_field, 2, 1, 1, 7)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 3, 7, 1, 1)

        self.setLayout(self.layout)

    def on_click_save(self):
        self.data.lmf = create_lmf(
            transcription_language=self.widgets.transcription_language_field.text(),
            translation_language=self.widgets.translation_language_field.text(),
            author=self.widgets.author_name_field.text()
        )
        self.close()

