import math
import pydub
import webbrowser
from PyQt5.QtWidgets import QProgressBar, QApplication, QMainWindow, QAction, QMessageBox
from typing import Union
from datatypes import AppSettings, OperationMode
from utilities.logger import setup_custom_logger
from utilities.settings import load_system_settings, system_settings_exist, save_system_settings
from widgets.session import SessionManager
from widgets.converter import ConverterWidget
from windows.about import AboutWindow, ONLINE_DOCS
from windows.project import ProjectDetailsWindow
from windows.settings import SettingsWindow


LOG_PRIMARY = setup_custom_logger("Primary")


class ProgressBarWidget(QProgressBar):
    """
    Custom progress bar for showing the progress of exporting transcription/translation/image/sound files.
    """

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.setMaximum(100)
        self.setMinimum(0)
        self.setValue(0)

    def update_progress(self, value: Union[float, int]) -> None:
        self.setValue(math.ceil(value * 100))
        self.app.processEvents()


class PrimaryWindow(QMainWindow):
    """
    The primary window for the application which houses the Converter, menus, statusbar and progress bar.
    """

    def __init__(self, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.title = 'Hermes: The Language Resource Creator'
        self.converter = None
        self.progress_bar = None
        self.table_menu = None
        self.settings = None
        self.session = None
        self.bar = self.menuBar()
        self.init_ui()
        self.init_menu()

    def init_ui(self) -> None:
        self.setWindowTitle(self.title)
        self.progress_bar = ProgressBarWidget(self.app)
        if system_settings_exist():
            self.settings = load_system_settings()
            if self.settings.ffmpeg_location:
                pydub.AudioSegment.converter = self.settings.ffmpeg_location
        else:
            self.settings = AppSettings()
        self.session = SessionManager(self)
        self.converter = ConverterWidget(parent=self,
                                         settings=self.settings)
        self.session.converter = self.converter
        self.setCentralWidget(self.converter)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def init_menu(self, save_flag: bool = False) -> None:
        LOG_PRIMARY.debug(f'Menu Bar initialised with save: {save_flag}')

        self.bar.clear()

        file = self.bar.addMenu('File')
        open_menu = QAction('Open Project', self)
        open_menu.triggered.connect(self.on_click_open)
        open_menu.setShortcut('Ctrl+O')
        file.addAction(open_menu)

        save_menu = QAction('Save Project', self)
        save_menu.triggered.connect(self.on_click_save)
        save_menu.setShortcut('Ctrl+S')
        file.addAction(save_menu)
        save_menu.setEnabled(save_flag)

        settings_menu = QAction('Settings', self)
        settings_menu.triggered.connect(self.on_click_settings)
        settings_menu.setShortcut('Ctrl+B')
        file.addAction(settings_menu)

        reset_menu_item = QAction('Reset', self)
        reset_menu_item.triggered.connect(self.on_click_reset)
        reset_menu_item.setShortcut('Ctrl+R')
        file.addAction(reset_menu_item)

        quit_menu_item = QAction('Quit', self)
        quit_menu_item.setShortcut('Ctrl+Q')
        quit_menu_item.triggered.connect(self.on_click_quit)
        file.addAction(quit_menu_item)

        data_menu = self.bar.addMenu('Project')
        project_details_item = QAction('Project Details', self)
        project_details_item.setShortcut('Ctrl+P')
        project_details_item.triggered.connect(self.on_click_project_details)
        data_menu.addAction(project_details_item)
        project_details_item.setEnabled(save_flag)

        template = self.bar.addMenu('Templates')
        template_save = QAction('Create Template', self)
        template_save.triggered.connect(self.on_click_template_create)
        template_save.setShortcut('Ctrl+Alt+T')
        template.addAction(template_save)
        template_save.setEnabled(save_flag)

        template_open = QAction('Load Template', self)
        template_open.triggered.connect(self.on_click_template_load)
        template_open.setShortcut('Ctrl+Alt+O')
        template.addAction(template_open)
        template_open.setEnabled(save_flag)

        table_menu = self.bar.addMenu('Table')
        add_row_menu_item = QAction('Add Row', self)
        add_row_menu_item.setShortcut('Ctrl+N')
        add_row_menu_item.triggered.connect(self.on_click_add_row)
        table_menu.addAction(add_row_menu_item)

        help_menu = self.bar.addMenu('Help')
        about_menu_item = QAction('About', self)
        about_menu_item.setShortcut('Ctrl+A')
        about_menu_item.triggered.connect(self.on_click_about)
        help_menu.addAction(about_menu_item)

        online_help_item = QAction('Online Docs', self)
        online_help_item.setShortcut('Ctrl+H')
        online_help_item.triggered.connect(self.on_click_online_help)
        help_menu.addAction(online_help_item)

    def on_click_quit(self) -> None:
        if self.converter.components.table:
            if not self.query_save_and_progress():
                return
        self.close()

    def on_click_about(self) -> None:
        about = AboutWindow(self)
        about.show()

    def on_click_settings(self) -> None:
        settings = SettingsWindow(parent=self,
                                  converter=self.converter)
        settings.show()

    def on_click_reset(self) -> None:
        if self.converter.components.table:
            if not self.query_save_and_progress():
                return
        self.session.end_autosave()
        self.init_ui()
        self.init_menu()
        self.shrink()

    def on_click_add_row(self) -> None:
        if self.converter.components.table:
            self.converter.components.filter_table.add_blank_row()

    def on_click_project_details(self) -> None:
        ProjectDetailsWindow(self, self.session).exec()

    def on_click_save(self) -> None:
        self.session.save_project()
        save_system_settings(self.settings)

    def on_click_open(self) -> None:
        if self.converter.components.table:
            if not self.query_save_and_progress():
                return
        self.converter.data.mode = OperationMode.SCRATCH
        if self.session.open_project():
            self.converter.load_main_hermes_app(self.converter.components,
                                                self.converter.data)
            self.session.load_project_save()

    def on_click_template_create(self) -> None:
        self.session.create_template()

    def on_click_template_load(self) -> None:
        self.session.load_template()

    def on_click_online_help(self) -> None:
        webbrowser.open(ONLINE_DOCS)
        LOG_PRIMARY.info(f'Opened default browser to: {ONLINE_DOCS}')

    def query_save_and_progress(self) -> bool:
        """Precautionary save call on project refresh event.

        E.g., App close, starting or opening a new project, etc.

        Returns:
            True if progression desired, false when cancel triggered.
        """
        save_query = QMessageBox.question(self, " ", "Do you want to save before continuing?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        if save_query == QMessageBox.Yes:
            self.session.save_project()
        elif save_query == QMessageBox.Cancel:
            return False
        return True

    def shrink(self) -> None:
        self.resize(0, 0)
