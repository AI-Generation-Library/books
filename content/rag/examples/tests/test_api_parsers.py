from dataclasses import replace
import io
from fastapi.testclient import TestClient
from ragbook.api import create_app
from ragbook.data import Principal
from ragbook.parsers import html_text, pdf_pages
from tests.test_core import Fixture, READER, ADMIN


class APITests(Fixture):
    def setUp(self):
        super().setUp()
        self.client = TestClient(
            create_app(
                self.engine, {"reader-local-token": READER, "admin-local-token": ADMIN}
            )
        )
        self.addCleanup(self.client.close)
        self.reader = {"Authorization": "Bearer reader-local-token"}
        self.admin = {"Authorization": "Bearer admin-local-token"}

    def test_auth_and_input_schema(self):
        self.assertEqual(
            self.client.post("/query", json={"question": "휴가"}).status_code, 401
        )
        self.assertEqual(
            self.client.post(
                "/query",
                headers=self.reader,
                json={"question": "휴가", "tenant": "other"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/query", headers=self.reader, json={"question": "휴가", "limit": 100}
            ).status_code,
            422,
        )

    def test_query_and_no_secret_in_search(self):
        self.store.upsert(
            replace(self.doc, id="secret", roles=("admin",), text="ORION-SECRET-42"),
            self.embedder,
        )
        result = self.client.post(
            "/query", headers=self.reader, json={"question": "휴가"}
        )
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json()["abstained"])
        self.assertIn("X-Request-ID", result.headers)
        result = self.client.post(
            "/search", headers=self.reader, json={"question": "ORION-SECRET-42"}
        )
        self.assertNotIn("ORION-SECRET-42", result.text)

    def test_admin_update_delete_and_reader_denied(self):
        body = {
            "id": "leave",
            "title": "휴가 개정",
            "source": "fixture://leave",
            "version": "v2",
            "roles": ["reader", "admin"],
            "text": "연차 휴가는 20일입니다.",
        }
        self.assertEqual(
            self.client.put("/documents", headers=self.reader, json=body).status_code,
            403,
        )
        self.assertEqual(
            self.client.put("/documents", headers=self.admin, json=body).status_code,
            200,
        )
        self.assertIn(
            "20일",
            self.client.post(
                "/query", headers=self.reader, json={"question": "휴가"}
            ).json()["answer"],
        )
        self.assertEqual(
            self.client.delete("/documents/leave", headers=self.admin).status_code, 200
        )
        self.assertTrue(
            self.client.post(
                "/query", headers=self.reader, json={"question": "휴가"}
            ).json()["abstained"]
        )

    def test_stream_and_ui(self):
        response = self.client.post(
            "/query/stream", headers=self.reader, json={"question": "휴가"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("event: answer", response.text)
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("textContent", page.text)
        self.assertNotIn("innerHTML", page.text)


class ParserTests(Fixture):
    def test_html_excludes_scripts_and_preserves_table_separator(self):
        result = html_text(
            "<h1>제목</h1><script>secret()</script><table><tr><td>A</td><td>B</td></tr></table>"
        )
        self.assertIn("제목", result)
        self.assertIn("A\tB", result)
        self.assertNotIn("secret", result)

    def test_pdf_text_and_blank_page_flags(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        content = DecodedStreamObject()
        content.set_data(b"BT /F1 12 Tf 72 720 Td (RAG sample evidence) Tj ET")
        page[NameObject("/Contents")] = content
        writer.add_blank_page(width=612, height=792)
        path = self.root / "sample.pdf"
        with path.open("wb") as stream:
            writer.write(stream)
        pages = pdf_pages(path)
        self.assertIn("RAG sample evidence", pages[0]["text"])
        self.assertFalse(pages[0]["needs_ocr"])
        self.assertTrue(pages[1]["needs_ocr"])
        with self.assertRaises(ValueError):
            pdf_pages(path, max_pages=1)
