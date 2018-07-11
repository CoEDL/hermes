import os
import sys
from PyQt5.QtWidgets import QFileDialog


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def open_folder_dialogue() -> str:
    file_dialogue = QFileDialog()
    file_dialogue.setOption(QFileDialog.ShowDirsOnly, True)
    file_name = file_dialogue.getExistingDirectory(file_dialogue,
                                                   'Choose an export folder',
                                                   os.path.expanduser('~'),
                                                   QFileDialog.ShowDirsOnly)
    return file_name


def open_file_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'ELAN Files (*.eaf)',
                                                 options=options)
    return file_name


def open_image_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'Image Files (*.png *.jpg)',
                                                 options=options)
    return file_name


def open_audio_dialogue() -> str:
    file_dialogue = QFileDialog()
    options = QFileDialog.Options()
    file_name, _ = file_dialogue.getOpenFileName(file_dialogue,
                                                 'QFileDialog.getOpenFileName()',
                                                 '',
                                                 'Audio Files (*.wav *.mp3)',
                                                 options=options)
    return file_name
