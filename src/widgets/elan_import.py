from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel, \
    QComboBox, QMessageBox
from typing import NewType, List
from utilities import open_file_dialogue
from .formatting import HorizontalLineWidget
from .warning import WarningMessage


ConverterWidget = NewType('ConverterWidget', QWidget)


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


