"""Optional integrations. Each retriever is bound to a server-authenticated principal."""


def langchain_retriever(engine, principal):
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document

    class AuthorizedRetriever(BaseRetriever):
        def _get_relevant_documents(self, query, *, run_manager):
            return [
                Document(
                    page_content=hit.chunk.text,
                    metadata={
                        "chunk_id": hit.chunk.id,
                        "document_id": hit.chunk.doc_id,
                        "version": hit.chunk.version,
                        "source": hit.chunk.source,
                    },
                )
                for hit in engine.search(query, principal)
            ]

    return AuthorizedRetriever()


def llamaindex_retriever(engine, principal):
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import TextNode, NodeWithScore

    class AuthorizedRetriever(BaseRetriever):
        def _retrieve(self, query_bundle):
            return [
                NodeWithScore(
                    node=TextNode(
                        id_=hit.chunk.id,
                        text=hit.chunk.text,
                        metadata={
                            "document_id": hit.chunk.doc_id,
                            "version": hit.chunk.version,
                            "source": hit.chunk.source,
                        },
                    ),
                    score=hit.score,
                )
                for hit in engine.search(query_bundle.query_str, principal)
            ]

    return AuthorizedRetriever()
