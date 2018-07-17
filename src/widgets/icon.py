from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize
from utilities import resource_path


class ApplicationIcon(QIcon):
    """
    Custom icon for the application to appear in the task bar (and in the MainWindow header on Windows).
    """
    def __init__(self) -> None:
        super().__init__()
        self.addFile(resource_path('./img/icon-3-48.png'), QSize(48, 48))
        self.addFile(resource_path('./img/icon-3-96.png'), QSize(96, 96))
        self.addFile(resource_path('./img/icon-3-192.png'), QSize(192, 192))
        self.addFile(resource_path('./img/icon-3-256.png'), QSize(256, 256))
        self.addFile(resource_path('./img/icon-3-512.png'), QSize(512, 512))
        self.addFile(resource_path('./img/icon-3-1024.png'), QSize(1024, 1024))
