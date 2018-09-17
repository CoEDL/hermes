from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QThread, QTimer
from datatypes import create_lmf, Transcription
from utilities.output import create_lmf_files
from utilities.files import open_folder_dialogue
from widgets.converter import ConverterWidget
from windows.manifest import ManifestWindow
from widgets.table import TABLE_COLUMNS
from widgets.warning import WarningMessage

import json
import logging


class SessionManager(object):
    """
    Session Manager handles session operations, providing functionality for Save, Save As, and Open.
    """

    def __init__(self, converter: ConverterWidget):
        self._file_dialog = QFileDialog()
        self.session_log = logging.getLogger("SessionManager")
        self.converter = converter
        self.session_filename = None
        self.autosave = AutosaveThread(self)
        # self.autosave.start()
        self.autosave_timer = QTimer()

    def open_file(self):
        """Open a .hermes json file and parse into table."""
        self.converter.components.status_bar.clearMessage()

        file_name, _ = self._file_dialog.getOpenFileName(self._file_dialog,
                                                         "Open Hermes Session", "", "hermes save (*.hermes)")
        # Ensure there is a file to open!
        if not file_name:
            file_not_found_msg()
            self.session_log.warn("No file selected for open function.")
            return
        self.session_filename = file_name
        self.session_log.info(f"File opened from: {self.session_filename}")
        self.exec_open()

    def exec_open(self):
        """Execs open functionality. Assumes that a file has been successfully found by user."""
        with open(self.session_filename, 'r') as f:
            loaded_data = json.loads(f.read())
            self.session_log.info(f"Data loaded: {loaded_data}")

        # Populate manifest in converter data
        self.populate_initial_lmf_fields(loaded_data)

        # Add transcriptions
        self.converter.data.transcriptions = list()
        self.converter.components.filter_table.clear_table()
        for i, word in enumerate(loaded_data['words']):
            self.converter.data.transcriptions.append(Transcription(index=i,
                                                                    transcription=word['transcription'],
                                                                    translation=word['translation'][0],
                                                                    image=word.get('image')[0] if word.get('image') else '',
                                                                    media=word.get('audio')[0] if word.get('audio') else '')
                                                      )

            if word.get('audio')[0]:
                # An audio file exists, add it.
                self.converter.data.transcriptions[i].set_blank_sample()
                self.converter.data.transcriptions[i].sample.set_sample(word.get('audio')[0])

            self.session_log.info(f"Transcription loaded: {self.converter.data.transcriptions[i]}")

        # Populate table, add an extra blank row for convenience at end.
        for n in range(len(loaded_data['words']) + 1):
            self.converter.components.filter_table.add_blank_row()
        self.converter.components.filter_table.populate_table(self.converter.data.transcriptions)
        self.converter.components.status_bar.showMessage(f"Data opened from: {self.session_filename}", 5000)

    def save_as_file(self):
        """User sets new file name + location with QFileDialog, if set then initialise save process."""
        file_name, _ = self._file_dialog.getSaveFileName(self._file_dialog,
                                                         "Save As", "mysession.hermes", "hermes save (*.hermes)")
        if file_name:
            self.session_filename = file_name
            self.create_session_lmf()
            self.session_log.info(f'New File created with Save As: {self.session_filename}')
            self.save_file()
        else:
            no_save_file_msg()
            self.session_log.warning("No save file was selected, aborting save.")
            return

    def save_file(self):
        # If no file then restart from save as
        if not self.session_filename:
            self.save_as_file()
            return

        # User to set export location if it does not exist, abort if not set.
        if not self.export_location():
            no_export_msg()
            self.session_log.warning("No export location was selected, aborting save.")
            return

        # All conditions met at this point, save is ready.
        self.exec_save()

    def exec_save(self):
        """Executes the save function. Assumes that all conditions are ready.

        All saves require a file name setup or loaded, and an export location set in prior steps.
        """
        # Empty lmf word list first, otherwise it will duplicate entries.
        self.converter.data.lmf['words'] = list()

        # Progress bar
        self.converter.components.status_bar.clearMessage()
        self.converter.components.progress_bar.show()
        complete_count = 0
        to_save_count = self.converter.components.table.rowCount()

        # Transfer data to lmf file.
        for row in range(self.converter.components.table.rowCount()):
            if self.converter.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"]):
                create_lmf_files(row, self.converter.data)
            complete_count += 1
            self.converter.components.progress_bar.update_progress(complete_count / to_save_count)

        # Save to json format
        if self.session_filename:
            with open(self.session_filename, 'w+') as f:
                json.dump(self.converter.data.lmf, f, indent=4)
        else:
            self.session_log.error("File not found on exec_save().")
            file_not_found_msg()

        self.converter.components.progress_bar.hide()
        self.converter.components.status_bar.showMessage(f"Data saved at: {self.session_filename}", 5000)
        self.session_log.info(f"File saved at {self.session_filename}")

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

        Args:
            source: ManifestWindow for input, or loaded .hermes (json) file with information to be extracted.
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

    def export_location(self) -> str:
        """User sets an export location if one is not already set.

        Returns:
            Path to export location, else None.
        """
        if not self.converter.data.export_location:
            export_init_msg()
            self.converter.data.export_location = open_folder_dialogue()
        self.session_log.info(f'Export location set: {self.converter.data.export_location}')
        return self.converter.data.export_location

    def autosave_thread_function(self):
        """TODO, this is to test that thread initialised"""
        print("Entered Thread")
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.run_autosave)
        self.autosave_timer.start(1000)
        print(f'Time remaining {self.autosave_timer.remainingTime()}')
        print(f'Time active {self.autosave_timer.isActive()}')

    def run_autosave(self):
        """TODO"""
        print(f'Autosaved!')


class AutosaveThread(QThread):
    """Threaded autosave to avoid interruption."""

    def __init__(self, session: SessionManager):
        QThread.__init__(self)
        self.session = session

    def run(self):
        self.session.autosave_thread_function()
        self.exec_()


def file_not_found_msg():
    file_not_found_warn = WarningMessage()
    file_not_found_warn.warning(file_not_found_warn, 'Warning',
                                f'No file was found.\n',
                                QMessageBox.Ok)


def no_save_file_msg():
    no_save_file_warn = WarningMessage()
    no_save_file_warn.warning(no_save_file_warn, 'Warning',
                              f"No save file was selected. You must specify a file to save to.\n",
                              QMessageBox.Ok)


def no_export_msg():
    no_save_file_warn = WarningMessage()
    no_save_file_warn.warning(no_save_file_warn, 'Warning',
                              f"No export location found. You must specify an export location.\n",
                              QMessageBox.Ok)


def export_init_msg():
    export_msg = WarningMessage()
    export_msg.information(export_msg, 'Export Location Needed',
                           f"Export location not set, a file dialog will now open. Please choose an export location.\n",
                           QMessageBox.Ok)
