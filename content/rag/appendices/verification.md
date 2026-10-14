---
title: "생성과 검증 기록"
description: "실제 실행·평가·한계와 재현 자료를 기록합니다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# 생성과 검증 기록

## 출처와 환경

- 작성·검증일: 2026-10-14, Asia/Seoul.
- 저작: Codex가 승인 목차로 대화에서 직접 작성했다. 정확한 저작 모델 ID는 확인하지 못해 null이다. 실습의 qwen 모델을 저작 모델로 기록하지 않는다.
- 입력: generation-input.json. 논문·공식 자료를 확인하고 원문을 대량 복제하지 않고 설명·코드·가상 데이터를 작성했다.
- Windows / Python 3.12.12. 격리한 가상환경과 작업 폴더 캐시를 사용했다.
- 독립 사람·전문가 전체 원고 검수는 미수행이다.

| 직접 의존성 | 실제 버전 |
| --- | --- |
| fastapi | 0.143.0 |
| uvicorn | 0.54.0 |
| httpx | 0.28.1 |
| httpx2 | 2.13.1 |
| pypdf | 6.20.1 |
| fastembed | 0.9.0 |
| langchain-core | 1.6.10 |
| llama-index-core | 0.14.25 |

전이 의존성 snapshot은 examples/requirements-lock.txt다. 처음에는 Starlette TestClient의 httpx deprecation 안내가 있었고 권장 httpx2를 설치한 뒤 최종 테스트 35개가 통과했다. 다른 OS·Python에서 동일 동작을 검증했다고 표시하지 않는다.

## 실제 실행 결과

| 검사 | 결과와 범위 |
| --- | --- |
| unittest discover | 35개 통과, 실패·skip 0. 문서·청크·모델 signature·BM25/RRF/MMR·인가·수정/삭제·인용·타입·거절·API·HTML·PDF |
| 실제 localhost Uvicorn | 인증·reader 검색·admin 교체·삭제 후 거절·비인가 자료 제외·SSE·UI HTTP 응답 확인 |
| CLI | index·query·evaluate·지표 계산 데모 정상 실행 |
| 실제 embedding | FastEmbed 다국어 ONNX로 7문서 색인, dev/test 각 4질문에서 BM25/dense/hybrid 비교 |
| 실제 리랭커 | 다국어 BGE int8 모델로 한국어 질문 1건의 후보 재정렬. 휴가 문서 1위 |
| 실제 생성 | embedding+reranker+Ollama qwen3.5:4b를 연결, 가상 휴가 질문에 15일·원문 인용 반환 |
| 프레임워크 | LangChain·LlamaIndex retriever 각 5결과, 비인가 자료 제외. 프레임워크 LLM 호출은 미실행 |
| PDF | 테스트가 직접 만든 텍스트 PDF와 빈 페이지 구분. OCR은 미실행 |

API TestClient만으로 실제 소켓 실행을 주장하지 않았으며 별도 Uvicorn 프로세스에서 HTTP smoke를 수행했다. 초기 샌드박스의 Git/캐시/스레드 실행 제한은 작업 폴더와 허용된 실행 환경으로 해결했다. 비밀정보·실제 사내 문서를 사용하지 않았다.

## 실제 모델과 제한된 관측

Embedding: fastembed:0.9.0:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2:aa0cb6bae80fb522d71afaa6871538139b61fdbe0a46536be7278d5bdec6a5c1

모델 가중치·토크나이저 파일 hash는 neural-results.json의 manifest에 있다. 리랭커 hash는 rerank-results.json에 있다. 가중치는 ZIP과 PR에 넣지 않았다.

Ollama 모델: qwen3.5:4b / digest d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04

실제 요청은 think=false, temperature=0, num_predict=768, num_ctx=4096을 사용했다. 최종 결합 smoke의 관측 소요 시간은 9.316초다. 한 가상 질문의 실행 관측이며 운영 지연·처리량·광범위한 정답률로 일반화하지 않는다.

## 검색 지표

