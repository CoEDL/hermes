from PyQt5.QtWidgets import QFileDialog, QMessageBox, QErrorMessage
from utilities.output import create_lmf_files
from windows.manifest import ManifestWindow
from widgets.converter import ConverterWidget
from datatypes import create_lmf
import json
import logging


LOG = logging.getLogger("SessionManager")


class SessionManager(object):
    """
    Session Manager handles session operations.
    """

    def __init__(self, converter: ConverterWidget):
        self.session_data = None
        self._file_dialog = QFileDialog()
        self.converter = converter

    def open_file(self):
        file_name, _ = self._file_dialog.getOpenFileName(self._file_dialog,
                                                         "Open Hermes Session", "", "hermes (*.hermes)")
        self.session_data = SessionFile(file_name)

        # TODO: Parse Opened File

        LOG.info("File opened from: {}".format(self.session_data.file_name))

    def save_as_file(self):
        file_name, _ = self._file_dialog.getSaveFileName(self._file_dialog,
                                                         "Save As", "mysession.hermes", "hermes (*.hermes)")
        if self.session_data is None:
            self.session_data = SessionFile(file_name)
        else:
            self.session_data.file_name = file_name
        self.create_session_lmf()
        LOG.info("New file created with Save AS: {}".format(self.session_data.file_name))
        self.save_file()

    def save_file(self):
        # If no file then save as
        if not self.session_data:
            self.save_as_file()
        else:
            file_name = self.session_data.file_name

        # Empty lmf word list first, otherwise it will duplicate entries.
        self.converter.data.lmf['words'] = list()
        for row in range(self.converter.components.table.rowCount()):
            create_lmf_files(row, self.converter.data)

        # Save to json format
        if file_name:
            with open(file_name, 'w+') as f:
                json.dump(self.converter.data.lmf, f, indent=4)
        else:
            file_not_found_msg()

        LOG.info("File saved at {}".format(self.session_data.file_name))

    def create_session_lmf(self):
        """Creates a new language manifest file prior to new save file."""
        lmf_manifest_window = ManifestWindow(self.converter.data)
        _ = lmf_manifest_window.exec()
        self.converter.data.lmf = create_lmf(
            transcription_language=lmf_manifest_window.widgets.transcription_language_field.text(),
            translation_language=lmf_manifest_window.widgets.translation_language_field.text(),
            author=lmf_manifest_window.widgets.author_name_field.text()
        )
        lmf_manifest_window.close()

    def update_session(self, file_name: str):
        self.session_data = SessionFile(file_name)
        self.parse(self.session_data.file_name)

    def parse(self, file_name: str):
        try:
            with open(file_name, 'r') as file:
                self.session_data.parse_data(file.readlines())
        except (OSError, IOError) as e:
            print("No file to open: {}".format(e))


class SessionFile(object):
    """Data structure holding stored data from a session."""

    def __init__(self, file_name: str):
        self._file_name = file_name
        self._data = None

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, name: str):
        self._file_name = name

    def parse_data(self, data):
        # TODO: Actual data structure and parse.
        self._data = data


def file_not_found_msg():
    warn = QErrorMessage()
    warn.showMessage("File not found, please enter or select a valid file.")
    warn.show()
