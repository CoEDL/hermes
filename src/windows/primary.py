import math
import pydub
import logging
import webbrowser
from PyQt5.QtWidgets import QProgressBar, QApplication, QMainWindow, QAction
from typing import Union
from datatypes import AppSettings
from utilities.settings import load_system_settings, system_settings_exist, save_system_settings
from widgets.session import SessionManager
from widgets.converter import ConverterWidget
from windows.about import AboutWindow, ONLINE_DOCS
from windows.settings import SettingsWindow


PRIMARY_LOG = logging.getLogger("PrimaryWindow")


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
        self.primary_log = logging.getLogger("PrimaryWindow")
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
        # self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowTitle(self.title)
        self.progress_bar = ProgressBarWidget(self.app)
        if system_settings_exist():
            self.settings = load_system_settings()
            if self.settings.ffmpeg_location:
                pydub.AudioSegment.converter = self.settings.ffmpeg_location
        else:
            self.settings = AppSettings()
        self.converter = ConverterWidget(parent=self,
                                         settings=self.settings)
        self.setCentralWidget(self.converter)
        self.session = SessionManager(self, self.converter)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def init_menu(self, save_flag: bool = False) -> None:
        self.primary_log.info(f'Menu Bar initialised with save: {save_flag}')

        self.bar.clear()
        file = self.bar.addMenu('File')

        open_menu = QAction('Open', self)
        open_menu.triggered.connect(self.on_click_open)
        open_menu.setShortcut('Ctrl+O')
        file.addAction(open_menu)
        open_menu.setEnabled(save_flag)

        save_menu = QAction('Save', self)
        save_menu.triggered.connect(self.on_click_save)
        save_menu.setShortcut('Ctrl+S')
        file.addAction(save_menu)
        save_menu.setEnabled(save_flag)

        save_as_menu = QAction('Save As', self)
        save_as_menu.triggered.connect(self.on_click_save_as)
        save_as_menu.setShortcut('Ctrl+Shift+S')
        file.addAction(save_as_menu)
        save_as_menu.setEnabled(save_flag)

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
        quit_menu_item.triggered.connect(self.close)
        file.addAction(quit_menu_item)

        template = self.bar.addMenu('Templates')
        template_save = QAction('Create Template', self)
        template_save.triggered.connect(self.on_click_template_save)
        template_save.setShortcut('Ctrl+Alt+T')
        template.addAction(template_save)
        template_save.setEnabled(save_flag)

        template_open = QAction('Load Template', self)
        template_open.triggered.connect(self.on_click_template_open)
        template_open.setShortcut('Ctrl+Alt+O')
        template.addAction(template_open)
        template_open.setEnabled(save_flag)

        self.table_menu = self.bar.addMenu('Table')
        add_row_menu_item = QAction('Add Row', self)
        add_row_menu_item.setShortcut('Ctrl+N')
        add_row_menu_item.triggered.connect(self.on_click_add_row)
        self.table_menu.addAction(add_row_menu_item)

        help_menu = self.bar.addMenu('Help')
        about_menu_item = QAction('About', self)
        about_menu_item.setShortcut('Ctrl+A')
        about_menu_item.triggered.connect(self.on_click_about)
        help_menu.addAction(about_menu_item)

        online_help_item = QAction('Online Docs', self)
        online_help_item.setShortcut('Ctrl+H')
        online_help_item.triggered.connect(self.on_click_online_help)
        help_menu.addAction(online_help_item)

    def on_click_about(self) -> None:
        about = AboutWindow(self)
        about.show()

    def on_click_settings(self) -> None:
        settings = SettingsWindow(parent=self,
                                  converter=self.converter)
        settings.show()

    def on_click_reset(self) -> None:
        self.session.session_filename = None
        self.session.end_autosave()
        self.init_ui()
        self.init_menu()
        self.shrink()

    def on_click_add_row(self) -> None:
        if self.converter.components.table:
            self.converter.components.filter_table.add_blank_row()

    def on_click_save_as(self) -> None:
        self.session.save_as_file()
        save_system_settings(self.settings)

    def on_click_save(self) -> None:
        self.session.save_file()
        save_system_settings(self.settings)

    def on_click_open(self) -> None:
        self.session.open_file()

    def on_click_template_save(self) -> None:
        self.session.save_template()

    def on_click_template_open(self) -> None:
        self.session.open_template()

    def on_click_online_help(self) -> None:
        webbrowser.open(ONLINE_DOCS)
        self.primary_log.info(f'Opened default browser to: {ONLINE_DOCS}')

    def shrink(self) -> None:
        self.resize(0, 0)
