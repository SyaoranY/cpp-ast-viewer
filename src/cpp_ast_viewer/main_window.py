from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow, QSplitter

from cpp_ast_viewer.ast_view import AstView
from cpp_ast_viewer.file_panel import FilePanel
from cpp_ast_viewer.log_view import LogView
from cpp_ast_viewer.source_view import SourceView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_menu_bar()
        self._init_main_component()

    def _init_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        load_action = file_menu.addAction("&Load compile_command.json")
        load_action.setShortcut(Qt.Key_Open)
        load_action.triggered.connect(self._load_new_compile_comands)

    def _init_main_component(self):
        self._file_panel = FilePanel()
        self._source_view = SourceView()
        self._ast_view = AstView()
        self._log_view = LogView()

        self._init_layout()

        self._file_panel.tu_selected.connect(self._on_tu_selected)
        self._file_panel.file_selected.connect(self._on_file_selected)
        self._ast_view.cursor_selected.connect(self._on_cursor_selected)
        self._source_view.position_clicked.connect(self._on_source_clicked)

    def _init_layout(self):
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.addWidget(self._file_panel)
        top_splitter.addWidget(self._source_view)
        top_splitter.addWidget(self._ast_view)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(top_splitter)
        main_splitter.addWidget(self._log_view)

        self.setCentralWidget(main_splitter)

        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 3)
        top_splitter.setStretchFactor(2, 3)

        main_splitter.setStretchFactor(0, 4)
        main_splitter.setStretchFactor(1, 1)

    def _load_new_compile_comands(self):
        file_filter = "Compilation Database (compile_commands.json)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select compile_command.json", "", file_filter)
        if not file_path:
            return
        self._log_view.new_session("Load compile_commands.json")
        self._source_view.reset_all()
        self._ast_view.reset_all()
        self._file_panel.load_compile_command_json(Path(file_path))

    def _on_tu_selected(self, tu):
        self._ast_view.show_ast(tu)

    def _on_file_selected(self, tu, file_path):
        self._source_view.show_source_code(file_path)
        self._ast_view.show_ast(tu)

    def _on_cursor_selected(self, cursor):
        if cursor.location.file is None:
            return
        file_path = Path(cursor.location.file.name).resolve()
        self._file_panel.select_file(file_path)
        self._source_view.show_source_code(file_path)
        self._source_view.highlight_cursor(cursor)

    def _on_source_clicked(self, path, line, column):
        cursor = self._ast_view.select_at(path, line, column)
        if cursor is not None:
            self._source_view.highlight_cursor(cursor)
