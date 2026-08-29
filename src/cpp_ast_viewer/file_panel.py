import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QTreeView) 
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from cpp_ast_viewer.ast_parser import AstParser


logger = logging.getLogger(__name__)

class FilePanel(QWidget):
  file_selected = Signal(object, str)
  FILE_PATH_ROLE = Qt.ItemDataRole.UserRole
  TU_ROLE = Qt.ItemDataRole.UserRole + 1
  def __init__(self):
    super().__init__()

    self.search_edit = QLineEdit()
    self.search_edit.setPlaceholderText("Filter files...")

    self.tree_view = QTreeView()
    self.model = QStandardItemModel()
    self.proxy_model = QSortFilterProxyModel(self)
    self.proxy_model.setSourceModel(self.model)
    self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    self.proxy_model.setRecursiveFilteringEnabled(True)
    self.tree_view.setModel(self.proxy_model)
    self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
    self.tree_view.clicked.connect(self._on_tree_clicked)

    layout = QVBoxLayout(self)
    layout.addWidget(self.search_edit)
    layout.addWidget(self.tree_view)

    self.search_edit.textChanged.connect(self._on_search_changed)

  def load_compile_command_json(self, file_path):
    logger.debug(f"load compile_command.json {file_path}")
    self.ast_parser = AstParser(file_path)
    tu_infos = self.ast_parser.GetTuInfos()
    self.load_transition_unit(tu_infos)

  def load_transition_unit(self, tu_infos):
    source_paths = [Path(source) for source, tu_info in tu_infos.items()]
    common_path = Path(os.path.commonpath(source_paths))
    root_item = QStandardItem(str(common_path))
    self.model.clear()
    self.model.appendRow(root_item)
    for source_path, tu_info in tu_infos.items():
      relative_path = Path(source_path).relative_to(common_path)
      self.add_path(root_item, relative_path.parts, source_path, tu_info)
    self.tree_view.expandToDepth(1)

  def add_path(self, parent, parts, full_path, tu_info):
    current = parent
    for part in parts:
      child = self.find_or_create_child(current, part)
      current = child
    current.setText(f"tu:{parts[-1]}")

    source_item = QStandardItem(full_path)
    source_item.setData(full_path, self.FILE_PATH_ROLE)
    source_item.setData(tu_info['tu'], self.TU_ROLE)
    current.appendRow(source_item)
    for include in tu_info['includes']:
      include_item = QStandardItem(include)
      include_item.setData(include, self.FILE_PATH_ROLE)
      include_item.setData(tu_info['tu'], self.TU_ROLE)
      current.appendRow(include_item)
    # current.setData(str(full_path), Qt.ItemDataRole.UserRole)

  def find_or_create_child(self, parent, child_name):
    for row in range(parent.rowCount()):
      child = parent.child(row)
      if child.text() == child_name:
        return child
    child = QStandardItem(child_name)
    parent.appendRow(child)
    return child

  def _on_tree_clicked(self, proxy_index):
    source_index = self.proxy_model.mapToSource(proxy_index)
    item = self.model.itemFromIndex(source_index)
    path = item.data(Qt.ItemDataRole.UserRole)
    tu = item.data(self.TU_ROLE)
    if path:
      self.file_selected.emit(tu, path)
    else:
      current_expend_status = self.tree_view.isExpanded(proxy_index)
      self.tree_view.setExpanded(proxy_index, not current_expend_status)

  def _on_search_changed(self, text):
    self.proxy_model.setFilterFixedString(text)
    if text.strip():
      self.tree_view.expandAll()
    else:
      self.tree_view.expandToDepth(1)
