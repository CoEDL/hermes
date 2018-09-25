import sys
import pytest

from PyQt5.QtWidgets import QApplication
from datatypes import *


class TestWindowPrimary:

    @pytest.fixture(scope="function")
    def converter_data(self):
        # Setup
        converter_data = ConverterData()
        yield converter_data

    def test_converter_data_init(self, converter_data):
        assert isinstance(converter_data, ConverterData)
        assert not converter_data.elan_file
        assert not converter_data.eaf_object
        assert not converter_data.audio_file
        assert not converter_data.transcriptions
        assert not converter_data.translations
        assert not converter_data.temp_file
        assert not converter_data.mode
        assert not converter_data.lmf

    def test_create_blank_lmf(self, converter_data):
        assert not converter_data.lmf
        empty_lmf = create_lmf("TranscriptionLang", "TranslationLang", "Author")
        converter_data.lmf = create_lmf("French", "English", "Fake Person")
        # Empty LMF dict with no words holds 5 items.
        assert len(converter_data.lmf) == len(empty_lmf)


