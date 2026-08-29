from clang import cindex
from pathlib import Path
from cpp_ast_viewer.compile_command import CompileCommands

class AstParser:
  def __init__(self, compile_commands_json_path):
    self.compile_commands = CompileCommands(compile_commands_json_path).compile_commands
    self.index = cindex.Index.create()

  def GetTuInfos(self):
    result = {}
    for source, compile_options in self.compile_commands.items():
      tu = self.index.parse(source, args=compile_options)
      includes = [str(Path(include.include.name).resolve()) for include in tu.get_includes()]
      result[source] = {}
      result[source]['tu'] = tu
      result[source]['includes'] = sorted(set(includes))
    return result

  def GetCompileOptions(self):
    pass
  # def GetTuPaths(self):
  #   compile_command_lists = self.compile_commands.compile_commands
  #   {
  #     "source_path" : "compile_options"
  #   }
  #   [{"source":"path", "includes": ["include1","include2"]}]