import pyaudio
import wave


class AudioRecorder(object):
    def __init__(self, channels=1, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer

    def open(self, file_name, mode='wb'):
        return WavFile(file_name, mode, self.channels, self.rate,
                       self.frames_per_buffer)


class WavFile(object):
    def __init__(self, file_name, mode, channels,
                 rate, frames_per_buffer):
        self.file_name = file_name
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self._pa = pyaudio.PyAudio()
        self.wav_file = self.prepare_wav_file(self.file_name, self.mode)
        self._stream = None

    def start_recording(self):
        self._stream = self._pa.open(format=pyaudio.paInt16,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.frames_per_buffer,
                                     stream_callback=self.get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wav_file.writeframes(in_data)
            return in_data, pyaudio.paContinue

        return callback

    def close(self):
        self._stream.close()
        self._pa.terminate()
        self.wav_file.close()

    def prepare_wav_file(self, file_name, mode='wb'):
        wav_file = wave.open(file_name, mode)
        wav_file.setnchannels(self.channels)
        wav_file.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wav_file.setframerate(self.rate)
        return wav_file
