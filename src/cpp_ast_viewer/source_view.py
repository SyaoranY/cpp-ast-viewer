import logging
from pathlib import Path

from clang.cindex import Cursor, CursorKind, SourceLocation
from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent, QTextCursor, QTextDocument
from PySide6.QtWidgets import QPlainTextEdit, QLabel, QVBoxLayout, QWidget, QSizePolicy

logger = logging.getLogger(__name__)


class SourceCodeEdit(QPlainTextEdit):
    position_clicked = Signal(Path, int, int)

    def __init__(self):
        super().__init__()
        self.reset_all()

    def reset_all(self):
        self._path = None
        self.clear()
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        if self._path is not None:
            cursor = self.cursorForPosition(event.position().toPoint())
            line = cursor.blockNumber() + 1
            column = cursor.positionInBlock() + 1
            self.position_clicked.emit(self._path, line, column)

    def show_source_code(self, path):
        try:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as f:
                self._path = path
                self.setPlainText(f.read())
        except Exception:
            logger.exception("Failed to open file: %s", str(path))

    def highlight_cursor(self, cursor: Cursor):
        if cursor.kind == CursorKind.NO_DECL_FOUND:
            return
        start: SourceLocation = cursor.extent.start
        end: SourceLocation = cursor.extent.end

        if start.file is None or end.file is None or start.line <= 0 or end.line <= 0:
            return

        document: QTextDocument = self.document()

        start_block = document.findBlockByNumber(start.line - 1)
        end_block = document.findBlockByNumber(end.line - 1)

        start_pos = start_block.position() + start.column - 1
        end_pos = end_block.position() + end.column - 1

        text_cursor = QTextCursor(document)
        text_cursor.setPosition(start_pos)
        text_cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)

        self.setTextCursor(text_cursor)
        self.ensureCursorVisible()

class SourceView(QWidget):
    position_clicked = Signal(Path, int, int)

    def __init__(self):
        super().__init__()
        self._path_label = QLabel()
        self._source_edit = SourceCodeEdit()

        self._path_label.setContentsMargins(8, 4, 8, 4)
        self._path_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._path_label)
        layout.addWidget(self._source_edit)

        self._source_edit.position_clicked.connect(self.position_clicked)

        self.reset_all()

    def reset_all(self):
        self._path_label.clear()
        self._source_edit.reset_all()

    def show_source_code(self, path):
        self._path_label.setText(str(path))
        self._path_label.setToolTip(str(path))
        self._source_edit.show_source_code(path)

    def highlight_cursor(self, cursor: Cursor):
        self._source_edit.highlight_cursor(cursor)