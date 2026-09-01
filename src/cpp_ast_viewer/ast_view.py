import logging
from pathlib import Path
from clang.cindex import Cursor

from PySide6.QtWidgets import (
  QWidget,
  QTreeView,
  QPlainTextEdit,
  QSplitter,
  QVBoxLayout
) 

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel

logger = logging.getLogger(__name__)

class AstTreeView(QTreeView):
  cursor_selected = Signal(object)
  def __init__(self):
    super().__init__()
    self.setEditTriggers(self.EditTrigger.NoEditTriggers)
    self.model = QStandardItemModel()
    self.model.setHorizontalHeaderLabels(["AST"])
    self.setModel(self.model)
    self.clicked.connect(self._on_clicked)

  def show_ast(self, tu, file_path):
    self.model.clear()
    self.model.setHorizontalHeaderLabels(["AST"])
    root = self.model.invisibleRootItem()
    self._add_cursor(tu.cursor, root, file_path)

  def _add_cursor(self, cursor : Cursor, parent_item, file_path):
    location_file = cursor.location.file
    if location_file is not None:
      cursor_file = Path(location_file.name).resolve()
      logger.debug(f"{cursor_file} {file_path}")
      if cursor_file == file_path:
        text = f"{cursor.kind.name}  {cursor.spelling}"
        item = QStandardItem(text)
        item.setData(cursor, Qt.ItemDataRole.UserRole)
        parent_item.appendRow(item)
        parent_item = item
    for child in cursor.get_children():
      self._add_cursor(child, parent_item, file_path)

  def _on_clicked(self, index):
    cursor = index.data(Qt.ItemDataRole.UserRole)
    if cursor is not None:
      self.cursor_selected.emit(cursor)

  def select_at(self, line, column):
    item = self.find_cursor_item(line, column)
    if item is None:
      return None
    index = item.index()
    self._expand_parents(index)
    self.setCurrentIndex(index)
    self.scrollTo(index)
    return item.data(Qt.ItemDataRole.UserRole)

  def _expand_parents(self, index):
    parent = index.parent()
    while parent.isValid():
      self.expand(parent)
      parent = parent.parent()

  def find_cursor_item(self, line, column):
    root = self.model.invisibleRootItem()
    return self._find_cursor_item(root, line, column)

  def _find_cursor_item(self, parent, line, column):
    best_item = None
    for row in range(parent.rowCount()):
      item = parent.child(row)
      cursor = item.data(Qt.ItemDataRole.UserRole)
      start = cursor.extent.start
      end = cursor.extent.end
      pos = (line, column)
      start_pos = (start.line, start.column)
      end_pos = (end.line, end.column)
      if start_pos <= pos <= end_pos:
        best_item = item
        child_item = self._find_cursor_item(item, line, column)
        if child_item is not None:
          best_item = child_item
    return best_item

class AstDetailsView(QPlainTextEdit):
  def __init__(self):
    super().__init__()
    self.setReadOnly(True)

  def show_cursor(self, cursor : Cursor):
    extent = cursor.extent

    text = (
        f"Kind: {cursor.kind.name}\n"
        f"Spelling: {cursor.spelling}\n"
        f"Display name: {cursor.displayname}\n"
        f"Type: {cursor.type.spelling}\n"
        f"\n"
        f"Location: "
        f"{cursor.location.line}:"
        f"{cursor.location.column}\n"
        f"\n"
        f"Extent:\n"
        f"  Start: {extent.start.line}:{extent.start.column}\n"
        f"  End:   {extent.end.line}:{extent.end.column}\n"
    )

    self.setPlainText(text)

class AstView(QWidget):
  cursor_selected = Signal(object)
  def __init__(self):
    super().__init__()
    self.ast_tree_view = AstTreeView()
    self.ast_details_view = AstDetailsView()

    splitter = QSplitter(Qt.Orientation.Vertical)
    splitter.addWidget(self.ast_tree_view)
    splitter.addWidget(self.ast_details_view)

    layout = QVBoxLayout(self)
    layout.addWidget(splitter)

    self.ast_tree_view.cursor_selected.connect(self._on_cursor_selected)

  def show_ast(self, tu, file_path):
    self.ast_tree_view.show_ast(tu, file_path)
    self.ast_details_view.clear()

  def select_at(self, line, column):
    cursor = self.ast_tree_view.select_at(line, column)
    if cursor is not None:
      self.ast_details_view.show_cursor(cursor)
    return cursor

  def _on_cursor_selected(self, cursor : Cursor):
    self.ast_details_view.show_cursor(cursor)
    self.cursor_selected.emit(cursor)

