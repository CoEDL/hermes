from PyQt5.QtWidgets import QFileDialog, QErrorMessage
from utilities.output import create_lmf_files
from utilities.files import open_folder_dialogue
from windows.manifest import ManifestWindow
from widgets.converter import ConverterWidget
from datatypes import create_lmf, Transcription
import json
import logging
import os


LOG = logging.getLogger("SessionManager")


class SessionManager(object):
    """
    Session Manager handles session operations, providing functionality for Save, Save As, and Open.
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
        with open(file_name, 'r') as f:
            loaded_data = json.loads(f.read())
            LOG.info("Data loaded: {}".format(loaded_data))

        # Populate manifest in converter data
        self.populate_initial_lmf_fields(loaded_data)
        LOG.info("Manifest: {}".format(self.converter.data.lmf))

        # Add transcriptions
        self.converter.data.transcriptions = list()
        for i, word in enumerate(loaded_data['words']):
            self.converter.data.transcriptions.append(Transcription(index=i-1,
                                                                    transcription=word['transcription'],
                                                                    translation=word['translation'][0],
                                                                    image=word.get('image')[0] if word.get('image') else '')
                                                      )
            LOG.info("Transcriptions loaded: {}".format(self.converter.data.transcriptions[i]))

        for n in range(len(self.converter.data.transcriptions)):
            self.converter.components.filter_table.add_blank_row()

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

        if not self.converter.data.export_location:
            self.converter.data.export_location = open_folder_dialogue()

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
        self.populate_initial_lmf_fields(lmf_manifest_window)
        lmf_manifest_window.close()

    def populate_initial_lmf_fields(self, source) -> None:
        """
        Populates a language manifest file's descriptive data.

        If source is a new ManifestWindow, then user will enter information for languages, and authorship.

        Otherwise, source is a loaded file.

        Keyword arguments:
            source -- ManifestWindow for input, or loaded .hermes (json) file with information to be extracted.
        """
        if isinstance(source, ManifestWindow):
            self.converter.data.lmf = create_lmf(
                transcription_language=source.widgets.transcription_language_field.text(),
                translation_language=source.widgets.translation_language_field.text(),
                author=source.widgets.author_name_field.text()
            )
        else:
            self.converter.data.lmf = create_lmf(
                transcription_language=source['transcription-language'],
                translation_language=source['translation-language'],
                author=source['author']
            )

    def update_session(self, file_name: str) -> None:
        self.session_data = SessionFile(file_name)
        self.parse(self.session_data.file_name)


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
