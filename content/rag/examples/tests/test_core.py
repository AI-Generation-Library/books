from dataclasses import replace
import json
import math
from pathlib import Path
import tempfile
import unittest
from ragbook.data import Document, Principal, chunks, normalize, tokenize
from ragbook.embedding import CharacterEmbedder, cosine, unit
from ragbook.store import Store
from ragbook.engine import Engine
from ragbook.generation import Claim, ExtractiveGenerator, validate_claims
from ragbook.retrieval import Hit, bm25, dense, rrf, mmr
from ragbook.metrics import retrieval_metrics, evaluate

BASE = Path(__file__).resolve().parents[1]
READER = Principal("acme", frozenset({"reader"}))
ADMIN = Principal("acme", frozenset({"admin"}))


class Fixture(unittest.TestCase):
    def setUp(self):
        directory = BASE / "var/tests"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=directory)
        self.root = Path(self.temp.name)
        self.assertTrue(self.root.resolve().is_relative_to(directory.resolve()))
        self.addCleanup(self.temp.cleanup)
        self.embedder = CharacterEmbedder()
        self.store = Store(self.root / "index.sqlite3", self.embedder.signature)
        self.doc = Document(
            "leave",
            "acme",
            ("reader", "admin"),
            "휴가",
            "fixture://leave",
            "v1",
            "연차 휴가는 연간 15일입니다. 휴가 신청은 3일 전에 합니다.",
        )
        self.store.upsert(self.doc, self.embedder)
        self.engine = Engine(self.store, self.embedder, ExtractiveGenerator())


class DataTests(Fixture):
    def test_normalize_and_idempotence(self):
        value = normalize("Ａ  B\r\n  휴가\t 안내 ")
        self.assertEqual(value, "A B\n휴가 안내")
        self.assertEqual(normalize(value), value)

    def test_chunk_offsets_cover_normalized_text(self):
        doc = replace(self.doc, text="안녕하세요 " * 200)
        text = normalize(doc.text)
        parts = chunks(doc, 64, 12)
        self.assertEqual(parts[0].start, 0)
        self.assertEqual(parts[-1].end, len(text))
        self.assertTrue(all(c.text == text[c.start : c.end] for c in parts))
        self.assertTrue(all(a.end - b.start == 12 for a, b in zip(parts, parts[1:])))

    def test_chunk_identity_tracks_metadata_version_and_tenant(self):
        original = chunks(self.doc)[0].id
        for doc in [
            replace(self.doc, version="v2"),
            replace(self.doc, tenant="other"),
            replace(self.doc, roles=("admin",)),
            replace(self.doc, source="fixture://new"),
        ]:
            self.assertNotEqual(chunks(doc)[0].id, original)
        self.assertEqual(chunks(self.doc)[0].id, original)

    def test_empty_and_invalid_chunk_config(self):
        self.assertEqual(chunks(replace(self.doc, text="  ")), [])
        for size, overlap in [(10, 0), (64, 64), (64, -1)]:
            with self.assertRaises(ValueError):
                chunks(self.doc, size, overlap)

    def test_korean_bigrams_and_nfkc(self):
        self.assertIn("휴가", tokenize("휴가는"))
        self.assertIn("abc", tokenize("ＡＢＣ"))

    def test_vectors_are_normalized_and_cosine_validated(self):
        a = self.embedder.embed(["같은 문장"])[0]
        self.assertAlmostEqual(cosine(a, a), 1)
        self.assertAlmostEqual(sum(x * x for x in a), 1)
        self.assertEqual(unit([0, 0]), (0, 0))
        with self.assertRaises(ValueError):
            cosine([1], [1, 0])
        with self.assertRaises(ValueError):
            unit([float("nan")])


