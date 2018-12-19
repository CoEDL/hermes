import copy
import json
import os
import shutil
from PyQt5.QtWidgets import QCheckBox, QDialog, QFileDialog, QGridLayout, QLabel, QMainWindow, QMessageBox, QPushButton
from PyQt5.QtCore import QThread, QTimer, QEventLoop
from PyQt5.QtGui import QFont
from box import Box
from datatypes import create_lmf, ConverterData, Transcription
from datetime import datetime
from enum import Enum
from tempfile import mkdtemp
from utilities.files import open_folder_dialogue
from utilities.logger import setup_custom_logger
from utilities.output import create_lmf_files
from widgets.table import TABLE_COLUMNS
from widgets.warning import WarningMessage
from windows.manifest import ManifestWindow


################################################################################
# Save/Load Functionality
################################################################################


LOG_SESSION = setup_custom_logger("Session Manager")
LOG_AUTOSAVE = setup_custom_logger("Autosave Thread")


class SessionManager(object):
    """
    Session Manager handles session operations, providing functionality for Save, Save As, and Open.
    """

    def __init__(self, parent: QMainWindow):
        self._file_dialog = QFileDialog()

        self.parent = parent
        # Converter widget that runs hermes' main operations, set in Primary after initialisation of all elements.
        self.converter = None

        # Project Parameters/Paths
        self.project_name = ""
        self.project_path = ""
        self.assets_audio = ""
        self.assets_images = ""
        self.exports = ""
        self.templates = ""
        self.saves = ""

        # Save file parameters TODO: Create Save Object
        self.save_fp = None
        self.save_data = None
        self.data_author = ""
        self.data_transcription_language = ""
        self.data_translation_language = ""

        # Template parameters
        self.template_name = None
        self.template_type = None
        self.template_options = TemplateDialog(self.parent, self)

        # Autosave parameters
        self.autosave_thread = None
        self.autosave_fp = None
        self.autosave_interval = 120  # Seconds

        # Session Parameters
        self.save_mode = SaveMode.MANUAL

    def setup_project_paths(self):
        """Setup project paths for this session, on new project or on load."""
        self.project_path = os.path.join(self.parent.settings.project_root_dir, self.project_name)
        self.assets_audio = os.path.join(self.project_path, "assets", "audio")
        self.assets_images = os.path.join(self.project_path, "assets", "images")
        self.exports = os.path.join(self.project_path, "export")
        self.templates = os.path.join(self.project_path, "templates")
        self.saves = os.path.join(self.project_path, "saves")
        self.save_fp = os.path.join(self.saves, self.project_name + ".hermes")
        self.autosave_fp = os.path.join(self.saves, "autosave.hermes")
        LOG_SESSION.debug(f"Setup paths: {self.assets_images} {self.assets_audio} {self.exports} {self.templates} {self.saves}")
        LOG_SESSION.debug(f"Save path: {self.save_fp} :: Autosave {self.autosave_fp}")

    def open_project(self) -> bool:
        """Open a project, and setup the paths associated with this project as
        a pre-processing step before data load.

        If project path is not found, will throw a warning and abort process.

        Returns:
            True if a project was successfully opened, else False.
        """
        self.project_path = self._file_dialog.getExistingDirectory(self._file_dialog,
                                                                   "Choose Project to Open",
                                                                   self.parent.settings.project_root_dir,
                                                                   QFileDialog.ShowDirsOnly)
        if self.project_path:
            self.project_name = os.path.basename(self.project_path)
            self.setup_project_paths()
            LOG_SESSION.info(f"Opened project: {self.project_path}")
            return True
        LOG_SESSION.warn(f"Unable to open project, project not selected by user. Process Aborted.")
        folder_not_found_msg()
        return False

    def load_project_save(self):
        """Loads the project save file path into the Session Manager. Project
        save files are autonamed and generated on save.

        Returns:
            True if a save file exists in project, else False.
        """
        if os.path.exists(self.save_fp):
            LOG_SESSION.info(f"Save file found @ {self.save_fp}")
            self.load_project_data()
            return True
        LOG_SESSION.info(f"No save found, no data loaded.")
        return False

    def load_project_data(self):
        """Opens save file for the current project and populates table. This
        functionality only runs on open option if load_project_save() has
        successfully found a save file.
        """
        LOG_SESSION.info(f"Loading Project Data")
        with open(self.save_fp, 'r') as f:
            self.save_data = json.loads(f.read())
            LOG_SESSION.debug(f"Data loaded: {self.save_data}")
        # Populate Language and Author details
        self.data_author = self.save_data['author']
        self.data_transcription_language = self.save_data['transcription-language']
        self.data_translation_language = self.save_data['translation-language']
        self.populate_filter_table()

    def populate_filter_table(self):
        """Populates the table with save files transcriptions."""
        self.converter.data.transcriptions = list()
        self.converter.components.filter_table.clear_table()
        for i, word in enumerate(self.save_data['words']):
            self.converter.data.transcriptions.append(Transcription(index=i,
                                                                    transcription=word['transcription'],
                                                                    translation=word['translation'][0],
                                                                    image=word.get('image')[0] if word.get('image') else '',
                                                                    media=word.get('audio')[0] if word.get('audio') else '')
                                                      )
            if word.get('audio'):
                # An audio file exists, add it.
                self.converter.data.transcriptions[i].set_blank_sample()
                self.converter.data.transcriptions[i].sample.set_sample(word.get('audio')[0])
        # Populate table with data
        for n in range(len(self.save_data['words'])):
            self.converter.components.filter_table.add_blank_row()
        self.converter.components.filter_table.populate_table(self.converter.data.transcriptions)
        # Update user on save success in status bar.
        self.converter.components.status_bar.clearMessage()
        self.converter.components.status_bar.showMessage(f"Data opened from: {self.save_fp}", 5000)
        LOG_SESSION.info(f"Table populated with {len(self.save_data['words'])} transcriptions.")

    def save_project(self):
        """Saves data from table into the project's json based save file.

        Assets associated with word list will be moved to the appropriate asset folders.
        """
        if self.save_mode is SaveMode.AUTOSAVE:
            save = self.autosave_fp
        else:
            save = self.save_fp

        # Progress Bar
        if self.save_mode is not SaveMode.AUTOSAVE:
            self.converter.components.status_bar.clearMessage()
            complete_count = 0
            to_save_count = self.converter.components.table.rowCount()

        self.create_save_data()
        # Transfer data
        for row in range(self.converter.components.table.rowCount()):
            if self.data_exists(row):
                self.prepare_save_data(row)
            if self.save_mode is not SaveMode.AUTOSAVE:
                complete_count += 1
                self.converter.components.progress_bar.update_progress(complete_count / to_save_count)

        # Write Save File
        try:
            with open(save, 'w') as f:
                json.dump(self.save_data, f, indent=4)
                self.converter.components.status_bar.showMessage(f"Data saved at {save}", 5000)
                LOG_SESSION.info(f"File saved at {save}")
        except Exception as e:
            LOG_SESSION.warn(f"Error -  {e}: Unable to save file to {save}")
            save_fail_warn()

    def data_exists(self, row: int):
        return self.converter.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"]) \
               or self.converter.components.table.get_cell_value(row, TABLE_COLUMNS["Translation"])

    def create_save_data(self) -> None:
        """Create save data file and TODO: draw authorship details from table."""
        self.save_data = create_lmf(
            transcription_language=self.data_transcription_language,
            translation_language=self.data_translation_language,
            author=self.data_author
        )

    def prepare_save_data(self, row: int) -> None:
        """Record data for this session into a dictionary for saving to .hermes"""
        transcription = self.converter.data.transcriptions[row]
        word_entry = {
            "id": str(transcription.id),
            "transcription": transcription.transcription,
            "translation": [transcription.translation, ],
        }
        if transcription.sample:
            sound_file = transcription.sample.get_sample_file_object()
            sound_file_path = f'{self.assets_audio}/{transcription.transcription}-{row}.wav'
            sound_file.export(sound_file_path, format='wav')
            word_entry['audio'] = [sound_file_path, ]
        if transcription.image:
            _, image_extension = os.path.splitext(transcription.image)
            image_file_path = os.path.join(self.assets_images,
                                           f'{transcription.transcription}-{row}{image_extension}')
            try:
                shutil.copy(transcription.image, image_file_path)
            except shutil.SameFileError:
                pass
            word_entry['image'] = [image_file_path, ]
        self.save_data['words'].append(word_entry)

    # TODO: Re-implement templates based on new project logic.
    @DeprecationWarning
    def prepare_template_file(self) -> ConverterData:
        """Prepares template files based on user selection.

        Template files can have the following fields prepared:
        - Transcription
        - Translation
        - Both

        Resources such as audio and images are best added in a resource creation
        session as opposed to fixed with template to allow for transferal of
        templates to other users and/or computers.

        Returns:
            ConverterData with only relevant information as requested by user.
        """
        if not self.template_type:
            no_template_msg()

        # Prepare custom converter data to save
        data = ConverterData()
        data.transcriptions = copy.deepcopy(self.converter.data.transcriptions)

        for i in range(len(data.transcriptions)):
            # Clear transcription or translation if only one type wanted.
            if self.template_type is TemplateType.TRANSCRIPTION:
                data.transcriptions[i].translation = ""
            elif self.template_type is TemplateType.TRANSLATION:
                data.transcriptions[i].transcription = ""

            # Clear images and sounds
            data.transcriptions[i].image = None
            data.transcriptions[i].sample = None

            LOG_SESSION.info(f"Template prepared data {data.transcriptions[i]}")

        return data

    @DeprecationWarning
    def save_template(self):
        """Asks user to save a template file, user will need to name the template
        file, and then select fields they wish to use for this template.
        """
        self.template_options.exec()

        # Get template options
        self.template_type = self.get_template_option(self.template_options)
        self.template_options.close()

        # widgets.transcription_language_field.text()
        if self.template_type:
            self.save_as_file()

        # Go back to normal saving mode.
        self.template_type = None

    @DeprecationWarning
    def get_template_option(self, template_dialog):
        """Retrieve template option"""
        template_choice = None
        translation_check = template_dialog.widgets.template_translation_check.isChecked()
        transcription_check = template_dialog.widgets.template_transcription_check.isChecked()

        if translation_check and transcription_check:
            template_choice = TemplateType.TRANSCRIPT_TRANSLATE
        elif transcription_check:
            template_choice = TemplateType.TRANSCRIPTION
        elif translation_check:
            template_choice = TemplateType.TRANSLATION

        return template_choice

    @DeprecationWarning
    def open_template(self):
        """Asks user to open a template file, user will need to name the template
        file, and then select fields they wish to use for this template.
        """
        self.template_type = TemplateType.OPEN_TEMPLATE
        self.open_file()
        # Go back to normal saving mode.
        self.template_type = None

    def start_autosave(self):
        self.autosave_thread = AutosaveThread(self)
        self.autosave_thread.start()

    def end_autosave(self):
        if self.autosave_thread:
            self.autosave_thread.quit()
            self.autosave_thread.wait()
            self.autosave_thread = None


