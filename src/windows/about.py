from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QMainWindow, QLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from utilities import resource_path


REPO_LINK = 'https://github.com/CoEDL/hermes'
VERSION = '0.6.3'


class AboutWindow(QDialog):
    def __init__(self, parent: QMainWindow = None) -> None:
        super().__init__(parent)
        self.layout = QGridLayout()
        self.init_ui()

    def init_ui(self) -> None:
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        logo_label = QLabel()
        logo_image = QPixmap(resource_path('./img/icon-5-128.png'))
        logo_label.setPixmap(logo_image)
        self.setWindowTitle('About')
        self.layout.addWidget(logo_label, 0, 1, 1, 1)
        name_label = QLabel('<b>Hermes</b><br/><i>The Language Resource Creator</i></b>')
        name_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(name_label, 1, 0, 1, 3)
        version_label = QLabel(f'Version {VERSION}')
        version_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(version_label, 2, 0, 1, 3)
        link_label = QLabel(f'<a href="{REPO_LINK}">Report Issues Here</a>')
        link_label.setAlignment(Qt.AlignCenter)
        link_label.setTextFormat(Qt.RichText)
        link_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link_label.setOpenExternalLinks(True)
        self.layout.addWidget(link_label, 3, 0, 1, 3)
        self.setLayout(self.layout)
        self.show()
