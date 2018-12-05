from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QMessageBox, QLineEdit
from typing import NewType
from os import listdir
from utilities import open_folder_dialogue
from widgets.warning import WarningMessage


ConverterWidget = NewType('ConverterWidget', QWidget)


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
            self.set_export_field_text(self.data.export_location)
            self.parent.enable_export_button()

    def set_export_field_text(self, path: str) -> None:
        self.export_location_field.setText(path)


class ExportButton(QWidget):
    def __init__(self,
                 parent: ConverterWidget) -> None:
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        export_button = QPushButton('Start Export')
        export_button.clicked.connect(self.on_click_export)
        self.layout.addWidget(export_button, 0, 0, 1, 8)
        self.setLayout(self.layout)

    def on_click_export(self) -> None:
        if self.parent.components.table.get_selected_count() == 0:
            warning_message = WarningMessage()
            warning_message.warning(warning_message, 'Warning',
                                    f'You have not selected any items to export.\n'
                                    f'Please select at least one item to continue.',
                                    QMessageBox.Yes)
        else:
            if not self.export_directory_empty():
                warning_message = WarningMessage()
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
        if listdir(self.parent.data.export_location):
            return False
        return True
