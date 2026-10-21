
# so we will have a root right
# then each root will have childeren
# so each children either a file or an empty array or a __FILE__ str if 
# first we need a way to construct the path to each file and dir


FILE_IDENTIFIER= "__FILE__"
DIR_EMOJI = "📂"
FILE_EMOJI = "📃"
root = "root"

# CURSOR = "root"
# path: raw bytes

import base64
import fnmatch


class Filesystem:
    def __init__(self, root_name="root", max_file_bytes=4096, max_total_bytes=1048576, journal=None):
        self.root_name = root_name
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes
        self.journal = journal
        self.paths = {root_name: {}}
        self.contents = {}
        self.cwd = f"/{root_name}"

    @property
    def used_bytes(self):
        return sum(len(data) for data in self.contents.values())

    def pwd(self):
        return self.cwd

    def exists(self, path):
        return self._node(path) is not None

    def ls(self, path=None):
        node = self._node(path)
        if node is None:
            raise FileNotFoundError(f"no such path: {path or self.cwd}")
        if not isinstance(node, dict):
            raise NotADirectoryError(f"not a directory: {path}")
        return list(node.keys())

    def cd(self, path):
        resolved = self._resolve(path)
        node = self._node(resolved)
        if node is None:
            raise FileNotFoundError(f"no such directory: {path}")
        if not isinstance(node, dict):
            raise NotADirectoryError(f"not a directory: {path}")
        self.cwd = resolved
        return self.cwd

    def mkdir(self, path):
        resolved = self._resolve(path)
        if resolved == f"/{self.root_name}":
            raise FileExistsError(f"already exists: {path}")
        parent, name = self._split(resolved)
        node = self._node(parent)
        if node is None or not isinstance(node, dict):
            raise FileNotFoundError(f"missing parent: {path}")
        if name in node:
            raise FileExistsError(f"already exists: {path}")
        node[name] = {}
        self._record("mkdir", path=resolved)
        return resolved

    def mkdirs(self, path):
        resolved = self._resolve(path)
        node = self.paths
        for part in resolved.strip("/").split("/"):
            if part not in node:
                node[part] = {}
            elif not isinstance(node[part], dict):
                raise NotADirectoryError(f"not a directory: {part}")
            node = node[part]
        self._record("mkdirs", path=resolved)
        return resolved

    def touch(self, path, content=b""):
        if isinstance(content, str):
            content = content.encode()
        self._validate_text(content)
        resolved = self._resolve(path)
        self._check_quota(resolved, content)
        if self._node(resolved) is not None:
            raise FileExistsError(f"already exists: {path}")
        parent, name = self._split(resolved)
        node = self._node(parent)
        if node is None or not isinstance(node, dict):
            raise FileNotFoundError(f"missing parent: {path}")
        node[name] = FILE_IDENTIFIER
        self.contents[resolved] = content
        self._record("touch", path=resolved, content_b64=base64.b64encode(content).decode("ascii"))
        return resolved

    def read(self, path):
        resolved = self._resolve(path)
        node = self._node(resolved)
        if node is None:
            raise FileNotFoundError(f"no such file: {path}")
        if not isinstance(node, str):
            raise IsADirectoryError(f"is a directory: {path}")
        return self.contents.get(resolved, b"")

    def write(self, path, content=b"", parents=False):
        if isinstance(content, str):
            content = content.encode()
        self._validate_text(content)
        resolved = self._resolve(path)
        self._check_quota(resolved, content)
        node = self._node(resolved)
        if node is None:
            parent, name = self._split(resolved)
            if parents and self._node(parent) is None:
                self.mkdirs(parent)
            pnode = self._node(parent)
            if pnode is None:
                raise FileNotFoundError(f"missing parent: {path}")
            if not isinstance(pnode, dict):
                raise NotADirectoryError(f"not a directory: {path}")
            pnode[name] = FILE_IDENTIFIER
        elif not isinstance(node, str):
            raise IsADirectoryError(f"is a directory: {path}")
        self.contents[resolved] = content
        self._record("write", path=resolved, content_b64=base64.b64encode(content).decode("ascii"), parents=parents)
        return resolved

    def is_dir(self, path):
        return isinstance(self._node(path), dict)

    def is_file(self, path):
        return self._node(path) == FILE_IDENTIFIER

    def resolve(self, path=None):
        return self._resolve(path)

    def _record(self, op, **args):
        if self.journal is not None:
            self.journal.record(op, **args)

    def _validate_text(self, content):
        if b"\x00" in content:
            raise ValueError("binary content not allowed: files must be utf-8 text")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("binary content not allowed: files must be utf-8 text") from e

    def _check_quota(self, resolved, content):
        if len(content) > self.max_file_bytes:
            raise ValueError(f"file exceeds cap: {len(content)} > {self.max_file_bytes} bytes")
        projected = self.used_bytes - len(self.contents.get(resolved, b"")) + len(content)
        if projected > self.max_total_bytes:
            raise ValueError(f"total quota exceeded: {projected} > {self.max_total_bytes} bytes")

    def edit(self, path, old_string, new_string, replace_all=False):
        if not old_string:
            raise ValueError("old_string is empty")
        text = self.read(path).decode()
        count = text.count(old_string)
        if count == 0:
            raise ValueError(f"old_string not found in {path}")
        if count > 1 and not replace_all:
            raise ValueError(f"old_string matches {count} times in {path}, pass replace_all=True")
        if replace_all:
            text = text.replace(old_string, new_string)
        else:
            text = text.replace(old_string, new_string, 1)
        self.write(path, text.encode())
        return self._resolve(path)

    def delete(self, path, recursive=True):
        resolved = self._resolve(path)
        if resolved == f"/{self.root_name}":
            raise PermissionError("cannot delete root")
        node = self._node(resolved)
        if node is None:
            raise FileNotFoundError(f"no such path: {path}")
        if isinstance(node, dict) and node and not recursive:
            raise OSError(f"directory not empty: {path}")
        parent, name = self._split(resolved)
        del self._node(parent)[name]
        for key in [k for k in self.contents if k == resolved or k.startswith(resolved + "/")]:
            del self.contents[key]
        self._record("delete", path=resolved, recursive=recursive)
        return resolved

    def glob(self, pattern, path=None):
        base = self._resolve(path)
        prefix = base.strip("/")
        matches = []
        for full in self._walk(base):
            rel = full.strip("/")[len(prefix):].strip("/")
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel.rsplit("/", 1)[-1], pattern):
                matches.append(full)
        return sorted(matches)

    def grep(self, pattern, path=None, glob=None):
        base = self._resolve(path)
        matches = []
        for full in self._walk(base):
            if not self.is_file(full):
                continue
            if glob and not (fnmatch.fnmatch(full, glob) or fnmatch.fnmatch(full.rsplit("/", 1)[-1], glob)):
                continue
            for number, line in enumerate(self.read(full).decode(errors="replace").splitlines(), 1):
                if pattern in line:
                    matches.append((full, number, line))
        return sorted(matches)

    def _walk(self, base):
        node = self._node(base)
        if node is None:
            raise FileNotFoundError(f"no such path: {base}")
        if isinstance(node, str):
            yield base
            return
        stack = [(base, node)]
        while stack:
            path, current = stack.pop()
            for name, value in current.items():
                child = f"{path}/{name}"
                yield child
                if isinstance(value, dict):
                    stack.append((child, value))

    def _resolve(self, path=None):
        if path is None:
            return self.cwd
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
            if not parts or parts[0] != self.root_name:
                parts.insert(0, self.root_name)
            stack = []
        else:
            stack = [p for p in self.cwd.split("/") if p]
            parts = [p for p in path.split("/") if p]
        for part in parts:
            if part == ".":
                continue
            if part == "..":
                if len(stack) > 1:
                    stack.pop()
            else:
                stack.append(part)
        return "/" + "/".join(stack)

    def _node(self, path):
        node = self.paths
        for part in self._resolve(path).strip("/").split("/"):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    @staticmethod
    def _split(resolved):
        parent, _, name = resolved.strip("/").rpartition("/")
        return f"/{parent}" if parent else "/", name