################################################################################
# Autosave Functionality
################################################################################


class AutosaveThread(QThread):
    """Threaded autosave to avoid interruption."""

    def __init__(self, session: SessionManager):
        QThread.__init__(self)
        self.session = session

    def run(self):
        self.autosave_thread_function()
        loop = QEventLoop()
        loop.exec_()

    def autosave_thread_function(self):
        """Thread function, continue until thread is terminated.
        By default, timer is set to every 5 minutes.
        TODO: Implement setting for timer.
        """
        LOG_AUTOSAVE.debug("Autosave thread started")
        self.autosave_timer = QTimer()
        self.autosave_timer.moveToThread(self)
        self.autosave_timer.timeout.connect(self.run_autosave)
        self.autosave_timer.start(1000 * self.session.autosave_interval)

    def run_autosave(self):
        """Run the autosave function in current session upon timer expire."""
        LOG_AUTOSAVE.info(f'Autosaving! {datetime.now().time()}')

        # Do autosave
        self.session.save_mode = SaveMode.AUTOSAVE
        self.session.save_project()
        self.session.save_mode = SaveMode.MANUAL

    def __del__(self):
        self.wait()


################################################################################
# Template Utilities
################################################################################


class TemplateDialog(QDialog):
    """Dialog box for deciding on template type."""

    def __init__(self, parent: QMainWindow, session: SessionManager):
        super().__init__(parent)
        self.session = session
        self.layout = QGridLayout()
        self.widgets = Box()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Template Options')
        self.setMinimumWidth(300)

        header_font = QFont()
        header_font.setFamily('SansSerif')
        header_font.setPointSize(12)
        header_font.setBold(True)

        template_type_label = QLabel('Choose Template Field(s):')
        template_type_label.setFont(header_font)
        self.layout.addWidget(template_type_label, 0, 0, 1, 4)

        template_translation_label = QLabel('Translation')
        self.layout.addWidget(template_translation_label, 1, 0, 1, 1)
        self.widgets.template_translation_check = QCheckBox()
        self.layout.addWidget(self.widgets.template_translation_check, 1, 1, 1, 1)

        template_transcription_label = QLabel('Transcription')
        self.layout.addWidget(template_transcription_label, 2, 0, 1, 1)
        self.widgets.template_transcription_check = QCheckBox()
        self.layout.addWidget(self.widgets.template_transcription_check, 2, 1, 1, 1)

        ok_button = QPushButton('Ok')
        ok_button.clicked.connect(self.on_click_ok)
        ok_button.setDefault(True)
        self.layout.addWidget(ok_button, 4, 3, 1, 1)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.on_click_cancel)
        self.layout.addWidget(cancel_button, 4, 4, 1, 1)

        self.setLayout(self.layout)

    def on_click_ok(self):
        self.close()

    def on_click_cancel(self):
        self.widgets.template_translation_check.setChecked(False)
        self.widgets.template_transcription_check.setChecked(False)
        self.close()


