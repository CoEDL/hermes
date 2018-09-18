import sys, os
import pytest
from pytest_mock import mocker

from datatypes.datatypes import AppSettings
from PyQt5.QtWidgets import QApplication, QWidget
from widgets.converter import ConverterWidget
from widgets.icon import ApplicationIcon
from windows import PrimaryWindow, ProgressBarWidget

'''
Run tests with pytest in ./hermes root directory, or python -m pytest.

-v for verbose, -s to output print
'''


class TestMain:

    @pytest.fixture(scope="class")
    def main_window(self):
        # Setup
        App = QApplication(sys.argv)
        App.setWindowIcon(ApplicationIcon())
        Main = PrimaryWindow(App)
        yield Main

    def test_primary_window_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window, PrimaryWindow)

    def test_progress_widget_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window.progress_bar, ProgressBarWidget)

    def test_converter_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window.converter, ConverterWidget)

    def test_table_menu_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window.table_menu, QWidget)

    def test_menubar_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window.bar, QWidget)

