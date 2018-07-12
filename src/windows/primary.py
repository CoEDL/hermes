import math
from PyQt5.QtWidgets import QProgressBar, QApplication, QMainWindow, QLayout, QAction
from typing import Union
from widgets.converter import ConverterWidget
from windows.about import AboutWindow
from windows.settings import SettingsWindow


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
        self.title = 'Language Resource Creator'
        self.converter = None
        self.progress_bar = None
        self.table_menu = None
        self.bar = self.menuBar()
        self.init_ui()
        self.init_menu()

    def init_ui(self) -> None:
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.setWindowTitle(self.title)
        self.progress_bar = ProgressBarWidget(self.app)
        self.converter = ConverterWidget(parent=self)
        self.setCentralWidget(self.converter)
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def init_menu(self) -> None:
        file = self.bar.addMenu('File')

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

        self.table_menu = self.bar.addMenu('Table')
        add_row_menu_item = QAction('Add Row', self)
        add_row_menu_item.setShortcut('Ctrl+N')
        add_row_menu_item.triggered.connect(self.on_click_add_row)
        self.table_menu.addAction(add_row_menu_item)

        help_menu = self.bar.addMenu('Help')
        about_menu_item = QAction('About', self)
        about_menu_item.setShortcut('Ctrl+H')
        about_menu_item.triggered.connect(self.on_click_about)
        help_menu.addAction(about_menu_item)

    def on_click_about(self) -> None:
        about = AboutWindow(self)
        about.show()

    def on_click_settings(self) -> None:
        settings = SettingsWindow(self, self.converter)
        settings.show()

    def on_click_reset(self) -> None:
        self.init_ui()
        self.shrink()

    def on_click_add_row(self) -> None:
        if self.converter.components.table:
            self.converter.components.filter_table.add_blank_row()

    def shrink(self) -> None:
        self.resize(0, 0)