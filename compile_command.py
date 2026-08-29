import json
import logging

logger = logging.getLogger(__name__)

class CompileCommands:
  def __init__(self, compile_commands_json_path):
    self.__compile_commands = {}
    logger.debug(f"open compile_command.json: {compile_commands_json_path}")
    with open(compile_commands_json_path, 'r') as fp:
      compile_commands_json = json.load(fp)
      for compile_command_item in compile_commands_json:
        file_path = compile_command_item['file']
        compile_options = self.get_compile_options(compile_command_item['command'])
        self.__compile_commands[file_path] = compile_options
        logger.debug(f"{file_path} {compile_options}")

  @property
  def compile_commands(self):
    return self.__compile_commands

  @staticmethod
  def get_compile_options(command):
    command_list = command.split()
    command_list = command_list[1:]
    result = []
    i = 0
    while i < len(command_list):
      if command_list[i] == '-o' or command_list[i] == '-c':
        i += 1
      else:
        result.append(command_list[i])
      i += 1
    return result
