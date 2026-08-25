from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt

from file_panel import FilePanel
from source_view import SourceView
from ast_view import AstView
from log_view import LogView

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.file_panel = FilePanel()
    self.source_view = SourceView()
    self.ast_view = AstView()
    self.log_view = LogView()

    self.top_splitter = QSplitter(Qt.Orientation.Horizontal)
    self.top_splitter.addWidget(self.file_panel)
    self.top_splitter.addWidget(self.source_view)
    self.top_splitter.addWidget(self.ast_view)

    self.main_splitter = QSplitter(Qt.Orientation.Vertical)
    self.main_splitter.addWidget(self.top_splitter)
    self.main_splitter.addWidget(self.log_view)

    self.setCentralWidget(self.main_splitter)

    self.top_splitter.setStretchFactor(0, 1)
    self.top_splitter.setStretchFactor(1, 3)
    self.top_splitter.setStretchFactor(2, 3)

    self.main_splitter.setStretchFactor(0, 4)
    self.main_splitter.setStretchFactor(1, 1)