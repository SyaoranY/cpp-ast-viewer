import logging
import os
from enum import Enum, auto
from pathlib import Path

from clang.cindex import TranslationUnit
from PySide6.QtCore import QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QLineEdit, QTreeView, QVBoxLayout, QWidget

from cpp_ast_viewer.ast_parser import AstParser, AstTuInfo

logger = logging.getLogger(__name__)


class NodeType(Enum):
    DIR = auto()
    TU = auto()
    FILE = auto()


class ModelItemData:
    def __init__(self, item_type: NodeType, item_data=None):
        self._item_type = item_type
        self._data = item_data

    def is_dir_item(self) -> bool:
        return self._item_type == NodeType.DIR

    def is_tu_item(self) -> bool:
        return self._item_type == NodeType.TU

    def is_file_item(self) -> bool:
        return self._item_type == NodeType.FILE

    def get_tu_info(self) -> AstTuInfo:
        return self._data

    def get_file_path(self) -> Path:
        return self._data


class FilePanel(QWidget):
    tu_selected = Signal(TranslationUnit)
    file_selected = Signal(TranslationUnit, Path)

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

        self._selected_tu_item: QStandardItem = None

    def select_file(self, file_path: Path):
        if self._selected_tu_item is None:
            raise ValueError("logic error")
        file_item = self._find_file_item(self._selected_tu_item, file_path)
        self._search_edit.clear()
        proxy_index = self._proxy_model.mapFromSource(file_item.index())
        self._expand_parents(proxy_index)
        self._tree_view.setCurrentIndex(proxy_index)
        self._tree_view.scrollTo(proxy_index)

    def _find_file_item(self, tu_item, file_path):
        for row in range(tu_item.rowCount()):
            file_item = tu_item.child(row)
            if file_item.data().get_file_path() == file_path:
                return file_item
        raise ValueError("file item not found")

    def _expand_parents(self, index):
        parent = index.parent()
        while parent.isValid():
            self._tree_view.expand(parent)
            parent = parent.parent()

    def load_compile_command_json(self, file_path: Path):
        logger.debug(f"load compile_command.json {file_path}")
        ast_parser = AstParser(file_path)
        tu_infos = ast_parser.get_tu_infos()
        self._load_transition_units(tu_infos)

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
        data: ModelItemData = item.data()
        if data.is_dir_item():
            # expand next level or collapse
            current_expend_status = self._tree_view.isExpanded(proxy_index)
            self._tree_view.setExpanded(proxy_index, not current_expend_status)
        elif data.is_tu_item():
            self._selected_tu_item = item
            # expand file path
            current_expend_status = self._tree_view.isExpanded(proxy_index)
            self._tree_view.setExpanded(proxy_index, not current_expend_status)
            # show ast
            self.tu_selected.emit(data.get_tu_info().tu)
        elif data.is_file_item():
            self._selected_tu_item = item.parent()
            # show source file and ast
            tu_info: AstTuInfo = item.parent().data().get_tu_info()
            self.tu_selected.emit(tu_info.tu)
            self.file_selected.emit(tu_info.tu, data.get_file_path())
        else:
            raise ValueError("invalid model item type")

    def _load_transition_units(self, tu_infos: list[AstTuInfo]):
        self._model.clear()
        common_path = self._get_tu_common_path(tu_infos)
        root_item = QStandardItem(str(common_path))
        root_item.setData(ModelItemData(NodeType.DIR))
        self._model.appendRow(root_item)
        for tu_info in tu_infos:
            self._add_path(root_item, common_path, tu_info)
        self._tree_view.expandToDepth(0)

    def _get_tu_common_path(self, tu_infos: list[AstTuInfo]):
        source_parent_paths = [tu_info.source.parent for tu_info in tu_infos]
        common_path = Path(os.path.commonpath(source_parent_paths))
        return common_path

    def _add_path(self, parent_item, common_path, tu_info: AstTuInfo):
        relative_path = tu_info.source.relative_to(common_path)
        # create directories
        for part in relative_path.parts[:-1]:
            child = self._find_or_create_child(parent_item, part)
            parent_item = child
        # create tu item
        tu_item = QStandardItem(f"tu:{relative_path.parts[-1]}")
        tu_item.setData(ModelItemData(NodeType.TU, tu_info))
        parent_item.appendRow(tu_item)
        # create source item
        source_item = QStandardItem(str(tu_info.source))
        source_item.setData(ModelItemData(NodeType.FILE, tu_info.source))
        tu_item.appendRow(source_item)
        # create include items
        for include in tu_info.includes:
            include_item = QStandardItem(str(include))
            include_item.setData(ModelItemData(NodeType.FILE, include))
            tu_item.appendRow(include_item)

    def _find_or_create_child(self, parent, child_name):
        for row in range(parent.rowCount()):
            child = parent.child(row)
            if child.text() == child_name:
                return child
        child = QStandardItem(child_name)
        child.setData(ModelItemData(NodeType.DIR))
        parent.appendRow(child)
        return child