class TemplateType(Enum):
    """Template types that a user can save."""
    TRANSCRIPTION = 0
    TRANSLATION = 1
    # Represents a template of both transcription and translation types.
    TRANSCRIPT_TRANSLATE = 2
    # Tag to indicate template is to be opened
    OPEN_TEMPLATE = 3


class SaveMode(Enum):
    MANUAL = 0
    AUTOSAVE = 1


################################################################################
# Popup Messages
################################################################################


def folder_not_found_msg():
    folder_not_loaded = WarningMessage()
    folder_not_loaded.warning(folder_not_loaded, 'Warning',
                                f'No folder selected, load aborted.\n',
                                QMessageBox.Ok)


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
                              f"No export location found. You must specify an export location to save assets.\n",
                              QMessageBox.Ok)


def export_init_msg():
    export_msg = WarningMessage()
    export_msg.information(export_msg, 'Export Location Needed',
                           f"Export location not set, a file dialog will now open. Please choose a location to save assets.\n",
                           QMessageBox.Ok)


def no_template_msg():
    export_msg = WarningMessage()
    export_msg.information(export_msg, 'Warning',
                           f"No Template Type selected, template creation aborted.\n",
                           QMessageBox.Ok)


def save_fail_warn():
    export_msg = WarningMessage()
    export_msg.information(export_msg, 'Warning',
                           f"Save failed, please contact team for support\n",
                           QMessageBox.Ok)