| split | 검색 | answerable 평균 Recall@3 | MRR | nDCG | 전체 split 거절 정확도 |
| --- | --- | --- | --- | --- | --- |
| dev | bm25 | 1.000 | 1.000 | 1.000 | 1.000 |
| dev | dense | 1.000 | 0.750 | 0.815 | 1.000 |
| dev | hybrid | 1.000 | 1.000 | 1.000 | 1.000 |
| test | bm25 | 1.000 | 1.000 | 1.000 | 1.000 |
| test | dense | 1.000 | 1.000 | 1.000 | 1.000 |
| test | hybrid | 1.000 | 1.000 | 1.000 | 1.000 |

저자 작성 가상 8질문이다. dev 4개, test 4개이며 test의 answerable은 2개다. mean_retrieval은 answerable 사례만 집계하고 거절 정확도는 각 split 전체다. 문서 단위 qrels이며 최대 20 후보 청크의 고유 문서 top-k를 평가한다. Precision 분모는 k다. 동일 저자·작은 표본·명시적 어휘 질문의 편향이 있어 실제 사용자 성능을 추정할 수 없다. dense가 dev에서 낮게 나온 관측도 그대로 보존했다.

## 자동 검사와 의미적 한계

인용 검사는 허용 ID·자료형·길이·원문 부분 문자열에 한정한다. 잘못된 주장과 실제 quote가 함께 통과하는 한계를 테스트로 명시했다. 의미적 뒷받침·전체 정답·완전성의 보증이 아니다. 기본 문자 벡터와 발췌는 실제 신경망·생성 결과로 합산하지 않았다.

반환 전 현재 허용 청크를 다시 확인하지만 분산 전체의 원자적 권한 회수 프로토콜은 아니다. 본문에서 보장과 운영 확장을 구분했다.

## 미검증 범위

- 전체 독립 사람·전문가 원고 검수, 다양한 실사용 질문의 LLM 정답·보안 평가.
- 실제 산업 데이터·대규모 동시 부하·지연 분포·운영 비용·고객 SLA.
- OCR·pgvector ANN·외부 DB·클라우드·컨테이너·TLS·운영 인증·장애/백업 복원.
- 자동 HyDE/Multi-hop/대화 상태·전체 Agentic/GraphRAG·멀티모달 추론·파인튜닝·대규모 LLM-as-judge.
- 브라우저 시각·접근성 QA. UI는 HTTP 응답과 코드의 textContent 사용을 확인한 범위다.

## 재현 자료

[검색 결과](neural-results.json) · [LLM 결과](llm-results.json) · [리랭커 결과](rerank-results.json) · [프레임워크](framework-results.json) · [실제 HTTP](http-results.json) · [CLI](cli-results.json) · [패키지](versions.json) · [공식 링크 접근](source-results.json)

examples README의 설치·기본 테스트·모델 선택·프레임워크 명령을 따른다. 모델 캐시·실행 DB·가상환경·실제 비밀정보는 배포에 포함하지 않는다. 코드를 바꾸면 메타데이터·검증 범위·다운로드를 함께 갱신한다.


## 제출 전 검사 요약

[기계 판독 검사 집계](validation-results.json)와 원고·예제 ZIP을 함께 제공한다.


- Python 실행 소스 21개, 본문 Python 블록 8개 문법 검사 통과.
- Markdown 52개, 로컬 링크·앵커 267개, JSON 13개 검사 오류 0건. UI JavaScript 문법도 통과했다.
- 소스는 표준 포맷으로 정리하고 AST 동등성을 확인했으며 정리 후 테스트 35개가 다시 통과했다.
- uv pip check: 설치한 96개 패키지 호환성 통과.
- 논문·공식 URL 65개 중 62개 자동 HTTP 200, 자동 403인 3개는 공식 사이트의 링크를 따라 웹 본문 확인.
- 저장소 validate-books: 기존 4권과 RAG를 포함한 5권 통과. RAG는 40장·9부·다운로드 2개다.
- 두 ZIP의 CRC·압축 해제·소스 일치와 책 ZIP 압축 해제본의 메타데이터를 검사했다. 자기 자신인 ZIP 다운로드 항목은 압축 내부에서 제외했다.

모델 가중치·모델 캐시·실행 DB·var·가상환경·Python 캐시·실제 비밀정보는 ZIP과 PR에 포함하지 않는다. 예제 ZIP에는 검증 문서와 결과 JSON을 함께 넣었다.
