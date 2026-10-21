TOOL_SPECS = [
	{
		"name": "ls",
		"description": "List a directory. Returns sorted entries with path, is_dir and size.",
		"parameters": {
			"type": "object",
			"properties": {
				"path": {
					"type": "string",
					"description": "Directory path, absolute or relative to root.",
					"default": "/",
				},
			},
			"required": [],
		},
	},
	{
		"name": "read",
		"description": "Read a text file. Line-based pagination via offset and limit; negative offset counts from the end.",
		"parameters": {
			"type": "object",
			"properties": {
				"file_path": {"type": "string", "description": "File path to read."},
				"offset": {"type": "integer", "description": "Line to start from.", "default": 0},
				"limit": {"type": "integer", "description": "Max lines to return.", "default": 2000},
			},
			"required": ["file_path"],
		},
	},
	{
		"name": "write",
		"description": "Create or overwrite a file with text content.",
		"parameters": {
			"type": "object",
			"properties": {
				"file_path": {"type": "string", "description": "File path to write."},
				"content": {"type": "string", "description": "Full file content."},
			},
			"required": ["file_path", "content"],
		},
	},
	{
		"name": "edit",
		"description": "Replace text inside an existing file. Fails if old_string is missing or matches more than once, unless replace_all is true.",
		"parameters": {
			"type": "object",
			"properties": {
				"file_path": {"type": "string", "description": "File path to edit."},
				"old_string": {"type": "string", "description": "Exact text to replace."},
				"new_string": {"type": "string", "description": "Replacement text."},
				"replace_all": {"type": "boolean", "description": "Replace every occurrence.", "default": False},
			},
			"required": ["file_path", "old_string", "new_string"],
		},
	},
	{
		"name": "glob",
		"description": "Find paths matching a glob pattern (supports *, ? and **). Optional path scopes the search to a directory.",
		"parameters": {
			"type": "object",
			"properties": {
				"pattern": {"type": "string", "description": "Glob pattern, matched against full path and basename."},
				"path": {"type": "string", "description": "Directory to search in.", "default": "/"},
			},
			"required": ["pattern"],
		},
	},
	{
		"name": "grep",
		"description": "Search file contents for a literal string. Returns path, line number and line text. Optional glob filters which files are searched.",
		"parameters": {
			"type": "object",
			"properties": {
				"pattern": {"type": "string", "description": "Literal text to find."},
				"path": {"type": "string", "description": "Directory to search in.", "default": "/"},
				"glob": {"type": "string", "description": "Glob filter for files, e.g. '*.txt'."},
			},
			"required": ["pattern"],
		},
	},
	{
		"name": "delete",
		"description": "Delete a file or a directory with everything inside it.",
		"parameters": {
			"type": "object",
			"properties": {
				"file_path": {"type": "string", "description": "File or directory path to delete."},
			},
			"required": ["file_path"],
		},
	},
]
