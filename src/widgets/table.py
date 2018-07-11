from PyQt5.QtWidgets import QTableWidget, QWidget, QGridLayout, QTableWidgetItem, QPushButton, QHeaderView, \
    QLabel, QStatusBar, QHBoxLayout, QCheckBox, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QMouseEvent
from typing import List, NewType
from pygame import mixer
from functools import partial
from datatypes import OperationMode, Transcription
from utilities import open_image_dialogue, resource_path
from .formatting import HorizontalLineWidget
from .record import RecordWindow


ConverterData = NewType('ConverterData', object)

TABLE_COLUMNS = {
    'Index': 0,
    'Transcription': 1,
    'Translation': 2,
    'Preview': 3,
    'Image': 4,
    'Include': 5,
}


class TranslationTableWidget(QTableWidget):
    """
    A table containing transcriptions, translations and buttons for live previews, adding images and selectors for
    inclusion in the export process.
    """

    def __init__(self, num_rows: int) -> None:
        super().__init__(num_rows, 6)
        self.setMinimumHeight(200)
        self.setHorizontalHeaderLabels([''] + [column_name for column_name in list(TABLE_COLUMNS.keys())[1:]])
        self.horizontalHeader().setSectionResizeMode(TABLE_COLUMNS['Transcription'], QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(TABLE_COLUMNS['Translation'], QHeaderView.Stretch)
        self.setColumnWidth(TABLE_COLUMNS['Index'], 30)
        self.setColumnWidth(TABLE_COLUMNS['Preview'], 50)
        self.setColumnWidth(TABLE_COLUMNS['Image'], 50)
        self.setColumnWidth(TABLE_COLUMNS['Include'], 50)
        self.verticalHeader().hide()
        self.setSortingEnabled(False)

    def sort_by_index(self) -> None:
        self.sortByColumn(TABLE_COLUMNS['Index'], Qt.AscendingOrder)

    def show_all_rows(self) -> None:
        for row in range(self.rowCount()):
            self.showRow(row)

    def filter_rows(self, string: str) -> None:
        self.setSortingEnabled(False)
        self.show_all_rows()
        for row in range(self.rowCount()):
            if string not in self.get_cell_value(row, TABLE_COLUMNS['Transcription']) and \
                    string not in self.get_cell_value(row, TABLE_COLUMNS['Translation']):
                self.hideRow(row)

    def get_cell_value(self, row, column) -> str:
        return self.item(row, column).text()

    def get_selected_count(self) -> int:
        count = 0
        for row in range(self.rowCount()):
            count += 1 if self.row_is_checked(row) else 0
        return count

    def row_is_checked(self, row) -> bool:
        return self.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked()


class FilterTable(QWidget):
    def __init__(self,
                 data: ConverterData,
                 status_bar) -> None:
        super().__init__()
        self.status_bar = status_bar
        self.layout = QGridLayout()
        self.table = TranslationTableWidget(max(len(data.transcriptions),
                                                len(data.translations)))
        self.filter_field = None
        self.data = data
        self.init_ui()

    def init_ui(self) -> None:
        if self.data.mode == OperationMode.ELAN:
            self.layout.addWidget(HorizontalLineWidget(), 0, 0, 1, 8)
        filter_label = QLabel('Filter Results:')
        self.layout.addWidget(filter_label, 1, 0, 1, 1)
        self.setLayout(self.layout)
        self.filter_field = FilterFieldWidget('', self.table)
        self.layout.addWidget(self.filter_field, 1, 1, 1, 2)
        filter_clear_button = FilterClearButtonWidget('Clear', self.filter_field)
        self.layout.addWidget(filter_clear_button, 1, 3, 1, 1)
        add_row_button = QPushButton('Add Row')
        add_row_button.setToolTip('Left click to add a new blank row to the table')
        add_row_button.clicked.connect(self.add_blank_row)
        self.layout.addWidget(add_row_button, 1, 6, 1, 1)
        select_all_button = QPushButton('Select All')
        select_all_button.setToolTip('Select/Deselect all currently shown transcriptions\n'
                                     'Note: has no effect on filtered (hidden) results')
        select_all_button.clicked.connect(self.on_click_select_all)
        self.layout.addWidget(select_all_button, 1, 7, 1, 1)
        self.populate_table(self.data.transcriptions)
        self.layout.addWidget(self.table, 2, 0, 1, 8)
        self.setLayout(self.layout)

    def populate_table_row(self, row: int) -> None:
        self.table.setItem(row, TABLE_COLUMNS['Index'], TableIndexCell(row))
        self.table.setItem(row, TABLE_COLUMNS['Transcription'],
                           QTableWidgetItem(self.data.transcriptions[row].transcription))
        self.table.setItem(row, TABLE_COLUMNS['Translation'],
                           QTableWidgetItem(self.data.transcriptions[row].translation))
        PreviewButtonWidget(self, row, self.table, transcription=self.data.transcriptions[row])
        ImageButtonWidget(self, row, self.table)
        SelectorCellWidget(row, self.status_bar, self.table)

    def populate_table(self, transcriptions: List[Transcription]) -> None:
        for row in range(len(transcriptions)):
            self.populate_table_row(row)
        self.table.sort_by_index()

    def on_click_select_all(self) -> None:
        if self.all_selected():
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(False)
        else:
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.setChecked(True)

    def all_selected(self) -> bool:
        for row in range(self.table.rowCount()):
            if not self.table.cellWidget(row, TABLE_COLUMNS['Include']).selector.isChecked() \
                    and not self.table.isRowHidden(row):
                return False
        return True

    def add_blank_row(self):
        new_row_index = self.table.rowCount()
        self.table.insertRow(new_row_index)
        self.data.transcriptions.append(Transcription(index=new_row_index,
                                                      transcription=""))
        self.populate_table_row(self.table.rowCount() - 1)


class SelectorCellWidget(QWidget):
    """
    A custom selector cell for inclusion in the TranslationTable.
    Uses a QCheckbox for selection and deselection.
    """

    def __init__(self,
                 row: int,
                 status_bar: QStatusBar,
                 table: TranslationTableWidget) -> None:
        super().__init__()
        self.status_bar = status_bar
        self.table = table
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.selector = QCheckBox()
        self.selector.stateChanged.connect(self.update_select_count)
        self.layout.addWidget(self.selector)
        self.setLayout(self.layout)
        tooltip = 'Check to include in export\nUncheck to exclude from export'
        self.setToolTip(tooltip)
        self.selector.setToolTip(tooltip)
        self.table.setCellWidget(row, TABLE_COLUMNS['Include'], self)

    def update_select_count(self) -> None:
        self.status_bar.showMessage(f'{self.table.get_selected_count()} '
                                    f'valid items selected for export')


class PreviewButtonWidget(QPushButton):
    """
    Custom button for previewing an audio clip.
    """

    right_click = pyqtSignal()

    def __init__(self,
                 parent: FilterTable,
                 row: int,
                 table: TranslationTableWidget,
                 transcription: Transcription = None) -> None:
        super().__init__()
        self.parent = parent
        self.transcription = transcription
        if self.transcription and self.transcription.sample:
            image_icon = QIcon(resource_path('./img/play.png'))
        else:
            image_icon = QIcon(resource_path('./img/no_sample.png'))
        self.setIcon(image_icon)
        self.clicked.connect(partial(self.play_sample, self.transcription))
        self.setToolTip('Left click to hear a preview of the audio for this word')
        table.setCellWidget(row, TABLE_COLUMNS['Preview'], self)
        self.right_click.connect(self.open_record_window)

    def play_sample(self, transcription: Transcription) -> None:
        if transcription.sample:
            sample_file_path = transcription.sample.get_sample_file_path()
            mixer.init()
            sound = mixer.Sound(sample_file_path)
            sound.play()
        else:
            self.parent.status_bar.showMessage('There is no audio for this transcription', 5000)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QPushButton.mousePressEvent(self, event)

        if event.button() == Qt.RightButton:
            self.right_click.emit()

    def open_record_window(self):
        record_window = RecordWindow(self.parent)
        record_window.show()


class ImageButtonWidget(QPushButton):
    """
    Custom button for adding and removing images related to particular translations. For inclusion in rows of the
    TranslationTable.
    """
    right_click = pyqtSignal()

    def __init__(self,
                 parent: FilterTable,
                 row: int,
                 table: TranslationTableWidget) -> None:
        super().__init__()
        self.parent = parent
        self.row = row
        self.image_icon_no = QIcon(resource_path('./img/image-no.png'))
        self.image_icon_yes = QIcon(resource_path('./img/image-yes.png'))
        self.setIcon(self.image_icon_no)
        self.clicked.connect(partial(self.on_click_image, row))
        self.setToolTip('Left click to choose an image for this word\n'
                        'Right click to delete the existing image')
        self.right_click.connect(self.remove_image)
        table.setCellWidget(row, TABLE_COLUMNS['Image'], self)

    def swap_icon_yes(self) -> None:
        self.setIcon(self.image_icon_yes)

    def swap_icon_no(self) -> None:
        self.setIcon(self.image_icon_no)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        QPushButton.mousePressEvent(self, event)

        if event.button() == Qt.RightButton:
            self.right_click.emit()

    def remove_image(self) -> None:
        self.parent.data.transcriptions[self.row].image = None
        self.swap_icon_no()

    def on_click_image(self, row: int) -> None:
        image_path = open_image_dialogue()
        if image_path:
            self.parent.data.transcriptions[row].image = image_path
            self.parent.table.cellWidget(row, TABLE_COLUMNS['Image']).swap_icon_yes()


class FilterFieldWidget(QLineEdit):
    """
    Custom text input field connected to a table.
    Text input to the field will filter the entries in the table.
    """

    def __init__(self, string: str, table: TranslationTableWidget) -> None:
        super().__init__(string)
        self.table = table
        self.textChanged.connect(self.update_table)

    def update_table(self, p_str) -> None:
        if p_str == '':
            self.table.show_all_rows()
        else:
            self.table.filter_rows(p_str)


class FilterClearButtonWidget(QPushButton):
    """
    Custom button connected to a FilterFieldWidget which clears the field, triggering the associated table to show all
    rows.
    """

    def __init__(self, name: str, field: QLineEdit) -> None:
        super().__init__(name)
        self.field = field
        self.clicked.connect(self.clear_filter)
        self.setToolTip('Left click to clear filters and\n'
                        'show all imported transcriptions')

    def clear_filter(self) -> None:
        self.field.setText('')


class TableIndexCell(QTableWidgetItem):
    """
    Custom table cell widget for displaying the index of the given row (centred).
    """

    def __init__(self, value: int) -> None:
        super().__init__()
        self.setTextAlignment(Qt.AlignCenter)
        self.setData(Qt.EditRole, value + 1)
        self.setFlags(self.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsSelectable))
