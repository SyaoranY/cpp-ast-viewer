import logging
from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextDocument, QTextCursor, QMouseEvent
from clang.cindex import Cursor, SourceLocation


logger = logging.getLogger(__name__)

class SourceView(QPlainTextEdit):
  position_clicked = Signal(int, int)
  def __init__(self):
    super().__init__()
    self.setReadOnly(True)
    self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

  def mousePressEvent(self, event : QMouseEvent):
    super().mousePressEvent(event)
    cursor = self.cursorForPosition(event.position().toPoint())
    line = cursor.blockNumber() + 1
    column = cursor.positionInBlock() + 1
    self.position_clicked.emit(line, column)

  def show_source_code(self, path):
    try:
      with open(path, "r", encoding="utf-8", errors="replace",) as f:
        self.setPlainText(f.read())
    except Exception as e:
      logger.exception("Failed to open file: %s", str(path))

  def highlight_cursor(self, cursor : Cursor):
    start : SourceLocation = cursor.extent.start
    end : SourceLocation = cursor.extent.end

    document : QTextDocument = self.document()

    start_block = document.findBlockByNumber(start.line - 1)
    end_block = document.findBlockByNumber(end.line - 1)

    start_pos = start_block.position() + start.column - 1
    end_pos = end_block.position() + end.column - 1

    text_cursor = QTextCursor(document)
    text_cursor.setPosition(start_pos)
    text_cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)

    self.setTextCursor(text_cursor)
    self.ensureCursorVisible()