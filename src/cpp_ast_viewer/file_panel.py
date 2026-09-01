import os
import logging
from pathlib import Path
from clang.cindex import TranslationUnit
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QTreeView) 
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from cpp_ast_viewer.ast_parser import AstParser, AstTuInfo


logger = logging.getLogger(__name__)

class FilePanel(QWidget):
  file_selected = Signal(TranslationUnit, Path)
  FILE_PATH_ROLE = Qt.ItemDataRole.UserRole
  TU_ROLE = Qt.ItemDataRole.UserRole + 1

  def __init__(self):
    super().__init__()

    self._search_edit = QLineEdit()
    self._search_edit.setPlaceholderText("Filter files...")

    self._model = QStandardItemModel()

    self._proxy_model = self._create_filter_proxy_model(self._model)

    self._tree_view = QTreeView()
    self._tree_view.setModel(self._proxy_model)
    self._tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

    layout = QVBoxLayout(self)
    layout.addWidget(self._search_edit)
    layout.addWidget(self._tree_view)

    self._search_edit.textChanged.connect(self._on_search_changed)
    self._tree_view.clicked.connect(self._on_tree_clicked)

  def load_compile_command_json(self, file_path : Path):
    logger.debug(f"load compile_command.json {file_path}")
    ast_parser = AstParser(file_path)
    tu_infos = ast_parser.GetTuInfos()
    self._load_transition_unit(tu_infos)

  @staticmethod
  def _create_filter_proxy_model(source_model):
    proxy_model = QSortFilterProxyModel()
    proxy_model.setSourceModel(source_model)
    proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    proxy_model.setRecursiveFilteringEnabled(True)
    return proxy_model

  def _on_search_changed(self, text):
    self._proxy_model.setFilterFixedString(text)
    if text.strip():
      self._tree_view.expandAll()
    else:
      self._tree_view.expandToDepth(0)

  def _on_tree_clicked(self, proxy_index):
    source_index = self._proxy_model.mapToSource(proxy_index)
    item = self._model.itemFromIndex(source_index)
    path = item.data(Qt.ItemDataRole.UserRole)
    tu = item.data(self.TU_ROLE)
    if path:
      self.file_selected.emit(tu, path)
    else:
      current_expend_status = self._tree_view.isExpanded(proxy_index)
      self._tree_view.setExpanded(proxy_index, not current_expend_status)

  def _load_transition_unit(self, tu_infos):
    common_path = self._get_tu_common_path(tu_infos)
    root_item = QStandardItem(str(common_path))
    self._model.clear()
    self._model.appendRow(root_item)
    for tu_info in tu_infos:
      self._add_path(root_item, common_path, tu_info)
    self._tree_view.expandToDepth(0)

  def _get_tu_common_path(self, tu_infos : list[AstTuInfo]):
    source_parent_paths = [tu_info.source.parent for tu_info in tu_infos]
    common_path = Path(os.path.commonpath(source_parent_paths))
    return common_path

  def _add_path(self, parent_item, common_path, tu_info : AstTuInfo):
    current = parent_item
    relative_path = tu_info.source.relative_to(common_path)
    for part in relative_path.parts:
      child = self._find_or_create_child(current, part)
      current = child
    current.setText(f"tu:{relative_path.parts[-1]}")

    source_item = QStandardItem(str(tu_info.source))
    source_item.setData(tu_info.source, self.FILE_PATH_ROLE)
    source_item.setData(tu_info.tu, self.TU_ROLE)
    current.appendRow(source_item)
    for include in tu_info.includes:
      include_item = QStandardItem(str(include))
      include_item.setData(include, self.FILE_PATH_ROLE)
      include_item.setData(tu_info.tu, self.TU_ROLE)
      current.appendRow(include_item)
    # current.setData(str(full_path), Qt.ItemDataRole.UserRole)

  def _find_or_create_child(self, parent, child_name):
    for row in range(parent.rowCount()):
      child = parent.child(row)
      if child.text() == child_name:
        return child
    child = QStandardItem(child_name)
    parent.appendRow(child)
    return child

