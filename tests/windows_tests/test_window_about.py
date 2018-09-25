import pytest
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from windows.primary import PrimaryWindow
from windows.about import AboutWindow, NAME, REPO_LINK, VERSION
from widgets.icon import ApplicationIcon


class TestWindowAbout:

    @pytest.fixture(scope="class")
    def about_window(self):
        # Setup
        App = QApplication(sys.argv)
        App.setWindowIcon(ApplicationIcon())
        Main = PrimaryWindow(App)
        about = AboutWindow(Main)
        return about

    def test_about_window_init(self, about_window: AboutWindow):
        assert isinstance(about_window, AboutWindow)
        for i in range(about_window.layout.count()):
            q_widget = about_window.layout.itemAt(i).widget()
            if not q_widget.text():
                assert isinstance(q_widget.pixmap(), QPixmap)
            else:
                assert VERSION in q_widget.text() or REPO_LINK in q_widget.text() or NAME in q_widget.text()
