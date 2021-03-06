import os
import csv
import pympi
import json
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QFrame, QLineEdit
from PyQt5.QtGui import QDesktopServices, QFont
from PyQt5.QtCore import QUrl
from datatypes import OperationMode, Transcription, ConverterData, AppSettings, OutputMode, ConverterComponents
from utilities.output import create_opie_files, create_dict_files, create_lmf_files
from utilities.parse import get_audio_file, extract_elan_data
from utilities.logger import setup_custom_logger
from widgets.mode import MainProjectSelection, ModeSelection
from widgets.elan_import import ELANFileField, TierSelector
from widgets.table import TABLE_COLUMNS, FilterTable
from widgets.export import ExportLocationField, ExportButton
from windows.manifest import ManifestWindow


LOG_CONVERTER = setup_custom_logger("Converter Widget")

BASE_MARGIN = 10


class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.

    Manages the process flow of the Hermes app, initialised by primary window.
    """

    def __init__(self,
                 parent: QWidget,
                 settings: AppSettings) -> None:
        super().__init__()
        self.parent = parent
        self.settings = settings
        self.session = parent.session
        self.components = ConverterComponents(
            progress_bar=self.parent.progress_bar,
            status_bar=self.parent.statusBar()
        )
        self.data = ConverterData()
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        self.setMinimumWidth(650)
        self.layout.setVerticalSpacing(0)
        self.load_main_menu_projects()
        self.setLayout(self.layout)

    def load_main_menu_projects(self):
        """Main Menu: Greet user with the option to:
        1) Start a New Project
        2) Open an Existing Project
        """
        self.components.status_bar.showMessage("Start a new project, or load your existing project.")
        self.components.main_project_select = MainProjectSelection(self)
        self.layout.addWidget(self.components.main_project_select, 0, 0, 1, 8)

    def load_new_project_mode(self):
        """When starting a new project:
        1) Choose ELAN import mode, or
        2) Start from Scratch
        """
        self.components.status_bar.showMessage('Name your project, and choose a mode to begin')
        self.components.project_mode_select = ModeSelection(self)
        self.components.main_project_select.hide()
        self.layout.addWidget(self.components.project_mode_select, 0, 0, 1, 8)

    def load_elan_loader(self) -> None:
        """Elan Import Mode Selected: user to select an ELAN file to load."""
        # First Row (ELAN File Field)
        self.components.status_bar.showMessage('Load an ELAN file to get started')
        self.components.elan_file_field = ELANFileField(self)
        self.components.project_mode_select.hide()
        self.layout.removeWidget(self.components.project_mode_select)
        self.layout.addWidget(self.components.elan_file_field, 0, 0, 1, 8)

    def load_elan_tier_select(self,
                                  components: ConverterComponents,
                                  data: ConverterData) -> None:
        """Elan Import Mode: user to select tiers to import into Hermes"""
        components.status_bar.showMessage('Select transcription and translation tiers, then click import')
        data.eaf_object = pympi.Elan.Eaf(data.elan_file)
        components.tier_selector = TierSelector(self)
        components.tier_selector.populate_tiers(list(data.eaf_object.get_tier_names()))
        self.layout.addWidget(components.tier_selector, 1, 0, 1, 8)

    def load_main_hermes_app(self,
                             components: ConverterComponents,
                             data: ConverterData) -> None:
        """Main hermes app once a file is loaded or a new project has begun is initialised.

        Main app contains the table widget allowing for user input, image uploading, audio recording, and the final
        export process.

        At this stage, main menu functionality is fully activated, and the autosave thread starts.
        """
        if self.data.mode == OperationMode.ELAN:
            data.audio_file = get_audio_file(self.data)
            transcription_tier = components.tier_selector.get_transcription_tier()
            translation_tier = components.tier_selector.get_translation_tier()
            extract_elan_data(transcription_tier, translation_tier, self.data, components)
        else:
            if self.components.project_mode_select:
                self.components.project_mode_select.hide()
            elif self.components.main_project_select:
                self.components.main_project_select.hide()
            self.data.transcriptions.append(Transcription(index=0,
                                                          transcription=""))
        # Filter Table Rows
        self.components.filter_table = FilterTable(self.data,
                                                   self.components.status_bar,
                                                   self.settings)
        self.layout.addWidget(self.components.filter_table, 2, 0, 1, 8)
        self.components.table = self.components.filter_table.table
        # Export Frame
        export_separator = QFrame()
        export_separator.setFrameShape(QFrame.StyledPanel)
        export_separator.setFrameShadow(QFrame.Sunken)
        export_separator.setLineWidth(1)
        export_separator.setContentsMargins(BASE_MARGIN, 1, BASE_MARGIN, 1)
        self.layout.addWidget(export_separator, 3, 0, 5, 8)
        # Export Components, Margins follow (left, top, right, bottom)
        # Header
        export_heading = QLabel("Export")
        header_font = QFont()
        header_font.setFamily('SansSerif')
        header_font.setPointSize(10)
        header_font.setBold(True)
        export_heading.setFont(header_font)
        export_heading.setContentsMargins(BASE_MARGIN + 10, BASE_MARGIN, 0, 0)
        self.layout.addWidget(export_heading, 4, 0, 1, 8)
        # Export Field
        self.components.export_location_field = ExportLocationField(self)
        self.components.export_location_field.setContentsMargins(BASE_MARGIN, 0, BASE_MARGIN, 0)
        self.layout.addWidget(self.components.export_location_field, 5, 0, 1, 8)
        self.components.status_bar.showMessage('Select words to include and choose an export location')
        # Set export location
        self.data.export_location = self.parent.session.export_path
        self.components.export_location_field.set_export_field_text(self.data.export_location)
        # Export Button
        self.components.export_button = ExportButton(self)
        self.components.export_button.setContentsMargins(BASE_MARGIN, 0, BASE_MARGIN, BASE_MARGIN)
        self.layout.addWidget(self.components.export_button, 6, 0, 1, 8)
        # self.components.export_button.setEnabled(False)
        self.enable_export_button()

        # Re-init menu to allow for Open/Save functionality now that table widget exists.
        self.parent.init_menu(True)
        self.parent.session.start_autosave()

    def enable_export_button(self) -> None:
        """Allow final export step, which enables the export button."""
        self.components.status_bar.showMessage('Press the export button to begin the process')
        self.components.export_button.setEnabled(True)

    def setup_project(self) -> None:
        """Sets up the project according to user specifications.

        If the project directory does not yet exist, will create the appropriate
        structure.

        project_root/
            project_name/
                assets/
                    audio/
                    images/
                export/
                templates/
                saves/

        """
        project_root = self.settings.project_root_dir
        project_name = self.session.project_name
        project_path = self.session.project_path
        LOG_CONVERTER.debug(f"Setup Project Root Dir: {project_root}")
        LOG_CONVERTER.debug(f"Setup Project Initialised as: {project_name}")
        LOG_CONVERTER.debug(f"Setup Project Path: {project_path}")

        if not os.path.exists(project_path):
            os.makedirs(project_path)
            os.makedirs(self.session.assets_audio_path)
            os.makedirs(self.session.assets_images_path)
            os.makedirs(self.session.export_path)
            os.makedirs(self.session.templates_path)
            os.makedirs(self.session.saves_path)

    def export_resources(self) -> None:
        self.components.status_bar.clearMessage()
        self.components.progress_bar.show()
        export_count = self.components.table.get_selected_count()
        completed_count = 0
        if self.settings.output_format == OutputMode.DICT:
            with open(os.path.join(self.data.export_location, 'dictionary.csv'), 'w') as file:
                writer = csv.writer(file)
                writer.writerow(['Transcription', 'Translation', 'Audio', 'Image'])
        elif self.settings.output_format == OutputMode.LMF:
            lmf_manifest_window = ManifestWindow(self.parent, self.data)
            _ = lmf_manifest_window.exec()
        opie_index = 0
        for row in range(self.components.table.rowCount()):
            if self.components.table.row_is_checked(row) and \
                    self.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"]):
                self.components.status_bar.showMessage(f'Exporting file {completed_count + 1} of {export_count}')
                if self.settings.output_format == OutputMode.OPIE:
                    create_opie_files(row, self.data, self.components, opie_index)
                    opie_index += 1
                elif self.settings.output_format == OutputMode.DICT:
                    create_dict_files(row, self.data)
                elif self.settings.output_format == OutputMode.LMF:
                    create_lmf_files(row, self.data)
                completed_count += 1
                self.components.progress_bar.update_progress(completed_count / export_count)
        self.components.progress_bar.hide()
        if self.settings.output_format == OutputMode.LMF:
            manifest_file_path = os.path.join(self.data.export_location, 'manifest.json')
            with open(manifest_file_path, 'w') as manifest_file:
                json.dump(self.data.lmf, manifest_file, indent=4)
        self.components.status_bar.showMessage(f'Exported {str(completed_count)} valid words to '
                                               f'{self.data.export_location}')
        QDesktopServices().openUrl(QUrl().fromLocalFile(self.data.export_location))
        LOG_CONVERTER.info(f"Exported {completed_count} transcriptions.")
