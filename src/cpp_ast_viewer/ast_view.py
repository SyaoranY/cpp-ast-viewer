import logging
from dataclasses import dataclass
from enum import Enum, auto

from clang.cindex import Cursor, TranslationUnit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QSplitter, QTreeView, QVBoxLayout, QWidget

from cpp_ast_viewer.ast_details_view import AstDetailsView

logger = logging.getLogger(__name__)


class ItemType(Enum):
    LEAF = auto()
    EXPANDED = auto()
    UNEXPANDED = auto()


@dataclass(slots=True)
class CursorData:
    cursor: Cursor
    type: ItemType


class AstTreeView(QTreeView):
    cursor_selected = Signal(Cursor)

    def __init__(self):
        super().__init__()
        self.setEditTriggers(self.EditTrigger.NoEditTriggers)
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(["AST"])
        self.setModel(self._model)
        self.clicked.connect(self._on_clicked)
        self.expanded.connect(self._on_expanded)

        self._parent_dict_cache: dict[TranslationUnit, dict[Cursor, Cursor]] = {}

    def reset_all(self):
        self._parent_dict_cache = {}
        self._model.removeRows(0, self._model.rowCount())

    def reset_view(self):
        self._model.removeRows(0, self._model.rowCount())

    def _set_tu(self, tu):
        parent_dict = self._parent_dict_cache.get(tu)
        if parent_dict is None:
            self._parent_dict_cache[tu] = self._build_parent_dict(tu)

    def _build_parent_dict(self, tu) -> dict[Cursor, Cursor]:
        parent_dict: dict[Cursor, Cursor] = {}
        root = tu.cursor  # root cursor not included in parent_dict
        visited: set[Cursor] = {root}

        def visit(parent: Cursor):
            for child in parent.get_children():
                if child in visited:
                    continue
                visited.add(child)
                parent_dict[child] = parent
                visit(child)

        visit(root)
        return parent_dict

    def show_ast(self, tu):
        self._set_tu(tu)
        self.reset_view()
        root = self._model.invisibleRootItem()
        root.setData(tu)
        self._add_cursor(tu.cursor, root)

    def _add_cursor(self, cursor: Cursor, parent_item):
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
        item = self._model.itemFromIndex(index)
        cursor = item.data().cursor
        if cursor is not None:
            self.cursor_selected.emit(cursor)

    def _on_expanded(self, index):
        item = self._model.itemFromIndex(index)
        self._load_children(item)

    # lazy load
    def _load_children(self, item):
        cursor_data: CursorData = item.data()
        if cursor_data.type == ItemType.UNEXPANDED:
            item.removeRows(0, item.rowCount())
            for child in cursor_data.cursor.get_children():
                self._add_cursor(child, item)
            cursor_data.type = ItemType.EXPANDED

    def select_at(self, path, line, column):
        cursor = self._get_cursor_at(path, line, column)
        cursor_path = self._get_cursor_path(cursor)
        parent = self._model.invisibleRootItem().child(0)
        for cursor_part in cursor_path:
            child = self._load_children_at(cursor_part, parent)
            parent = child
        self._expand_parents(parent.index())
        self.setCurrentIndex(parent.index())
        self.scrollTo(parent.index())
        return cursor

    def _get_cursor_path(self, cursor: Cursor) -> list[Cursor]:
        cursor_path = []
        current = cursor
        tu = self._model.invisibleRootItem().data()
        while current in self._parent_dict_cache[tu]:
            cursor_path.append(current)
            current = self._parent_dict_cache[tu][current]
        cursor_path.reverse()
        return cursor_path

    def _load_children_at(self, cursor, parent):
        self._load_children(parent)  # lazy load item
        for row in range(parent.rowCount()):
            if parent.child(row).data().cursor == cursor:
                return parent.child(row)
        raise ValueError("not find child")

    def _get_cursor_at(self, path, line, column) -> Cursor:
        tu = self._model.invisibleRootItem().data()
        location = tu.get_location(str(path), (line, column))
        cursor = Cursor.from_location(tu, location)
        return cursor

    def _expand_parents(self, index):
        parent = index.parent()
        while parent.isValid():
            self.expand(parent)
            parent = parent.parent()


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

    def reset_all(self):
        self.ast_tree_view.reset_all()
        self.ast_details_view.reset_all()

    def show_ast(self, tu):
        self.ast_tree_view.show_ast(tu)
        self.ast_details_view.reset_all()

    def select_at(self, path, line, column):
        cursor = self.ast_tree_view.select_at(path, line, column)
        if cursor is not None:
            self.ast_details_view.show_cursor(cursor)
        return cursor

    def _on_cursor_selected(self, cursor: Cursor):
        self.ast_details_view.show_cursor(cursor)
        self.cursor_selected.emit(cursor)
