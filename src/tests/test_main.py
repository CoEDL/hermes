import sys, os
import pytest
from PyQt5.QtWidgets import QApplication
from widgets.icon import ApplicationIcon
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from windows import PrimaryWindow

'''
Run tests with pytest in ./hermes root directory, or python -m pytest.

-v for verbose, -s to output print
'''

class TestMain:

    @pytest.fixture(scope="class")
    def main_app(self):
        # Setup
        app = QApplication(sys.argv)
        app.setWindowIcon(ApplicationIcon())
        yield app
        # Teardown
        app = None

    def test_primary_window_exists(self, main_app: QApplication):
        assert isinstance(main_app, QApplication)
        main = PrimaryWindow(main_app)
        assert main is not None and isinstance(main, PrimaryWindow)

