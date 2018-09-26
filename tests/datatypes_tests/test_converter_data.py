import pytest

from datatypes import *
import utilities.output as output


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

    def test_lmf_one_transcription(self, converter_data):
        # Transcription create
        transcription_object = Transcription(0, "Bonjour", "Hello")
        converter_data.transcriptions.append(transcription_object)
        assert len(converter_data.transcriptions) == 1
        assert converter_data.transcriptions[0].index == 0
        assert converter_data.transcriptions[0].transcription == "Bonjour"
        assert converter_data.transcriptions[0].translation == "Hello"

        # Language Manifest
        converter_data.lmf = create_lmf("French", "English", "Fake Person")
        output.create_lmf_files(0, converter_data)
        assert len(converter_data.lmf) == 5
        word_count = len(converter_data.lmf['words'])
        assert word_count == 1
        for i in range(word_count):
            assert converter_data.lmf['words'][i]['transcription'] == converter_data.transcriptions[i].transcription
            assert converter_data.transcriptions[i].translation in converter_data.lmf['words'][i]['translation']



