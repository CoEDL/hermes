from PyQt5.QtWidgets import QFrame


class HorizontalLineWidget(QFrame):
    """
    Horizontal separator for delineating separate sections of the interface.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
