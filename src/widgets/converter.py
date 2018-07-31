import os
import csv
import pympi
import json
from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from datatypes import OperationMode, Transcription, ConverterData, AppSettings, OutputMode, ConverterComponents
from utilities.output import create_opie_files, create_dict_files, create_lmf_files
from utilities.parse import get_audio_file, extract_elan_data
from widgets.mode import ModeSelection
from widgets.elan_import import ELANFileField, TierSelector
from widgets.table import TABLE_COLUMNS, FilterTable
from widgets.export import ExportLocationField, ExportButton
from windows.manifest import ManifestWindow


class ConverterWidget(QWidget):
    """
    The core widget of the application which contains all of the widgets required to convert ELAN files.
    """

    def __init__(self,
                 parent: QWidget,
                 settings: AppSettings) -> None:
        super().__init__()
        self.parent = parent
        self.settings = settings
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
        self.load_mode_choice()
        self.setLayout(self.layout)

    def load_mode_choice(self):
        self.components.status_bar.showMessage('Choose a mode to begin')
        self.components.mode_select = ModeSelection(self)
        self.layout.addWidget(self.components.mode_select, 0, 0, 1, 8)

    def load_initial_widgets(self) -> None:
        # First Row (ELAN File Field)
        self.components.status_bar.showMessage('Load an ELAN file to get started')
        self.components.elan_file_field = ELANFileField(self)
        self.components.mode_select.hide()
        self.layout.removeWidget(self.components.mode_select)
        self.layout.addWidget(self.components.elan_file_field, 0, 0, 1, 8)

    def load_second_stage_widgets(self,
                                  components: ConverterComponents,
                                  data: ConverterData) -> None:
        components.status_bar.showMessage('Select transcription and translation tiers, then click import')
        data.eaf_object = pympi.Elan.Eaf(data.elan_file)
        components.tier_selector = TierSelector(self)
        components.tier_selector.populate_tiers(list(data.eaf_object.get_tier_names()))
        self.layout.addWidget(components.tier_selector, 1, 0, 1, 8)

    def load_third_stage_widgets(self,
                                 components: ConverterComponents,
                                 data: ConverterData) -> None:
        if self.data.mode == OperationMode.ELAN:
            data.audio_file = get_audio_file(self.data)
            transcription_tier = components.tier_selector.get_transcription_tier()
            translation_tier = components.tier_selector.get_translation_tier()
            extract_elan_data(transcription_tier, translation_tier, self.data, components)
        else:
            self.components.mode_select.hide()
            self.data.transcriptions.append(Transcription(index=0,
                                                          transcription=""))
        # Sixth Row (Filter & Selector)
        self.components.filter_table = FilterTable(self.data,
                                                   self.components.status_bar,
                                                   self.settings)
        self.layout.addWidget(self.components.filter_table, 2, 0, 1, 8)
        self.components.table = self.components.filter_table.table
        # Eighth Row (Export Location)
        components.export_location_field = ExportLocationField(self)
        self.layout.addWidget(components.export_location_field, 3, 0, 1, 8)
        components.status_bar.showMessage('Select words to include and choose an export location')

    def load_fourth_stage_widgets(self) -> None:
        # Ninth Row (Export Button)
        export_button = ExportButton(self)
        self.layout.addWidget(export_button, 4, 0, 1, 8)
        self.components.status_bar.showMessage('Press the export button to begin the process')

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
            lmf_manifest_window = ManifestWindow(self.data)
            _ = lmf_manifest_window.exec()
        for row in range(self.components.table.rowCount()):
            if self.components.table.row_is_checked(row) and \
                    self.components.table.get_cell_value(row, TABLE_COLUMNS["Transcription"]):
                self.components.status_bar.showMessage(f'Exporting file {completed_count + 1} of {export_count}')
                if self.settings.output_format == OutputMode.OPIE:
                    create_opie_files(row, self.data, self.components)
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
