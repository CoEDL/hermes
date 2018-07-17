from PyQt5.QtWidgets import QMessageBox, QDesktopWidget, QWidget


class WarningMessage(QMessageBox):
    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        self.setIcon(QMessageBox.Warning)
        screen = QDesktopWidget().screenGeometry()
        this = self.sizeHint()
        self.move(screen.width() / 2 - this.width() / 2,
                  screen.height() / 2 - this.height() / 2)
