import gc
import os
import shutil
import sys
import tempfile
import time

from core.agent import AgentFilesystem
from core.persist import Wal
from core.setup import Filesystem

N = int(os.environ.get("BENCH_N", 500))
SIZES = [256, 1024, 4096]
REPEATS = 3
BACKENDS = ["real fs", "sfs", "sfs+wal", "agent"]
NEEDLE = "NEEDLE_sfs_bench"


def make_content(size, with_needle=False):
	line = "scratchpad line with some text and a number "
	text = (line * (size // len(line) + 1))[:size]
	if with_needle:
		text = NEEDLE + text[len(NEEDLE):]
	return text


class RealFs:
	def __init__(self, root):
		self.root = root
		os.makedirs(root, exist_ok=True)

	def write(self, i, content):
		with open(os.path.join(self.root, f"bench_{i:05d}.txt"), "w") as f:
			f.write(content)

	def read(self, i):
		with open(os.path.join(self.root, f"bench_{i:05d}.txt")) as f:
			return f.read()

	def grep(self, pattern):
		hits = []
		for i in range(N):
			if pattern in self.read(i):
				hits.append(i)
		return hits


class SfsBench:
	def __init__(self, wal_path=None, agent=False):
		fs = Filesystem(max_file_bytes=8192, max_total_bytes=64 * 1024 * 1024)
		if wal_path:
			fs.journal = Wal(wal_path)
		self.fs = fs
		self.afs = AgentFilesystem(fs) if agent else None
		self.wal_path = wal_path

	def write(self, i, content):
		self.fs.write(f"/bench_{i:05d}.txt", content)

	def read(self, i):
		return self.fs.read(f"/bench_{i:05d}.txt")

	def grep(self, pattern):
		return self.fs.grep(pattern)


class AgentBench(SfsBench):
	def __init__(self, tmp):
		super().__init__(agent=True)

	def write(self, i, content):
		self.afs.write(f"/bench_{i:05d}.txt", content)

	def read(self, i):
		return self.afs.read(f"/bench_{i:05d}.txt")

	def grep(self, pattern):
		return self.afs.grep(pattern).matches


def build(backend, tmp, round_no):
	shutil.rmtree(tmp, ignore_errors=True)
	os.makedirs(tmp, exist_ok=True)
	if backend == "real fs":
		return RealFs(os.path.join(tmp, "real"))
	if backend == "sfs":
		return SfsBench()
	if backend == "sfs+wal":
		return SfsBench(wal_path=os.path.join(tmp, "bench.wal"))
	return AgentBench(tmp)


def scenario(backend, tmp, size, mode):
	def run_once(round_no):
		b = build(backend, tmp, round_no)
		contents = [make_content(size, with_needle=(i == N // 2)) for i in range(N)]
		if mode != "write":
			for i, content in enumerate(contents):
				b.write(i, content)
		if mode == "write":
			def op():
				for i, content in enumerate(contents):
					b.write(i, content)
		elif mode == "read":
			def op():
				for i in range(N):
					b.read(i)
		elif mode == "overwrite":
			plain = make_content(size)
			def op():
				for i in range(N):
					b.write(i, plain)
		elif mode == "grep":
			def op():
				return len(b.grep(NEEDLE))
		start = time.perf_counter()
		gc_was = gc.isenabled()
		gc.disable()
		try:
			op()
		finally:
			if gc_was:
				gc.enable()
		return time.perf_counter() - start

	best = None
	for round_no in range(REPEATS):
		elapsed = run_once(round_no)
		best = elapsed if best is None else min(best, elapsed)
	return best


def fmt(seconds):
	per_op = seconds / N * 1e6
	return f"{N / seconds:>12,.0f} ops/s {per_op:>8.2f} us/op"


def main():
	tmp = tempfile.mkdtemp(prefix="sfs_bench_")
	print(f"sfs benchmark — {N} files per round, best of {REPEATS}")
	print()
	for mode in ["write", "read", "overwrite", "grep"]:
		print(f"[{mode}]")
		header = f"  {'size':>6}"
		for backend in BACKENDS:
			header += f" | {backend:>20}"
		print(header)
		for size in SIZES:
			row = f"  {size:>6}B"
			for backend in BACKENDS:
				row += f" | {fmt(scenario(backend, tmp, size, mode)):>20}"
			print(row)
		print()
	shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
	sys.exit(main())
