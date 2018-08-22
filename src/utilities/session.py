from PyQt5.QtWidgets import QFileDialog

class SessionFile(object):
    '''
    Session File stores and saves progress.
    '''

    def __init__(self):
        self.file_name = None
        self.file_contents = None

    def open_file(self):
        file_dialogue = QFileDialog()
        file_name, _ = file_dialogue.getOpenFileName(file_dialogue, "Open Hermes Session", "", "hermes (*.hermes)")
        self.set_file_name(file_name)

        try:
            with open(self.get_file_name()) as file:
                self.file_contents = file.readlines()
        except (OSError, IOError) as e:
            print("No file to open: " + e)

        print(self.file_name)
        print(self.file_contents)

    def save_as_file(self):
        file_dialogue = QFileDialog()
        file_name, _ = file_dialogue.getSaveFileName(file_dialogue, "Save As", "mysession.hermes", "hermes (*.hermes)")
        with open(file_name, 'a') as f:
            f.write("Save works!\n")
        self.set_file_name(file_name)

    def save_file(self):
        if self.get_file_name() is not None:
            with open(self.get_file_name(), 'a') as f:
                f.write("Saved from save!\n")

    def set_file_name(self, file_name: str):
        self.file_name = file_name

    def get_file_name(self):
        return self.file_name
