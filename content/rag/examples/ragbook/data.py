from dataclasses import dataclass
import hashlib
import re
import unicodedata


@dataclass(frozen=True)
class Principal:
    tenant: str
    roles: frozenset[str]


@dataclass(frozen=True)
class Document:
    id: str
    tenant: str
    roles: tuple[str, ...]
    title: str
    source: str
    version: str
    text: str


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    tenant: str
    title: str
    source: str
    version: str
    start: int
    end: int
    text: str
    vector: tuple[float, ...] = ()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(
        re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")
    ).strip()


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+|[가-힣]+", normalize(text).lower())
    # 형태소 분석기가 아니다. 조사 변화에 대한 작은 데모용 한글 2-gram이다.
    return words + [
        word[i : i + 2]
        for word in words
        if re.fullmatch("[가-힣]+", word)
        for i in range(len(word) - 1)
    ]


def chunks(doc: Document, size: int = 320, overlap: int = 40) -> list[Chunk]:
    if (
        not isinstance(size, int)
        or not isinstance(overlap, int)
        or size < 32
        or not 0 <= overlap < size
    ):
        raise ValueError("size>=32 and 0<=overlap<size")
    text = normalize(doc.text)
    if not text:
        return []
    result = []
    for start in range(0, len(text), size - overlap):
        end = min(start + size, len(text))
        body = text[start:end]
        identity = (
            doc.tenant,
            doc.id,
            doc.version,
            doc.title,
            doc.source,
            ",".join(sorted(doc.roles)),
            str(start),
            body,
        )
        key = hashlib.sha256("\0".join(identity).encode()).hexdigest()[:24]
        result.append(
            Chunk(
                key,
                doc.id,
                doc.tenant,
                doc.title,
                doc.source,
                doc.version,
                start,
                end,
                body,
            )
        )
        if end == len(text):
            break
    return result
