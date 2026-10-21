import json
from dataclasses import asdict

from core.agent import AgentFilesystem
from tools.schema import TOOL_SPECS


def _json(result):
	return json.dumps(asdict(result))


def _functions(afs: AgentFilesystem):
	def ls(path: str = "/") -> str:
		return _json(afs.ls(path=path))

	def read(file_path: str, offset: int = 0, limit: int = 2000) -> str:
		return _json(afs.read(file_path, offset=offset, limit=limit))

	def write(file_path: str, content: str) -> str:
		return _json(afs.write(file_path, content))

	def edit(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
		return _json(afs.edit(file_path, old_string, new_string, replace_all=replace_all))

	def glob(pattern: str, path: str = "/") -> str:
		return _json(afs.glob(pattern, path=path))

	def grep(pattern: str, path: str = "/", glob: str = None) -> str:
		return _json(afs.grep(pattern, path=path, glob=glob))

	def delete(file_path: str) -> str:
		return _json(afs.delete(file_path))

	return {"ls": ls, "read": read, "write": write, "edit": edit, "glob": glob, "grep": grep, "delete": delete}


def to_langchain(afs: AgentFilesystem):
	try:
		from langchain_core.tools import StructuredTool
	except ImportError as e:
		raise ImportError("langchain-core is not installed: pip install langchain-core") from e

	functions = _functions(afs)
	return [
		StructuredTool.from_function(func=functions[spec["name"]], name=spec["name"], description=spec["description"])
		for spec in TOOL_SPECS
	]
