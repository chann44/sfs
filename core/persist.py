import json
import os

from core.setup import Filesystem

WAL_OPS = {"mkdir", "mkdirs", "touch", "write", "delete"}


class Wal:
	def __init__(self, wal_path):
		self.wal_path = wal_path
		self.replaying = False

	def record(self, op, **args):
		if self.replaying:
			return
		with open(self.wal_path, "a", encoding="utf-8") as wal:
			wal.write(json.dumps({"op": op, "args": args}) + "\n")

	def load(self, fs: Filesystem):
		if not os.path.exists(self.wal_path):
			return fs
		self.replaying = True
		try:
			with open(self.wal_path, encoding="utf-8") as wal:
				chunks = wal.read().split("\n")
			torn = chunks.pop()
			lines = chunks if torn == "" else chunks + [torn]
			for number, line in enumerate(lines, 1):
				if not line.strip():
					continue
				try:
					record = json.loads(line)
					op, args = record["op"], record["args"]
				except (json.JSONDecodeError, KeyError) as e:
					if number == len(lines) and torn != "":
						continue
					raise ValueError(f"corrupt wal record at line {number}: {e}") from e
				if op == "snapshot":
					fs.root_name = args["root_name"]
					fs.max_file_bytes = args["max_file_bytes"]
					fs.max_total_bytes = args["max_total_bytes"]
					fs.paths = args["paths"]
					fs.contents = {p: c.encode() for p, c in args["contents"].items()}
					fs.cwd = f"/{fs.root_name}"
				elif op == "config":
					fs.root_name = args["root_name"]
					fs.max_file_bytes = args["max_file_bytes"]
					fs.max_total_bytes = args["max_total_bytes"]
					fs.paths = {fs.root_name: {}}
					fs.contents = {}
					fs.cwd = f"/{fs.root_name}"
				elif op in WAL_OPS:
					getattr(fs, op)(**args)
				else:
					raise ValueError(f"unknown wal op at line {number}: {op}")
		finally:
			self.replaying = False
		return fs

	def write_config(self, fs: Filesystem):
		with open(self.wal_path, "w", encoding="utf-8") as wal:
			wal.write(json.dumps({
				"op": "config",
				"args": {
					"root_name": fs.root_name,
					"max_file_bytes": fs.max_file_bytes,
					"max_total_bytes": fs.max_total_bytes,
				},
			}) + "\n")
		return self

	def save(self):
		if not os.path.exists(self.wal_path):
			open(self.wal_path, "a", encoding="utf-8").close()
		return self

	def compact(self, fs: Filesystem):
		snapshot = {
			"op": "snapshot",
			"args": {
				"root_name": fs.root_name,
				"max_file_bytes": fs.max_file_bytes,
				"max_total_bytes": fs.max_total_bytes,
				"paths": fs.paths,
				"contents": {p: c.decode() for p, c in fs.contents.items()},
			},
		}
		tmp = f"{self.wal_path}.tmp"
		with open(tmp, "w", encoding="utf-8") as wal:
			wal.write(json.dumps(snapshot) + "\n")
		os.replace(tmp, self.wal_path)
		return self


def attach(fs: Filesystem, wal_path: str):
	wal = Wal(wal_path)
	fs.journal = wal
	return wal
