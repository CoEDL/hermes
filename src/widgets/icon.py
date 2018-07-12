from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from utilities import resource_path


class ApplicationIcon(QIcon):
    """
    Custom icon for the application to appear in the task bar (and in the MainWindow header on Windows).
    """
    def __init__(self) -> None:
        super().__init__()
        self.addFile(resource_path('./img/language-48.png'), QSize(48, 48))
        self.addFile(resource_path('./img/language-96.png'), QSize(96, 96))
        self.addFile(resource_path('./img/language-192.png'), QSize(192, 192))
        self.addFile(resource_path('./img/language-256.png'), QSize(256, 256))


