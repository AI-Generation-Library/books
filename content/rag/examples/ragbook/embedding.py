from collections import Counter
import hashlib
import math
from pathlib import Path
from .data import normalize


def unit(vector):
    values = [float(x) for x in vector]
    if not values or not all(math.isfinite(x) for x in values):
        raise ValueError("invalid vector")
    length = math.sqrt(sum(x * x for x in values))
    return tuple(x / length for x in values) if length else tuple(values)


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("dimension mismatch")
    return sum(x * y for x, y in zip(unit(a), unit(b)))


class CharacterEmbedder:
    """결정적 문자 벡터 데모. 학습한 의미 임베딩으로 표시하지 않는다."""

    signature = "character-bigram-128-v1"

    def embed(self, texts):
        result = []
        for text in texts:
            text = normalize(text).lower()
            counts = Counter(text[i : i + 2] for i in range(max(0, len(text) - 1)))
            vector = [0.0] * 128
            for gram, n in counts.items():
                bucket = (
                    int.from_bytes(
                        hashlib.blake2b(gram.encode(), digest_size=4).digest(), "big"
                    )
                    % 128
                )
                vector[bucket] += n
            result.append(unit(vector))
        return result


class FastEmbedder:
    def __init__(
        self,
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir="model-cache",
    ):
        from fastembed import TextEmbedding
        from importlib.metadata import version

        self.model = TextEmbedding(
            model_name=model_name, cache_dir=cache_dir, threads=2
        )
        # 캐시에는 이 모델만 둔다. ONNX와 토크나이저 파일의 바이트를 함께 고정한다.
        files = sorted(
            p
            for p in Path(cache_dir).rglob("*")
            if p.is_file() and p.suffix in (".onnx", ".json", ".txt")
        )
        manifest = []
        for path in files:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            manifest.append((path.relative_to(cache_dir).as_posix(), digest))
        if not manifest:
            raise RuntimeError("model fingerprint unavailable")
        fingerprint = hashlib.sha256(repr(manifest).encode()).hexdigest()
        self.manifest = manifest
        self.signature = f"fastembed:{version('fastembed')}:{model_name}:{fingerprint}"

    def embed(self, texts):
        return [unit(vector) for vector in self.model.embed(list(texts))]
