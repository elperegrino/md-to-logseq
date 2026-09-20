import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Block:
    content: str
    children: list = field(default_factory=list)


def parse_markdown(text: str) -> tuple[str, list[Block]]:
    """
    Returns (title, blocks) where title is extracted from the first # heading
    or an empty string if none found. Blocks is the list of top-level blocks.
    """
    lines = text.strip().split("\n")
    title = ""
    start = 0

    if lines and re.match(r"^#\s+", lines[0]):
        title = re.sub(r"^#\s+", "", lines[0]).strip()
        start = 1

    blocks = _parse_lines(lines[start:])
    return title, blocks


def _parse_lines(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        # Fenced code block
        if line.startswith("```"):
            code_lines = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                code_lines.append(lines[i])
            blocks.append(Block(content="\n".join(code_lines)))
            i += 1
            continue

        # Heading (## and below become blocks; # is the page title handled above)
        if re.match(r"^#{1,6}\s+", line):
            blocks.append(Block(content=line.strip()))
            i += 1
            continue

        # Unordered list item at column 0
        ul_match = re.match(r"^[-*+]\s+(.+)", line)
        if ul_match:
            block = Block(content=ul_match.group(1).strip())
            i += 1
            i = _collect_list_children(lines, i, base_indent=0, parent=block)
            blocks.append(block)
            continue

        # Ordered list item at column 0
        ol_match = re.match(r"^\d+\.\s+(.+)", line)
        if ol_match:
            block = Block(content=ol_match.group(1).strip())
            i += 1
            i = _collect_list_children(lines, i, base_indent=0, parent=block, ordered=True)
            blocks.append(block)
            continue

        # Blockquote — collapse consecutive lines
        if line.startswith(">"):
            quote_lines = [re.sub(r"^>\s?", "", line)]
            i += 1
            while i < len(lines) and lines[i].startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append(Block(content="> " + " ".join(quote_lines)))
            continue

        # Horizontal rule → visual separator
        if re.match(r"^[-*_]{3,}\s*$", line):
            blocks.append(Block(content="---"))
            i += 1
            continue

        # Paragraph — collapse consecutive non-empty, non-special lines
        para_lines = [line.strip()]
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if (
                not next_line.strip()
                or next_line.startswith("#")
                or next_line.startswith("```")
                or next_line.startswith(">")
                or re.match(r"^[-*+]\s+", next_line)
                or re.match(r"^\d+\.\s+", next_line)
                or re.match(r"^[-*_]{3,}\s*$", next_line)
            ):
                break
            para_lines.append(next_line.strip())
            i += 1
        blocks.append(Block(content=" ".join(para_lines)))

    return blocks


def _collect_list_children(
    lines: list[str],
    start: int,
    base_indent: int,
    parent: Block,
    ordered: bool = False,
) -> int:
    """Reads indented list items after `start` and appends them as children of parent."""
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        if indent <= base_indent:
            break

        ul_match = re.match(r"^\s+[-*+]\s+(.+)", line)
        ol_match = re.match(r"^\s+\d+\.\s+(.+)", line)
        match = ul_match or ol_match
        if match:
            child = Block(content=match.group(1).strip())
            i += 1
            i = _collect_list_children(lines, i, base_indent=indent, parent=child)
            parent.children.append(child)
        else:
            break

    return i
