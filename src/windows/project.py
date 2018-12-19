from box import Box
from PyQt5.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QMainWindow, QDialog
from utilities.logger import setup_custom_logger
from widgets.session import SessionManager


LOG_PROJECT_WINDOW = setup_custom_logger("Project Details Window")


class ProjectDetailsWindow(QDialog):
    def __init__(self,
                 parent: QMainWindow,
                 session: SessionManager):
        super().__init__(parent)
        self.session = session
        self.layout = QGridLayout()
        self.widgets = Box()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Project Details')
        self.setMinimumWidth(300)
        instruction_label = QLabel('Hit save to record any changes to project details.')
        self.layout.addWidget(instruction_label, 0, 0, 1, 7)

        transcription_language_label = QLabel('Transcription Language:')
        self.layout.addWidget(transcription_language_label, 1, 0, 1, 1)
        self.widgets.transcription_language_field = QLineEdit()
        self.widgets.transcription_language_field.setText(self.session.data_transcription_language)
        self.layout.addWidget(self.widgets.transcription_language_field, 1, 1, 1, 7)

        translation_language_label = QLabel('Translation Language:')
        self.layout.addWidget(translation_language_label, 2, 0, 1, 1)
        self.widgets.translation_language_field = QLineEdit()
        self.widgets.translation_language_field.setText(self.session.data_translation_language)
        self.layout.addWidget(self.widgets.translation_language_field, 2, 1, 1, 7)

        author_name_label = QLabel('Author Name:')
        self.layout.addWidget(author_name_label, 3, 0, 1, 1)
        self.widgets.author_name_field = QLineEdit()
        self.widgets.author_name_field.setText(self.session.data_author)
        self.layout.addWidget(self.widgets.author_name_field, 3, 1, 1, 7)

        save_button = QPushButton('Save')
        save_button.clicked.connect(self.on_click_save)
        self.layout.addWidget(save_button, 4, 7, 1, 1)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.on_click_close)
        self.layout.addWidget(close_button, 4, 6, 1, 1)

        self.setLayout(self.layout)

    def on_click_save(self):
        self.session.data_transcription_language = self.widgets.transcription_language_field.text()
        self.session.data_translation_language = self.widgets.translation_language_field.text()
        self.session.data_author = self.widgets.author_name_field.text()
        LOG_PROJECT_WINDOW.info(f"Project Details set: \
                                {self.session.data_transcription_language}, \
                                {self.session.data_translation_language}, \
                                {self.session.data_author}")
        self.close()

    def on_click_close(self):
        self.close()
