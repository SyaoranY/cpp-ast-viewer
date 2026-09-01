import logging
from clang import cindex
from pathlib import Path
from dataclasses import dataclass
from cpp_ast_viewer.compile_database import CompileDatabase

logger = logging.getLogger(__name__)

@dataclass
class AstTuInfo:
  source : Path
  tu : cindex.TranslationUnit
  includes : list[Path]


class AstParser:
  def __init__(self, compile_commands_json : Path):
    self.index = cindex.Index.create()
    self.compile_database = CompileDatabase(compile_commands_json)

  def GetTuInfos(self) -> list[AstTuInfo]:
    result = []
    for item in self.compile_database.arguments:
      tu = self.index.parse(str(item.source), args=item.args)
      includes = [Path(include.include.name).resolve() for include in tu.get_includes()]
      includes = sorted(set(includes))
      result.append(AstTuInfo(source=item.source, tu=tu, includes=includes))
    return result
