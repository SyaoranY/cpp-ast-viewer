from clang.cindex import Cursor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class AstDetailsView(QTreeWidget):
    def __init__(self):
        super().__init__()

        self.setColumnCount(2)
        self.setHeaderLabels(["Property", "Value"])

        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setUniformRowHeights(False)

        self.header().setStretchLastSection(True)

        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)

    # ============================================================
    # Public interface
    # ============================================================

    def reset_all(self):
        self.clear()

    def show_cursor(self, cursor: Cursor):
        self.clear()

        self._add_basic_group(cursor)
        self._add_type_group(cursor)
        self._add_source_group(cursor)
        self._add_relation_group(cursor)
        self._add_declaration_group(cursor)
        self._add_cpp_group(cursor)
        self._add_argument_group(cursor)
        self._add_token_group(cursor)

        self.expandAll()

        self.resizeColumnToContents(0)

    # ============================================================
    # Basic
    # ============================================================

    def _add_basic_group(self, cursor: Cursor):
        group = self._create_group("Basic")

        self._add_property(group, "Kind", self._safe(lambda: cursor.kind.name))
        self._add_property(group, "Spelling", cursor.spelling or "-")
        self._add_property(group, "Display name", cursor.displayname or "-")
        self._add_property(group, "Hash", self._safe(lambda: cursor.hash))
        self._add_property(group, "USR", self._safe(cursor.get_usr))
        self._add_property(group, "Mangled name", self._safe(lambda: cursor.mangled_name))

    # ============================================================
    # Type
    # ============================================================

    def _add_type_group(self, cursor: Cursor):
        group = self._create_group("Type")

        self._add_property(group, "Type", self._safe(lambda: cursor.type.spelling))
        self._add_property(group, "Canonical type", self._safe(lambda: cursor.type.get_canonical().spelling))
        self._add_property(group, "Result type", self._safe(lambda: cursor.result_type.spelling))
        self._add_property(
            group, "Underlying typedef type", self._safe(lambda: cursor.underlying_typedef_type.spelling)
        )
        self._add_property(group, "Enum type", self._safe(lambda: cursor.enum_type.spelling))
        self._add_property(group, "Enum value", self._safe(lambda: cursor.enum_value))

    # ============================================================
    # Source
    # ============================================================

    def _add_source_group(self, cursor: Cursor):
        group = self._create_group("Source")

        location = cursor.location
        file_name = location.file.name if location.file is not None else "-"

        self._add_property(group, "File", file_name)
        self._add_property(group, "Line", location.line)
        self._add_property(group, "Column", location.column)
        self._add_property(group, "Offset", location.offset)

        extent = cursor.extent

        extent_group = QTreeWidgetItem(group, ["Extent", ""])

        self._add_property(extent_group, "Start", self._format_location(extent.start))
        self._add_property(extent_group, "End", self._format_location(extent.end))

    # ============================================================
    # Relations
    # ============================================================

    def _add_relation_group(self, cursor: Cursor):
        group = self._create_group("Relations")

        self._add_cursor_property(group, "Semantic parent", self._safe_value(lambda: cursor.semantic_parent))
        self._add_cursor_property(group, "Lexical parent", self._safe_value(lambda: cursor.lexical_parent))
        self._add_cursor_property(group, "Referenced", self._safe_value(lambda: cursor.referenced))
        self._add_cursor_property(group, "Canonical", self._safe_value(lambda: cursor.canonical))
        self._add_cursor_property(group, "Definition", self._safe_value(cursor.get_definition))

    # ============================================================
    # Declaration
    # ============================================================

    def _add_declaration_group(self, cursor: Cursor):
        group = self._create_group("Declaration")

        self._add_property(group, "Is definition", self._safe(cursor.is_definition))
        self._add_property(group, "Access", self._safe(lambda: cursor.access_specifier.name))
        self._add_property(group, "Storage class", self._safe(lambda: cursor.storage_class.name))
        self._add_property(group, "Linkage", self._safe(lambda: cursor.linkage.name))
        self._add_property(group, "Availability", self._safe(lambda: cursor.availability.name))

    # ============================================================
    # C++
    # ============================================================

    def _add_cpp_group(self, cursor: Cursor):
        group = self._create_group("C++")

        checks = [
            ("Static method", "is_static_method"),
            ("Const method", "is_const_method"),
            ("Virtual method", "is_virtual_method"),
            ("Pure virtual method", "is_pure_virtual_method"),
            ("Abstract record", "is_abstract_record"),
            ("Default method", "is_default_method"),
            ("Deleted method", "is_deleted_method"),
            ("Copy constructor", "is_copy_constructor"),
            ("Move constructor", "is_move_constructor"),
            ("Converting constructor", "is_converting_constructor"),
            ("Default constructor", "is_default_constructor"),
            ("Mutable field", "is_mutable_field"),
            ("Scoped enum", "is_scoped_enum"),
        ]

        for display_name, method_name in checks:
            self._add_property(group, display_name, self._call_optional_method(cursor, method_name))

        self._add_property(
            group, "Exception specification", self._safe(lambda: cursor.exception_specification_kind.name)
        )

    # ============================================================
    # Arguments
    # ============================================================

    def _add_argument_group(self, cursor: Cursor):
        group = self._create_group("Arguments")

        try:
            arguments = list(cursor.get_arguments())
        except Exception:
            arguments = []

        if not arguments:
            self._add_property(group, "Arguments", "-")
            return

        for index, argument in enumerate(arguments):
            arg_item = QTreeWidgetItem(group, [f"Argument {index}", argument.spelling or ""])
            self._add_property(arg_item, "Kind", self._safe(lambda arg=argument: arg.kind.name))
            self._add_property(arg_item, "Spelling", argument.spelling or "-")
            self._add_property(arg_item, "Type", self._safe(lambda arg=argument: arg.type.spelling))
            self._add_property(
                arg_item, "Location", self._safe(lambda arg=argument: self._format_location(arg.location))
            )

    # ============================================================
    # Tokens
    # ============================================================

    def _add_token_group(self, cursor: Cursor):
        group = self._create_group("Tokens")

        try:
            tokens = list(cursor.get_tokens())
        except Exception:
            tokens = []

        if not tokens:
            self._add_property(group, "Tokens", "-")
            return

        self._add_property(group, "Count", len(tokens))
        token_text = " ".join(token.spelling for token in tokens)
        self._add_property(group, "Text", token_text)

        for index, token in enumerate(tokens):
            token_item = QTreeWidgetItem(group, [f"Token {index}", token.spelling])
            self._add_property(token_item, "Kind", self._safe(lambda tok=token: tok.kind.name))
            self._add_property(
                token_item, "Location", self._safe(lambda tok=token: self._format_location(tok.location))
            )

    # ============================================================
    # Tree helpers
    # ============================================================

    def _create_group(self, name: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self, [name, ""])

        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

        return item

    def _add_property(self, parent: QTreeWidgetItem, name: str, value) -> QTreeWidgetItem:
        text = "-" if value is None else str(value)
        item = QTreeWidgetItem(parent, [name, text])
        item.setToolTip(1, text)
        return item

    def _add_cursor_property(self, parent: QTreeWidgetItem, name: str, cursor):
        if cursor is None:
            self._add_property(parent, name, "-")
            return

        item = QTreeWidgetItem(parent, [name, self._cursor_summary(cursor)])

        self._add_property(item, "Kind", self._safe(lambda: cursor.kind.name))
        self._add_property(item, "Spelling", cursor.spelling or "-")
        self._add_property(item, "Display name", cursor.displayname or "-")
        self._add_property(item, "Location", self._safe(lambda: self._format_location(cursor.location)))

    # ============================================================
    # Formatting helpers
    # ============================================================

    def _cursor_summary(self, cursor: Cursor) -> str:
        try:
            kind = cursor.kind.name
        except Exception:
            kind = "UNKNOWN"

        spelling = cursor.spelling or ""

        if spelling:
            return f"{kind}  {spelling}"

        return kind

    def _format_location(self, location) -> str:
        if location is None:
            return "-"

        if location.file is None:
            return f"{location.line}:{location.column}"
        else:
            return f"{location.file.name}:{location.line}:{location.column}"

    # ============================================================
    # Safe access helpers
    # ============================================================

    def _safe(self, func):
        try:
            value = func()
            if value is None:
                return "-"
            text = str(value)
            return text if text else "-"
        except Exception:
            return "-"

    def _safe_value(self, func):
        try:
            return func()
        except Exception:
            return None

    def _call_optional_method(self, cursor: Cursor, method_name: str):
        try:
            method = getattr(cursor, method_name, None)
            return method() if method is not None else "-"
        except Exception:
            return "-"
