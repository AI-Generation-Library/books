---
title: "프레임워크 연결"
description: "기존 검색과 권한을 유지하는 어댑터입니다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# 프레임워크 연결

핵심 engine.search는 인증된 Principal을 받는다. LangChain BaseRetriever는 이를 Document로, LlamaIndex BaseRetriever는 NodeWithScore/TextNode로 변환한다. document_id·chunk_id·version·source를 유지한다.

```sh
python -m pip install -r requirements-frameworks.txt
python -m ragbook.cli index
python -m demos.frameworks
```

adapters/frameworks.py가 실제 구현이다. retriever 인스턴스는 서버가 검증한 Principal에 묶고 관리자 인스턴스를 다른 사용자에게 전역 공유하지 않는다. 외부 tracing과 프레임워크 기본 LLM은 자동 사용하지 않는다.

실제 실행은 각 어댑터의 결과 반환과 비인가 자료 제외를 확인했다. 프레임워크의 모든 생성 체인·agent·외부 모델을 검증한 것은 아니다. 패키지 버전이 바뀌면 sync/async 인터페이스·문서 모델·callback 계약을 확인한다.
