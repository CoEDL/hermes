import sys, os
import pytest
from pytest_mock import mocker

from PyQt5.QtWidgets import QApplication, QWidget
from windows.primary import PrimaryWindow, ProgressBarWidget
from widgets.icon import ApplicationIcon
from widgets.converter import ConverterWidget
from widgets.session import SessionManager
from datatypes import AppSettings


'''
Run tests with pytest in ./hermes root directory, or python -m pytest.

pytest --cov src/ for coverage outside PyCharm.

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
        main_fields = [main_window.converter, main_window.progress_bar, main_window.settings, main_window.session,
                       main_window.bar]
        for field in main_fields:
            assert field is not None

    def test_primary_widgets_init(self, main_window: PrimaryWindow):
        assert isinstance(main_window.converter, ConverterWidget)
        assert isinstance(main_window.progress_bar, ProgressBarWidget)
        assert isinstance(main_window.session, SessionManager)
        assert isinstance(main_window.settings, AppSettings)

