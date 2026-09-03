import logging
from pathlib import Path
from clang.cindex import Cursor
from dataclasses import dataclass
from enum import Enum, auto

from cpp_ast_viewer.ast_details_view import AstDetailsView

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (QWidget, QTreeView, QSplitter, QVBoxLayout)


logger = logging.getLogger(__name__)

class ItemType(Enum):
  LEAF = auto()
  EXPANDED = auto()
  UNEXPANDED = auto()

@dataclass
class CursorData:
  cursor : Cursor
  type : ItemType

class AstTreeView(QTreeView):
  cursor_selected = Signal(Cursor)
  def __init__(self):
    super().__init__()
    self.setEditTriggers(self.EditTrigger.NoEditTriggers)
    self.model = QStandardItemModel()
    self.model.setHorizontalHeaderLabels(["AST"])
    self.setModel(self.model)
    self.clicked.connect(self._on_clicked)
    self.expanded.connect(self._on_expanded)

  def reset_view(self):
    self.model.clear()
    self.model.setHorizontalHeaderLabels(["AST"])

  def show_ast(self, tu):
    self.reset_view()
    root = self.model.invisibleRootItem()
    root.setData(tu)
    self._add_cursor(tu.cursor, root)

  def _add_cursor(self, cursor : Cursor, parent_item):
    text = f"{cursor.kind.name}  {cursor.spelling}"
    item = QStandardItem(text)
    parent_item.appendRow(item)
    # add dummy child item
    children = list(cursor.get_children())
    if children:
      dummy = QStandardItem()
      item.appendRow(dummy)
      item.setData(CursorData(cursor=cursor, type=ItemType.UNEXPANDED))
    else:
      item.setData(CursorData(cursor=cursor, type=ItemType.LEAF))

  def _on_clicked(self, index):
    item = self.model.itemFromIndex(index)
    cursor = item.data().cursor
    if cursor is not None:
      self.cursor_selected.emit(cursor)

  def _on_expanded(self, index):
    item = self.model.itemFromIndex(index)
    cursor_data : CursorData = item.data()
    if cursor_data.type == ItemType.UNEXPANDED:
      item.removeRows(0, item.rowCount())
    for child in cursor_data.cursor.get_children():
      self._add_cursor(child, item)
    cursor_data.type == ItemType.EXPANDED

  def select_at(self, path, line, column):
    cursor = self._get_cursor_at(path, line, column) 

    # TODO
    return cursor
    # item = self.find_cursor_item(path, line, column) # TODO lazy load cursor
    # if item is None:
    #   return None
    # index = item.index()
    # self._expand_parents(index)
    # self.setCurrentIndex(index)
    # self.scrollTo(index)
    # return item.data().cursor

  def _get_cursor_at(self, path, line, column) -> Cursor:
    tu = self.model.invisibleRootItem().data()
    location = tu.get_location(str(path), (line, column))
    cursor = Cursor.from_location(tu, location)
    return cursor

  def _expand_parents(self, index):
    parent = index.parent()
    while parent.isValid():
      self.expand(parent)
      parent = parent.parent()

  def find_cursor_item(self, path, line, column):
    root = self.model.invisibleRootItem()
    return self._find_cursor_item(root, line, column)

  def _find_cursor_item(self, parent, line, column):
    best_item = None
    for row in range(parent.rowCount()):
      item = parent.child(row)
      cursor = item.data()
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


class AstView(QWidget):
  cursor_selected = Signal(Cursor)
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

  def reset_view(self):
    self.ast_tree_view.reset_view()
    self.ast_details_view.reset_view()

  def show_ast(self, tu):
    self.ast_tree_view.show_ast(tu)
    self.ast_details_view.reset_view()

  def select_at(self, path, line, column):
    cursor = self.ast_tree_view.select_at(path, line, column)
    if cursor is not None:
      self.ast_details_view.show_cursor(cursor)
    return cursor

  def _on_cursor_selected(self, cursor : Cursor):
    self.ast_details_view.show_cursor(cursor)
    self.cursor_selected.emit(cursor)

