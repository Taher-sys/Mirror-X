"""Git unified diff parser."""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileDiff:
    """Parsed diff for a single file."""

    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: str | None = None
    new_path: str | None = None
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)
    added_line_numbers: list[int] = field(default_factory=list)
    deleted_line_numbers: list[int] = field(default_factory=list)
    hunk_headers: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class GitDiffParser:
    """Parses standard Git unified diff strings into structured file diff records."""

    @classmethod
    def parse(cls, diff_text: str) -> list[FileDiff]:
        if not diff_text or not diff_text.strip():
            return []

        file_diffs: list[FileDiff] = []
        raw_files = re.split(r"(?=diff --git )", diff_text)

        for raw_file in raw_files:
            raw_file = raw_file.strip()
            if not raw_file or not raw_file.startswith("diff --git"):
                continue

            lines = raw_file.splitlines()
            header = lines[0]
            m = re.match(r"diff --git a/(.*) b/(.*)", header)
            old_path = m.group(1) if m else None
            new_path = m.group(2) if m else None
            file_path = new_path or old_path or "unknown"

            change_type = "modified"
            if any(line.startswith("new file mode") for line in lines[:5]):
                change_type = "added"
            elif any(line.startswith("deleted file mode") for line in lines[:5]):
                change_type = "deleted"
            elif any(line.startswith(("similarity index", "rename from")) for line in lines[:5]):
                change_type = "renamed"

            added_lines = []
            deleted_lines = []
            hunk_headers = []

            for line in lines:
                if line.startswith("@@"):
                    hunk_headers.append(line)
                elif line.startswith("+") and not line.startswith("+++"):
                    added_lines.append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    deleted_lines.append(line[1:])

            file_diffs.append(
                FileDiff(
                    file_path=file_path,
                    change_type=change_type,
                    old_path=old_path,
                    new_path=new_path,
                    added_lines=added_lines,
                    deleted_lines=deleted_lines,
                    hunk_headers=hunk_headers,
                )
            )

        return file_diffs
