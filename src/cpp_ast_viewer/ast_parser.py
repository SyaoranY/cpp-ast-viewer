import logging
from dataclasses import dataclass
from pathlib import Path

from clang import cindex

from cpp_ast_viewer.compile_database import CompileDatabase

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AstTuInfo:
    source: Path
    tu: cindex.TranslationUnit
    includes: list[Path]


class AstParser:
    def __init__(self, compile_commands_json: Path):
        self._index = cindex.Index.create()
        self._compile_database = CompileDatabase(compile_commands_json)

    def get_tu_infos(self) -> list[AstTuInfo]:
        result = []
        for item in self._compile_database.arguments:
            logger.info("Parsing TU: %s", item.source)
            tu = self._index.parse(str(item.source), args=item.args)
            self._print_tu_diagnostics(tu)
            includes = [Path(include.include.name).resolve() for include in tu.get_includes()]
            includes = list(set(includes))
            includes.sort(key=lambda header: self._header_sort_key(item.source, header))
            result.append(AstTuInfo(source=item.source, tu=tu, includes=includes))
        return result

    def _print_tu_diagnostics(self, tu: cindex.TranslationUnit):
        for diagnostic in tu.diagnostics:
            if diagnostic.severity == diagnostic.Fatal:
                logger.fatal("%s", diagnostic)
            elif diagnostic.severity == diagnostic.Error:
                logger.error("%s", diagnostic)
            elif diagnostic.severity == diagnostic.Warning:
                logger.warning("%s", diagnostic)
            else:
                logger.info("%s", diagnostic)

    def _header_sort_key(self, source_path: Path, header_path: Path):
        common = self._common_path_length(source_path.parent, header_path.parent)
        remaining = header_path.parts[common:]
        build_priority = 1 if "build" in remaining else 0
        return (-common, build_priority, header_path)

    def _common_path_length(self, a: Path, b: Path) -> int:
        a_parts = a.resolve().parts
        b_parts = b.resolve().parts
        common = 0
        for x, y in zip(a_parts, b_parts):
            if x != y:
                break
            common += 1
        return common
