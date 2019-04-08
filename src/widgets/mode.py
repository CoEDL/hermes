from box import Box
from PyQt5.QtWidgets import QPushButton, QWidget, QGridLayout, QLabel, QLineEdit
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt
from datatypes import OperationMode
from utilities import resource_path
from typing import Callable, NewType
from widgets.formatting import HorizontalLineWidget


ConverterWidget = NewType('ConverterWidget', QWidget)


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
        self.fields = Box()
        self.init_ui()

    def init_ui(self) -> None:
        project_name_label = QLabel('Project Name:')
        self.layout.addWidget(project_name_label, 0, 0, 1, 1)
        project_name_field = QLineEdit()
        project_name_field.setText('Enter a Unique Project Name.')
        self.fields.project_name = project_name_field
        self.layout.addWidget(project_name_field, 0, 1, 1, 1)

        project_transcription_label = QLabel('Transcription Language:')
        self.layout.addWidget(project_transcription_label, 1, 0, 1, 1)
        project_transcription_field = QLineEdit()
        project_transcription_field.setText('Enter Transcription Language.')
        self.fields.transcription_language = project_transcription_field
        self.layout.addWidget(project_transcription_field, 1, 1, 1, 1)

        project_translation_label = QLabel('Translation Language: ')
        self.layout.addWidget(project_translation_label, 2, 0, 1, 1)
        project_translation_field = QLineEdit()
        project_translation_field.setText('Enter Translation Language.')
        self.fields.translation_language = project_translation_field
        self.layout.addWidget(project_translation_field, 2, 1, 1, 1)

        project_author_label = QLabel('Author: ')
        self.layout.addWidget(project_author_label, 3, 0, 1, 1)
        project_author_field = QLineEdit()
        project_author_field.setText('Enter Author Name.')
        self.fields.author = project_author_field
        self.layout.addWidget(project_author_field, 3, 1, 1, 1)

        self.layout.addWidget(HorizontalLineWidget(), 4, 0, 1, 2)

        elan_button = ModeButton('./img/elan.png',
                                 'Import ELAN File',
                                 on_click=self.on_click_elan)
        self.layout.addWidget(elan_button, 5, 0, 1, 2)
        scratch_button = ModeButton('./img/scratch.png',
                                    'Start From Scratch',
                                    on_click=self.on_click_scratch)
        self.layout.addWidget(scratch_button, 6, 0, 1, 2)

        self.setLayout(self.layout)

    def on_click_elan(self) -> None:
        self.parent.data.mode = OperationMode.ELAN
        self.__set_project_information()
        self.parent.session.setup_project_paths()
        self.parent.setup_project()
        self.parent.load_elan_loader()

    def on_click_scratch(self) -> None:
        self.parent.data.mode = OperationMode.SCRATCH
        self.__set_project_information()
        self.parent.session.setup_project_paths()
        self.parent.setup_project()
        self.parent.load_main_hermes_app(self.parent.components, self.parent.data)

    def __set_project_information(self) -> None:
        self.parent.session.project_name = self.fields.project_name.text()
        self.parent.session.data_author = self.fields.author.text()
        self.parent.session.data_transcription_language = self.fields.transcription_language.text()
        self.parent.session.data_translation_language = self.fields.translation_language.text()


class MainProjectSelection(QWidget):
    """This is the main menu of Hermes that greets the user on app start.

    The user, from here, will select either a New Project or continue with
    an existing project.
    """
    def __init__(self, parent: ConverterWidget) -> None:
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        new_project_btn = ModeButton(resource_path("./img/icon_new_project.png"),
                                     "Start New Project",
                                     on_click = self.on_click_new_project)
        self.layout.addWidget(new_project_btn, 0, 0, 1, 1)
        open_project_btn = ModeButton(resource_path("./img/icon_open_project.png"),
                                      "Open Project",
                                      on_click = self.on_click_open_project)
        self.layout.addWidget(open_project_btn, 0, 1, 1, 1)
        self.setLayout(self.layout)

    def on_click_new_project(self) -> None:
        self.parent.load_new_project_mode()

    def on_click_open_project(self) -> None:
        self.parent.parent.on_click_open()
