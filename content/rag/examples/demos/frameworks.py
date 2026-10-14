import os

# 예시 데이터를 외부 tracing 서비스로 자동 전송하지 않는다.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"
from ragbook.cli import make_engine
from ragbook.data import Principal
from adapters.frameworks import langchain_retriever, llamaindex_retriever

if __name__ == "__main__":
    engine = make_engine("var/index-demo.sqlite3")
    identity = Principal("acme", frozenset({"reader"}))
    lc = langchain_retriever(engine, identity).invoke("휴가")
    li = llamaindex_retriever(engine, identity).retrieve("휴가")
    print(
        "LangChain:", [(d.metadata["document_id"], d.metadata["version"]) for d in lc]
    )
    print(
        "LlamaIndex:",
        [(d.node.metadata["document_id"], d.node.metadata["version"]) for d in li],
    )
