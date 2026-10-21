from dataclasses import dataclass, field
from typing import Optional

from core.setup import Filesystem


@dataclass
class LsResult:
    entries: list = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ReadResult:
    content: str = ""
    total_lines: int = 0
    offset: int = 0
    error: Optional[str] = None


@dataclass
class WriteResult:
    path: str = ""
    bytes_written: int = 0
    error: Optional[str] = None


@dataclass
class EditResult:
    path: str = ""
    error: Optional[str] = None


@dataclass
class GlobResult:
    paths: list = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class GrepResult:
    matches: list = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DeleteResult:
    path: str = ""
    error: Optional[str] = None


class AgentFilesystem:
    def __init__(self, filesystem=None):
        self.fs = filesystem or Filesystem()

    def ls(self, path="/"):
        try:
            base = self.fs.resolve(path).rstrip("/")
            entries = []
            for name in sorted(self.fs.ls(path)):
                full = f"{base}/{name}"
                if self.fs.is_dir(full):
                    entries.append({"path": full, "is_dir": True, "size": len(self.fs.ls(full))})
                else:
                    entries.append({"path": full, "is_dir": False, "size": len(self.fs.read(full))})
            return LsResult(entries=entries)
        except (OSError, ValueError) as e:
            return LsResult(error=str(e))

    def read(self, file_path, offset=0, limit=2000):
        try:
            text = self.fs.read(file_path).decode(errors="replace")
        except (OSError, ValueError) as e:
            return ReadResult(error=str(e))
        lines = text.splitlines()
        if offset < 0:
            offset = max(0, len(lines) + offset)
        window = lines[offset:offset + limit]
        return ReadResult(content="\n".join(window), total_lines=len(lines), offset=offset)

    def write(self, file_path, content):
        try:
            resolved = self.fs.write(file_path, content)
        except (OSError, ValueError) as e:
            return WriteResult(error=str(e))
        return WriteResult(path=resolved, bytes_written=len(content.encode()))

    def edit(self, file_path, old_string, new_string, replace_all=False):
        try:
            resolved = self.fs.edit(file_path, old_string, new_string, replace_all=replace_all)
        except (OSError, ValueError) as e:
            return EditResult(error=str(e))
        return EditResult(path=resolved)

    def glob(self, pattern, path=None):
        try:
            return GlobResult(paths=self.fs.glob(pattern, path=path))
        except (OSError, ValueError) as e:
            return GlobResult(error=str(e))

    def grep(self, pattern, path=None, glob=None):
        try:
            matches = [
                {"path": p, "line": n, "text": t}
                for p, n, t in self.fs.grep(pattern, path=path, glob=glob)
            ]
            return GrepResult(matches=matches)
        except (OSError, ValueError) as e:
            return GrepResult(error=str(e))

    def delete(self, file_path):
        try:
            return DeleteResult(path=self.fs.delete(file_path))
        except (OSError, ValueError) as e:
            return DeleteResult(error=str(e))

    def dispatch(self, name, **kwargs):
        method = getattr(self, name, None)
        if method is None or name.startswith("_"):
            return LsResult(error=f"unknown operation: {name}")
        try:
            return method(**kwargs)
        except TypeError as e:
            return LsResult(error=str(e))
