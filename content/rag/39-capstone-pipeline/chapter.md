---
title: "39장. 수집부터 답변까지 전체 파이프라인 구현"
description: "색인·검색·리랭킹·생성·API를 같은 계약으로 연결한다. 프레임워크 전환에도 권한과 출처를 유지한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 39
part: 9
enableToc: true
---

# 39장. 수집부터 답변까지 전체 파이프라인 구현

## 학습 목표

- 색인·검색·리랭킹·생성·API를 같은 계약으로 연결한다.
- 프레임워크 전환에도 권한과 출처를 유지한다.

## 실행 파일을 따라가기

data.py는 문서·청크·Principal과 정규화를, store.py는 원자적 교체·권한 후보를, retrieval.py는 BM25·dense·RRF·MMR을 담당한다. engine.py는 검색·근거 선택·생성·인용·반환 전 재검사를 연결한다. api.py와 serve.py는 HTTP와 학습용 인증을 조립한다.

모듈 import로 모델과 서버를 시작하지 않는다. CLI에서 embedding·model·rerank를 명시해 실제 모델 연결을 선택한다. 모델 signature가 다른 DB는 새로 만들고, API와 CLI가 같은 경로와 설정을 쓰게 한다.

## 기본 모드

```sh
python -m ragbook.cli index
python -m ragbook.cli query "연차 휴가는 연간 며칠인가요?"
python -m ragbook.cli evaluate --split test --mode hybrid
python serve.py
```

발췌 모드의 generator 값을 확인한다. 위조 인용·권한·삭제의 실패 경로를 먼저 검증한다. 출력의 citation_check는 원문 멤버십·부분 문자열 검사 범위를 알려 준다.

## 실제 모델 모드

별도 neural DB에 다국어 embedding으로 색인하고 선택형 리랭커를 켠다. 이미 준비된 로컬 Ollama 모델 이름을 --model로 전달하면 실제 생성으로 연결한다. 책의 집필 환경은 qwen3.5:4b를 사용했으며 모든 모델이 같은 품질과 출력 형식으로 동작한다고 보장하지 않는다.

모델명·가중치·양자화·컨텍스트·온도·출력 상한을 기록한다. 생성 JSON 파싱·없는 ID·quote 검증 실패는 안전하게 거절한다. 출력이 잘렸다면 임의로 성공 처리하지 않고 기한·길이·형식을 원인별로 확인한다.

## 프레임워크 연결

LangChain의 BaseRetriever와 LlamaIndex의 BaseRetriever를 서버 Principal에 묶어 같은 engine.search를 호출하게 한다. 반환 Document/TextNode에 청크 ID·문서·버전·source를 유지한다. 프레임워크로 감싼다고 권한 경계가 생기거나 없어지지 않는다.

어댑터 검증은 검색 반환과 비인가 자료 제외를 확인한다. 프레임워크의 기본 LLM·외부 tracing을 자동으로 켜지 않으며 별도 생성 체인을 검증했다고 기록하지 않는다. 특정 admin retriever를 모든 사용자에게 전역 재사용하지 않는다.

## 실패 때 읽을 순서

원본·정규화·청크·권한 후보·검색 순위·최종 컨텍스트·모델 출력·인용 검사 순서로 좁힌다. HTTP 오류와 품질 실패를 구분하고 비밀정보를 로그에 출력하지 않는다. 작은 정상 예제만 붙여 놓는 대신 이 경계 테스트를 유지한다.

## 실습과 평가

실제 모델 모드의 정확한 PowerShell 명령과 의존성 설치는 examples/README.md를 따른다. neural-results·rerank-results·llm-results는 각각 다른 관측 범위를 기록한다.

프레임워크 데모를 실행해 같은 질문의 document_id·version이 유지되는지 확인한다. 실제 LLM 출력 한 건을 전체 자동 평가 결과처럼 합산하지 않는다.

## 확인 문제

검색 어댑터를 프레임워크로 감싸면 원래 서비스의 인증·tenant 필터를 빼도 되는가?

[해설](../appendices/answers.md#장-39)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Retriever integrations - Docs by LangChain](https://docs.langchain.com/oss/python/integrations/retrievers)
- [Retriever | Developer Documentation](https://developers.llamaindex.ai/python/framework/module_guides/querying/retriever/)
- [FastEmbed](https://qdrant.github.io/fastembed/)

---

[이전 장](../38-capstone-design/chapter.md) · [책 목차](../index.md) · [다음 장](../40-capstone-validation/chapter.md)