class StoreTests(Fixture):
    def test_roles_and_tenant_are_filtered_before_retrieval(self):
        self.store.upsert(
            replace(self.doc, id="secret", roles=("admin",), text="ORION-SECRET-42"),
            self.embedder,
        )
        self.store.upsert(
            replace(self.doc, tenant="other", text="OTHER-TENANT-99"), self.embedder
        )
        reader = self.store.authorized(READER)
        self.assertEqual({x.doc_id for x in reader}, {"leave"})
        self.assertNotIn("SECRET", repr(reader))
        self.assertNotIn("OTHER-TENANT", repr(reader))
        self.assertEqual(
            {x.doc_id for x in self.store.authorized(ADMIN)}, {"leave", "secret"}
        )

    def test_empty_roles_deny_access(self):
        self.assertEqual(self.store.authorized(Principal("acme", frozenset())), [])

    def test_update_replaces_old_chunks(self):
        old = {c.id for c in self.store.authorized(READER)}
        self.store.upsert(
            replace(self.doc, version="v2", text="연차 휴가는 20일입니다."),
            self.embedder,
        )
        current = self.store.authorized(READER)
        self.assertTrue(old.isdisjoint(c.id for c in current))
        self.assertIn("20일", current[0].text)

    def test_delete_cascades_and_is_tenant_scoped(self):
        self.store.upsert(replace(self.doc, tenant="other"), self.embedder)
        self.store.delete("acme", "leave")
        self.assertEqual(self.store.authorized(READER), [])
        self.assertEqual(
            len(self.store.authorized(Principal("other", frozenset({"reader"})))), 1
        )

    def test_failed_embedding_keeps_old_version(self):
        class Broken(CharacterEmbedder):
            def embed(self, texts):
                raise RuntimeError("inference failed")

        with self.assertRaises(RuntimeError):
            self.store.upsert(replace(self.doc, version="v2"), Broken())
        self.assertEqual(self.store.authorized(READER)[0].version, "v1")

    def test_dimension_mismatch_rolls_back(self):
        class Wrong(CharacterEmbedder):
            def embed(self, texts):
                return [(1.0, 0.0)] * len(texts)

        with self.assertRaises(ValueError):
            self.store.upsert(replace(self.doc, version="v2"), Wrong())
        self.assertEqual(self.store.authorized(READER)[0].version, "v1")

    def test_embedding_signature_and_bad_metadata_rejected(self):
        with self.assertRaises(ValueError):
            Store(self.store.path, "different-model")
        for doc in [
            replace(self.doc, roles=()),
            replace(self.doc, source="javascript:alert(1)"),
            replace(self.doc, id="../bad"),
        ]:
            with self.assertRaises(ValueError):
                self.store.upsert(doc, self.embedder)


class RetrievalTests(Fixture):
    def test_bm25_relevant_and_unknown(self):
        parts = self.store.authorized(READER)
        self.assertEqual(bm25("휴가", parts)[0].chunk.doc_id, "leave")
        self.assertEqual(bm25("Saturn", parts), [])
        self.assertEqual(bm25("a", []), [])

    def test_dense_and_rrf(self):
        parts = self.store.authorized(READER)
        ranked = dense("휴가", parts, self.embedder)
        merged = rrf([ranked, ranked])
        self.assertEqual(len(merged), 1)
        self.assertAlmostEqual(merged[0].score, 2 / 61)

    def test_rrf_does_not_duplicate_same_chunk(self):
        hit = Hit(self.store.authorized(READER)[0], 1)
        self.assertAlmostEqual(rrf([[hit, hit]])[0].score, 1 / 61)

    def test_mmr_and_input_limits(self):
        parts = self.store.authorized(READER)
        ranked = dense("휴가", parts, self.embedder)
        self.assertEqual(len(mmr(ranked, self.embedder.embed(["휴가"])[0], 1)), 1)
        with self.assertRaises(ValueError):
            self.engine.search("휴가", READER, limit=0)
        with self.assertRaises(ValueError):
            self.engine.search("", READER)
        with self.assertRaises(ValueError):
            self.engine.search("휴가", READER, mode="magic")

    def test_reranker_never_receives_unauthorized_candidates(self):
        self.store.upsert(
            replace(self.doc, id="secret", roles=("admin",), text="휴가 SECRET"),
            self.embedder,
        )

        class Spy:
            received = []

            def rerank(self, q, hits):
                self.received = list(hits)
                return list(reversed(hits))

        spy = Spy()
        engine = Engine(self.store, self.embedder, ExtractiveGenerator(), spy)
        result = engine.search("휴가", READER)
        self.assertTrue(result)
        self.assertTrue(spy.received)
        self.assertTrue(all(h.chunk.doc_id != "secret" for h in spy.received))


