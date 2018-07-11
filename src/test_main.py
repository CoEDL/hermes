import sys
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from .main import MainWindow


def setup():
    widget = MainWindow()


class BasicTest(unittest.TestCase):
    setup()
    def test1(self):
        self.assertEquals('1', '1')

