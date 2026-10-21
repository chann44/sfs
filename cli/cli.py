import argparse
import json
import os
import shlex

from core.persist import Wal
from core.setup import DIR_EMOJI, FILE_EMOJI, Filesystem
from tools.openai import to_openai


## commands
# init it's intialize with a user and permissions and a fiele system root
# filesystem:
#	read
# 	write
# 	list

# OPS
# mkdir 
# cat
# create file
# create nested dir and files

## without any params it s shows the file system

class Cli:
	def __init__(self, filesystem=None):
		self.fs = filesystem or Filesystem()
		self.user = None
		self.permissions = "rw"
		self.parser = self._build_parser()

	def run(self, argv=None):
		args = self.parser.parse_args(argv)
		if args.command != "init" and os.path.exists(args.wal):
			wal = Wal(args.wal)
			self.fs = Filesystem(journal=wal)
			wal.load(self.fs)
		if args.command is None:
			self.show_tree()
			print("sfs: no command given, try 'shell' or -h")
			return 0
		if args.command == "shell":
			return self.shell()
		try:
			self.execute(args)
		except (OSError, ValueError) as e:
			print(f"sfs: {e}")
			return 1
		return 0

	def shell(self):
		self.show_tree()
		while True:
			try:
				line = input(self._prompt())
			except (EOFError, KeyboardInterrupt):
				print()
				return 0
			parts = shlex.split(line)
			if not parts:
				continue
			if parts[0] in ("exit", "quit"):
				return 0
			if parts[0] == "cd":
				self.cd(parts[1] if len(parts) > 1 else self._home())
				continue
			try:
				args = self.parser.parse_args(parts)
				self.execute(args)
			except SystemExit:
				pass
			except (OSError, ValueError) as e:
				print(f"sfs: {e}")

	def cd(self, path):
		try:
			self.fs.cd(path)
		except (OSError, ValueError) as e:
			print(f"sfs: {e}")

	def _init_fs(self, args):
		self.user = args.user
		self.permissions = args.permissions
		self.fs = Filesystem(
			root_name=args.root,
			max_file_bytes=args.file_cap,
			max_total_bytes=args.total_cap,
		)
		wal = Wal(args.wal)
		wal.write_config(self.fs)
		self.fs.journal = wal
		self.fs.mkdirs(f"home/{args.user}")
		self.fs.mkdir("usr")
		self.fs.touch(f"home/{args.user}/readme.txt", f"welcome {args.user}\n".encode())
		print(f"initialized /{args.root} for {args.user} (permissions: {self.permissions}, wal: {args.wal})")
		self.show_tree()

	def execute(self, args):
		if args.command == "init":
			self._init_fs(args)
		elif args.command == "ls":
			self._check("r")
			base = self.fs.resolve(args.path)
			for name in self.fs.ls(args.path):
				marker = DIR_EMOJI if self.fs.is_dir(f"{base}/{name}") else FILE_EMOJI
				print(f"{marker} {name}")
		elif args.command == "mkdir":
			self._check("w")
			if args.parents:
				self.fs.mkdirs(args.path)
			else:
				self.fs.mkdir(args.path)
		elif args.command == "touch":
			self._check("w")
			self.fs.touch(args.path)
		elif args.command == "cat":
			self._check("r")
			print(self.fs.read(args.path).decode(errors="replace"))
		elif args.command == "write":
			self._check("w")
			self.fs.write(args.path, args.content, parents=args.parents)
		elif args.command == "pwd":
			print(self.fs.pwd())
		elif args.command == "tree":
			self._check("r")
			self.show_tree()
		elif args.command == "tools":
			print(json.dumps(to_openai(), indent=2))

	def show_tree(self, structure=None, indent=0):
		if structure is None:
			structure = self.fs.paths
		for key, value in structure.items():
			if isinstance(value, dict):
				print(f"{' ' * indent}{DIR_EMOJI} {key}")
				self.show_tree(value, indent + 2)
			else:
				print(f"{' ' * indent}{FILE_EMOJI} {key}")

	def _build_parser(self):
		parser = argparse.ArgumentParser(prog="sfs", description="sfs - tiny fake filesystem")
		parser.add_argument("--wal", default="sfs.wal", help="write-ahead log path")
		sub = parser.add_subparsers(dest="command")
		init = sub.add_parser("init", help="initialize with a user, permissions and a root")
		init.add_argument("user")
		init.add_argument("--permissions", default="rw")
		init.add_argument("--root", default="root")
		init.add_argument("--file-cap", type=int, default=4096, help="max bytes per file")
		init.add_argument("--total-cap", type=int, default=1048576, help="max bytes across all files")
		ls = sub.add_parser("ls", help="list a directory")
		ls.add_argument("path", nargs="?", default=None)
		mkdir = sub.add_parser("mkdir", help="create a directory")
		mkdir.add_argument("path")
		mkdir.add_argument("-p", "--parents", action="store_true")
		touch = sub.add_parser("touch", help="create a file")
		touch.add_argument("path")
		cat = sub.add_parser("cat", help="read a file")
		cat.add_argument("path")
		write = sub.add_parser("write", help="write content to a file")
		write.add_argument("path")
		write.add_argument("content", nargs="?", default="")
		write.add_argument("-p", "--parents", action="store_true")
		sub.add_parser("pwd", help="print working directory")
		sub.add_parser("tree", help="show the whole filesystem")
		sub.add_parser("tools", help="print agent tool definitions as JSON")
		sub.add_parser("shell", help="interactive shell")
		return parser

	def _prompt(self):
		return f"{self.user or 'guest'}:{self.fs.pwd()}> "

	def _home(self):
		return f"/home/{self.user}" if self.user else "/"

	def _check(self, mode):
		if mode not in self.permissions:
			raise PermissionError(f"permission denied (need '{mode}')")


if __name__ == "__main__":
	cli = Cli()
	cli.run()