class GenerationTests(Fixture):
    def test_extractive_answer_and_citation(self):
        result = self.engine.answer("휴가", READER)
        self.assertFalse(result["abstained"])
        self.assertIn("15일", result["answer"])
        self.assertEqual(result["generator"], "extractive-demo-not-llm")
        self.assertEqual(result["citations"][0]["version"], "v1")

    def test_unknown_and_context_budget_refuse(self):
        self.assertTrue(self.engine.answer("Saturn rings", READER)["abstained"])
        self.assertEqual(
            self.engine.answer("휴가", READER, budget=1)["reason"], "context_budget"
        )

    def test_fabricated_citation_is_rejected(self):
        class Bad:
            name = "bad-test-double"

            def generate(self, q, context):
                return [Claim("거짓", "invented", "원문 아님")]

        result = Engine(self.store, self.embedder, Bad()).answer("휴가", READER)
        self.assertEqual(result["reason"], "invalid_citation")
        self.assertNotIn("거짓", result["answer"])

    def test_modified_quote_is_rejected(self):
        context = self.engine.search("휴가", READER)
        with self.assertRaises(ValueError):
            validate_claims(
                [Claim("답", context[0].chunk.id, "정확하지 않은 인용")], context
            )

    def test_malformed_model_field_types_are_rejected(self):
        context = self.engine.search("휴가", READER)
        with self.assertRaises(ValueError):
            validate_claims([Claim(42, context[0].chunk.id, "15일")], context)

    def test_model_can_explicitly_abstain(self):
        class Refused:
            name = "refusal-test-double"

            def generate(self, q, context):
                return []

        self.assertEqual(
            Engine(self.store, self.embedder, Refused()).answer("휴가", READER)[
                "reason"
            ],
            "model_abstained",
        )

    def test_substring_check_does_not_prove_claim_entailment(self):
        context = self.engine.search("휴가", READER)
        claim = Claim("휴가가 999일이라는 잘못된 주장", context[0].chunk.id, "15일")
        self.assertEqual(validate_claims([claim], context), [claim])
        # 이 통과가 의미적 정확성 보장이 아님을 의도적으로 고정한다.

    def test_permission_revocation_during_generation_blocks_delivery(self):
        fixture = self

        class Revoked:
            name = "revocation-test-double"

            def generate(self, q, context):
                fixture.store.upsert(
                    replace(fixture.doc, roles=("admin",)), fixture.embedder
                )
                return [
                    Claim(
                        context[0].chunk.text,
                        context[0].chunk.id,
                        context[0].chunk.text,
                    )
                ]

        result = Engine(self.store, self.embedder, Revoked()).answer("휴가", READER)
        self.assertEqual(result["reason"], "context_changed")
        self.assertEqual(result["citations"], [])

    def test_document_delete_during_generation_blocks_delivery(self):
        fixture = self

        class Deleted:
            name = "deletion-test-double"

            def generate(self, q, context):
                fixture.store.delete("acme", "leave")
                return [
                    Claim(
                        context[0].chunk.text,
                        context[0].chunk.id,
                        context[0].chunk.text,
                    )
                ]

        self.assertEqual(
            Engine(self.store, self.embedder, Deleted()).answer("휴가", READER)[
                "reason"
            ],
            "context_changed",
        )


class MetricTests(unittest.TestCase):
    def test_known_values_and_duplicates(self):
        result = retrieval_metrics(["x", "a", "a", "b"], {"a": 2, "b": 1}, 3)
        self.assertAlmostEqual(result["precision"], 2 / 3)
        self.assertEqual(result["recall"], 1)
        self.assertEqual(result["reciprocal_rank"], 0.5)
        expected = (3 / math.log2(3) + 1 / math.log2(4)) / (3 + 1 / math.log2(3))
        self.assertAlmostEqual(result["ndcg"], expected)

    def test_no_qrels_and_empty_rank(self):
        self.assertIsNone(retrieval_metrics(["a"], {}, 3)["recall"])
        self.assertIsNone(retrieval_metrics([], {}, 3)["ndcg"])
        self.assertEqual(retrieval_metrics([], {"a": 1}, 3)["recall"], 0)
        with self.assertRaises(ValueError):
            retrieval_metrics([], {}, 0)
