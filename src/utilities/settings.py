import os
from PyQt5.QtCore import QSettings
from datatypes import AppSettings, AUDIO_QUALITY, AUDIO_QUALITY_REV, OutputMode, OUTPUT_MODES_REV


def get_settings() -> QSettings:
    return QSettings('CoEDL', 'Language Resource Creator')


def system_settings_exist() -> bool:
    if os.path.exists(get_settings().fileName()):
        print(get_settings().fileName())
        return True
    else:
        return False


def print_system_settings() -> None:
    system_settings = get_settings()
    print(system_settings.value('Audio Quality'))
    print(system_settings.value('Output Format'))
    print(system_settings.value('Microphone'))


def load_system_settings(app_settings: AppSettings) -> None:
    print_system_settings()
    system_settings = get_settings()
    app_settings.audio_quality = AUDIO_QUALITY[system_settings.value('Audio Quality')]
    app_settings.output_format = list(OutputMode)[int(system_settings.value('Output Format'))]
    app_settings.microphone = system_settings.value('Microphone')


def save_system_settings(app_settings: AppSettings) -> None:
    system_settings = get_settings()
    system_settings.setValue('Audio Quality', AUDIO_QUALITY_REV[app_settings.audio_quality])
    system_settings.setValue('Output Format', app_settings.output_format.value)
    system_settings.setValue('Microphone', app_settings.microphone)
    system_settings.sync()
    print_system_settings()
