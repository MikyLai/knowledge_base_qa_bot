import math
import re # Regular Expression
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"
INDEX_PATH = Path(__file__).resolve().parents[3] / ".kb" / "index.json"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "is",
    "it",
    "my",
    "of",
    "the",
    "to",
    "what",
    "when",
    "which",
}


@dataclass
class Section:
    id: str
    file: str
    heading: str
    heading_path: list[str]
    content: str
    tokens: list[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file": self.file,
            "heading": self.heading,
            "heading_path": self.heading_path,
            "content": self.content,
            "tokens": self.tokens,
        }


sections: list[Section] = []
doc_freq: Counter[str] = Counter()
avg_doc_len = 0.0
files_indexed = 0


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP_WORDS]


def parse_markdown(path: Path) -> list[Section]:
    filename = path.name
    result: list[Section] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    current_heading: str | None = None
    current_content_lines: list[str] = []
    heading_stack: list[tuple[int, str]] = []  # (level, heading_text)

    def flush() -> None:
        if current_heading is None:
            return
        content = "\n".join(current_content_lines).strip()
        heading_path = [h for _, h in heading_stack]
        section_id = f"{filename}#{slugify(current_heading)}"
        tokens = tokenize(current_heading) + tokenize(content)
        result.append(Section(
            id=section_id,
            file=filename,
            heading=current_heading,
            heading_path=heading_path,
            content=content,
            tokens=tokens,
        ))

    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            heading_text = m.group(2)
            # 移除同層或更深層的標題，保留父層
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading_text))
            current_heading = heading_text
            current_content_lines = []
        else:
            if current_heading is not None:
                current_content_lines.append(line)

    flush()
    return result


def write_index_json(index_path: Path = INDEX_PATH) -> None:
    # TODO: Persist the section index to .kb/index.json so it is inspectable.
    #
    # Hints:
    # 1. Create index_path.parent if it does not exist.
    # 2. Write {"sections": [...], "stats": {...}} as pretty JSON.
    # 3. Use section.to_dict() for each Section.
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump({
            "sections": [s.to_dict() for s in sections],
            "stats": {
                "files_indexed": files_indexed,
                "sections_indexed": len(sections),
                "avg_doc_len": avg_doc_len,
            },
        }, f, indent=2)



def rebuild_stats() -> None:
    global doc_freq, avg_doc_len, files_indexed

    files_indexed = len({s.file for s in sections})

    doc_freq.clear()
    for s in sections:
        for token in set(s.tokens):  # set() 避免同一 section 重複計算
            doc_freq[token] += 1

    avg_doc_len = sum(len(s.tokens) for s in sections) / len(sections) if sections else 0.0


def load_index_json(index_path: Path = INDEX_PATH) -> tuple[int, int]:
    # TODO: Load .kb/index.json into the in-memory sections list.
    #
    # Hints:
    # 1. If index_path does not exist, return (0, 0).
    # 2. Read payload["sections"] and convert each item back to Section.
    # 3. Call rebuild_stats() after assigning sections.
    # 4. Return (files_indexed, sections_indexed).
    return 0, 0


def build_index(docs_dir: Path = DOCS_DIR) -> tuple[int, int]:
    global sections, doc_freq, avg_doc_len, files_indexed

    # TODO: Build an in-memory section index from docs/*.md.
    #
    # Hints:
    # 1. Read all Markdown files from docs_dir.
    # 2. Call parse_markdown() for each file.
    # 3. Call rebuild_stats() to compute BM25 metadata.
    # 4. Persist .kb/index.json with write_index_json().
    # 5. Call write_index_json() so students can inspect the generated index.
    # 6. Return (files_indexed, sections_indexed).
    sections = []
    doc_freq = Counter()
    avg_doc_len = 0.0
    files_indexed = 0

    for md_file in sorted(docs_dir.glob("*.md")):
        sections += parse_markdown(md_file)

    rebuild_stats()
    write_index_json()

    return files_indexed, len(sections)


def bm25_score(query_tokens: list[str], section: Section, k1: float = 1.5, b: float = 0.75) -> float:
    N = len(sections)
    if N == 0 or avg_doc_len == 0.0:
        return 0.0

    token_counts = Counter(section.tokens)
    doc_len = len(section.tokens)
    heading_tokens = set(tokenize(" ".join(section.heading_path)))

    score = 0.0
    for token in query_tokens:
        tf_t = token_counts[token]
        if tf_t == 0:
            continue
        df_t = doc_freq.get(token, 0)
        if df_t == 0:
            continue
        idf = math.log((N - df_t + 0.5) / (df_t + 0.5) + 1)
        tf_norm = (tf_t * (k1 + 1)) / (tf_t + k1 * (1 - b + b * doc_len / avg_doc_len))
        score += idf * tf_norm
        if token in heading_tokens:
            score += 0.5  # 標題命中加分

    return score


def search(query: str, k: int = 3) -> list[tuple[Section, float]]:
    query_tokens = tokenize(query)
    ranked = [
        (section, bm25_score(query_tokens, section))
        for section in sections
    ]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [(section, score) for section, score in ranked[:k] if score > 0]
