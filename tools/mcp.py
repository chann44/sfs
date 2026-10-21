import json
import sys
from dataclasses import asdict

from core.agent import AgentFilesystem
from tools.schema import TOOL_SPECS

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "sfs", "version": "0.1.0"}
TOOLS = [
	{"name": spec["name"], "description": spec["description"], "inputSchema": spec["parameters"]}
	for spec in TOOL_SPECS
]
TOOL_NAMES = {spec["name"] for spec in TOOL_SPECS}


class McpServer:
	def __init__(self, afs: AgentFilesystem, stdin=None, stdout=None):
		self.afs = afs
		self.stdin = stdin or sys.stdin
		self.stdout = stdout or sys.stdout

	def serve(self):
		for line in self.stdin:
			if not line.strip():
				continue
			try:
				message = json.loads(line)
			except json.JSONDecodeError as e:
				self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {e}"}})
				continue
			if not isinstance(message, dict):
				self._write({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "message must be an object"}})
				continue
			response = self.handle(message)
			if response is not None:
				self._write(response)

	def handle(self, message):
		method = message.get("method")
		if method is None or method.startswith("notifications/"):
			return None
		outcome = self._dispatch(method, message.get("params") or {})
		if "error" in outcome:
			return {"jsonrpc": "2.0", "id": message.get("id"), "error": outcome["error"]}
		return {"jsonrpc": "2.0", "id": message.get("id"), "result": outcome["result"]}

	def _dispatch(self, method, params):
		if method == "initialize":
			return {"result": {
				"protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
				"capabilities": {"tools": {}},
				"serverInfo": SERVER_INFO,
			}}
		if method == "ping":
			return {"result": {}}
		if method == "tools/list":
			return {"result": {"tools": TOOLS}}
		if method == "tools/call":
			return self._call(params)
		return {"error": {"code": -32601, "message": f"method not found: {method}"}}

	def _call(self, params):
		name = params.get("name")
		arguments = params.get("arguments") or {}
		if name not in TOOL_NAMES:
			return {"error": {"code": -32602, "message": f"unknown tool: {name}"}}
		if not isinstance(arguments, dict):
			return {"error": {"code": -32602, "message": "arguments must be an object"}}
		payload = asdict(self.afs.dispatch(name, **arguments))
		return {"result": {
			"content": [{"type": "text", "text": json.dumps(payload)}],
			"isError": payload.get("error") is not None,
		}}

	def _write(self, message):
		self.stdout.write(json.dumps(message) + "\n")
		self.stdout.flush()


def serve(afs: AgentFilesystem):
	McpServer(afs).serve()
