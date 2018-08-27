from PyQt5.QtWidgets import QFileDialog
from utilities.output import create_lmf_files
from windows.manifest import ManifestWindow
from datatypes import create_lmf
import json

class SessionManager(object):
    """
    Session Manager handles session operations.
    """

    def __init__(self, converter):
        self.session_data = None
        self._file_dialog = QFileDialog()
        self.converter = converter

    def open_file(self):
        file_name, _ = self._file_dialog.getOpenFileName(self._file_dialog, "Open Hermes Session", "", "hermes (*.hermes)")
        self.update_session(file_name)

        print(self.session_data.get_file_name())
        print(self.session_data.get_session_data())

    def save_as_file(self):
        file_name, _ = self._file_dialog.getSaveFileName(self._file_dialog, "Save As", "mysession.hermes", "hermes (*.hermes)")
        self.update_session(file_name)
        self.save_file()

    def save_file(self):
        file_name = self.session_data.get_file_name()
        print(file_name)
        if file_name is not None:
            lmf_manifest_window = ManifestWindow(self.converter.data)
            _ = lmf_manifest_window.exec()
            self.converter.data.lmf = create_lmf(
                transcription_language=lmf_manifest_window.widgets.transcription_language_field.text(),
                translation_language=lmf_manifest_window.widgets.translation_language_field.text(),
                author=lmf_manifest_window.widgets.author_name_field.text()
            )
            lmf_manifest_window.close()
            for row in range(self.converter.components.table.rowCount()):
                create_lmf_files(row, self.converter.data)
        with open(file_name, 'w') as f:
            # f.write("{}".format(self.converter.data.lmf))
            json.dump(self.converter.data.lmf, f, indent=4)
        self.update_session(file_name)
        print(self.session_data.get_file_name);

    def update_session(self, file_name: str):
        self.session_data = SessionFile(file_name)
        self.parse(self.session_data.get_file_name())

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

    def set_file_name(self, file_name: str):
        self._file_name = file_name

    def get_file_name(self):
        return self._file_name

    def parse_data(self, data):
        # TODO: Actual data structure and parse.
        self._data = data

    def get_session_data(self):
        return self._data
