
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


class Filesystem:
    def __init__(self, root_name="root"):
        self.root_name = root_name
        self.paths = {root_name: {}}
        self.contents = {}
        self.cwd = f"/{root_name}"

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
        return resolved

    def touch(self, path, content=b""):
        resolved = self._resolve(path)
        if self._node(resolved) is not None:
            raise FileExistsError(f"already exists: {path}")
        parent, name = self._split(resolved)
        node = self._node(parent)
        if node is None or not isinstance(node, dict):
            raise FileNotFoundError(f"missing parent: {path}")
        node[name] = FILE_IDENTIFIER
        self.contents[resolved] = content
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
        resolved = self._resolve(path)
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
        return resolved

    def is_dir(self, path):
        return isinstance(self._node(path), dict)

    def is_file(self, path):
        return self._node(path) == FILE_IDENTIFIER

    def resolve(self, path=None):
        return self._resolve(path)

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

