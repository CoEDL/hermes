from PyQt5.QtWidgets import QFileDialog


class SessionManager(object):
    """
    Session Manager handles session operations.
    """

    def __init__(self):
        self.session_data = None
        self._file_dialog = QFileDialog()

    def open_file(self):
        file_name, _ = self._file_dialog.getOpenFileName(self._file_dialog, "Open Hermes Session", "", "hermes (*.hermes)")
        self.update_session(file_name)

        print(self.session_data.get_file_name())
        print(self.session_data.get_session_data())

    def save_as_file(self):
        file_name, _ = self._file_dialog.getSaveFileName(self._file_dialog, "Save As", "mysession.hermes", "hermes (*.hermes)")
        with open(file_name, 'a') as f:
            f.write("Save works!\n")
        self.update_session(file_name)

    def save_file(self):
        file_name = self.session_data.get_file_name()
        if file_name is not None:
            with open(file_name, 'a') as f:
                f.write("Saved from save!\n")
        self.update_session(file_name)

    def update_session(self, file_name: str):
        self.session_data = SessionFile(file_name)
        self.parse(self.session_data.get_file_name())

    def parse(self, file_name: str):
        try:
            with open(file_name, 'r') as file:
                self.session_data.parse_data(file.readlines())
        except (OSError, IOError) as e:
            print("No file to open: {}".format(e))


class SessionFile(object):
    """Data structure holding stored data from a session."""

    def __init__(self, file_name: str):
        self._file_name = file_name
        self._data = None

    def set_file_name(self, file_name: str):
        self._file_name = file_name

    def get_file_name(self):
        return self._file_name

    def parse_data(self, data):
        # TODO: Actual data structure and parse.
        self._data = data

    def get_session_data(self):
        return self._data
