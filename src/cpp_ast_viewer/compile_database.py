import json
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CompileArguments:
    source: Path
    args: list[str]


class CompileDatabase:
    def __init__(self, compile_commands_json_path: Path):
        self._compilation_database = self._init_compilation_database(compile_commands_json_path)
        self._compilation_arguments = CompileDatabase._normalize(self._compilation_database)

    @property
    def arguments(self) -> list[CompileArguments]:
        return self._compilation_arguments

    def _init_compilation_database(self, compilation_db_path: Path):
        with open(compilation_db_path, "r") as fp:
            return json.load(fp)

    @staticmethod
    def _normalize(compilation_database):
        return [
            CompileDatabase._normalize_relative_path(compilation_db_item)
            for compilation_db_item in compilation_database
        ]

    @staticmethod
    def _normalize_relative_path(compilation_db_item):
        working_dir = Path(compilation_db_item["directory"])
        normalized_source_path = (working_dir / compilation_db_item["file"]).resolve()
        normalized_arguments = CompileDatabase._normalize_arguments(compilation_db_item)
        logger.debug(f"{normalized_source_path} {normalized_arguments}")
        return CompileArguments(source=normalized_source_path, args=normalized_arguments)

    @staticmethod
    def _normalize_arguments(compilation_db_item):
        if "arguments" in compilation_db_item:
            arguments = compilation_db_item["arguments"][1:]
        elif "command" in compilation_db_item:
            arguments = shlex.split(compilation_db_item["command"])[1:]
        else:
            raise ValueError("Invalid compile_commands.json: missing 'arguments' or 'command'")

        working_dir = Path(compilation_db_item["directory"])

        result = []
        i = 0
        while i < len(arguments):
            if arguments[i] == "-o" or arguments[i] == "-c":
                i += 1
            elif arguments[i].startswith("-I"):
                include_path = arguments[i][2:]
                normalized_include = str((working_dir / include_path).resolve())
                result.append("-I" + normalized_include)
            else:
                result.append(arguments[i])
            i += 1
        return result
