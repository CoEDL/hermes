import unittest
from src.main.python.Application.elan2resource import MainWindow


def setup():
    widget = MainWindow()


class BasicTest(unittest.TestCase):
    setup()
    def test1(self):
        self.assertEquals('1', '1')

