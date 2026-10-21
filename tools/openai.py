import json
from dataclasses import asdict

from core.agent import AgentFilesystem
from tools.schema import TOOL_SPECS


def to_openai():
	return [{"type": "function", "function": spec} for spec in TOOL_SPECS]


def execute(afs: AgentFilesystem, name: str, arguments) -> dict:
	if isinstance(arguments, str):
		try:
			arguments = json.loads(arguments)
		except json.JSONDecodeError as e:
			return {"error": f"invalid arguments json: {e}"}
	if not isinstance(arguments, dict):
		return {"error": "arguments must be an object"}
	return asdict(afs.dispatch(name, **arguments))
