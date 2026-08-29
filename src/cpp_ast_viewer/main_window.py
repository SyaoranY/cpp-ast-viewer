import logging

from PySide6.QtWidgets import (QMainWindow, QSplitter, QFileDialog)
from PySide6.QtCore import Qt
from cpp_ast_viewer.file_panel import FilePanel
from cpp_ast_viewer.source_view import SourceView
from cpp_ast_viewer.ast_view import AstView
from cpp_ast_viewer.log_view import LogView, QtLogHandler

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.init_menu_bar()
    self.file_panel = FilePanel()
    self.source_view = SourceView()
    self.ast_view = AstView()
    self.log_view = LogView()

    self.file_panel.file_selected.connect(self._on_file_selected)
    self.ast_view.cursor_selected.connect(self.source_view.highlight_cursor)
    self.source_view.position_clicked.connect(self._on_source_clicked)

    self.log_handler = QtLogHandler()
    self.log_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    self.log_handler.emitter.message.connect(self.log_view.log)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(self.log_handler)

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

  def init_menu_bar(self):
    menu_bar = self.menuBar()
    file_menu = menu_bar.addMenu("&File")
    load_action = file_menu.addAction("&Load compile_command.json")
    load_action.setShortcut(Qt.Key_Open)
    load_action.triggered.connect(self.load_compile_command_json)

  def load_compile_command_json(self):
    file_filter = "Compilation Database (compile_commands.json)"
    file_path, _ = QFileDialog.getOpenFileName(self, "Select compile_command.json", "", file_filter)
    if not file_path:
      return
    self.file_panel.load_compile_command_json(file_path)

  def _on_file_selected(self, tu, file_path):
    self.source_view.load_file(file_path)
    self.ast_view.load_ast(tu, file_path)

  def _on_source_clicked(self, line, column):
    cursor = self.ast_view.select_at(line, column)
    if cursor is not None:
      self.source_view.highlight_cursor(cursor)