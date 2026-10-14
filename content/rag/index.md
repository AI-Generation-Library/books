---
title: "RAG 완전 정복"
description: "문서 수집·파싱·청킹·임베딩·하이브리드 검색·리랭킹부터 근거 기반 생성·인용·평가·보안·운영까지. 9부 40장과 Python 실습으로 검색 품질을 측정하고 문서 지식 서비스를 완성하는 한국어 기술서."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# RAG 완전 정복

**문서 수집과 검색부터 평가·최적화·서비스 운영까지**

문서 수집·파싱·청킹·임베딩·하이브리드 검색·리랭킹부터 근거 기반 생성·인용·평가·보안·운영까지. 9부 40장과 Python 실습으로 검색 품질을 측정하고 문서 지식 서비스를 완성하는 한국어 기술서.

내 문서를 검색하는 작은 도구에서 시작해, 권한과 문서 갱신을 지키며 근거를 제시하는 지식 서비스로 확장한다. 검색·컨텍스트·생성·인용의 실패를 분리하고, 실제 모델 실행과 평가 기록으로 개선 과정을 확인한다.

**대상 독자:** Python 기본 문법을 아는 입문자와 RAG 품질·운영 문제를 해결하려는 개발자.

**구성:** 9부 40장. 개념 → 내부 원리 → 실습 → 실패 사례 → 평가와 확인 문제. 해설·지표 계산·용어·프레임워크 어댑터·공식 출처를 제공한다.

**실습:** Python 3.12 / SQLite / FastAPI. 기본 문자 벡터·발췌 데모와 실제 다국어 ONNX embedding·reranker·로컬 Ollama LLM을 분리한다. 정확한 패키지·모델·실행 범위는 검증 안내를 따른다.

[읽는 방법과 실습 기준](00-preface.md) · [예제 실행](examples/README.md) · [검증 기록](appendices/verification.md)

## 전체 목차

### 1부. RAG의 기본 원리와 첫 번째 구현

- [01장. RAG는 무엇이고 언제 필요한가](01-why-rag/chapter.md) — 검색·근거 구성·생성을 별도 단계로 설명한다.
- [02장. RAG에 필요한 LLM과 임베딩 기초](02-llm-embedding/chapter.md) — 생성 모델과 검색용 임베딩의 역할을 구분한다.
- [03장. 가장 작은 RAG 파이프라인 만들기](03-minimal-pipeline/chapter.md) — 색인과 질문 흐름을 독립적으로 실행한다.
- [04장. 문제 정의와 기준선 세우기](04-baseline/chapter.md) — 사용자 질문을 평가 가능한 요구사항으로 바꾼다.

### 2부. 문서를 검색 가능한 데이터로 만들기

- [05장. 문서 수집과 데이터 출처 관리](05-ingestion/chapter.md) — 수집 권한과 자료의 사용 범위를 기록한다.
- [06장. PDF·HTML·표·스캔 문서 파싱](06-parsing/chapter.md) — 원문 모양과 추출된 텍스트의 차이를 검사한다.
- [07장. 정규화·중복 제거·문서 버전 관리](07-normalization/chapter.md) — 검색 편의를 위한 변환과 원문 보존을 구분한다.
- [08장. 청킹 전략 설계와 비교](08-chunking/chapter.md) — 검색 단위와 답변에 필요한 문맥 단위를 구분한다.
- [09장. 메타데이터와 문서 식별 체계](09-metadata/chapter.md) — 인용·권한·버전·필터를 위한 필드를 정의한다.

### 3부. 검색의 기본 구조와 하이브리드 검색

- [10장. 키워드 검색과 BM25](10-bm25/chapter.md) — 역색인과 단어 통계로 순위를 만드는 원리를 이해한다.
- [11장. 임베딩과 의미 기반 검색](11-dense-embeddings/chapter.md) — 질문·문서 인코딩 계약과 검색 모델의 학습 목적을 확인한다.
- [12장. 벡터 인덱스의 내부 원리](12-ann-index/chapter.md) — 정확 최근접 검색과 근사 검색의 손실을 구분한다.
- [13장. 벡터 저장소 구성과 검색 조건](13-vector-store/chapter.md) — 저장소의 거리·차원·필터·갱신 계약을 확인한다.
- [14장. 하이브리드 검색과 순위 결합](14-hybrid-rrf/chapter.md) — 서로 다른 검색 점수를 무리하게 직접 더하지 않는다.

### 4부. 검색 품질을 높이는 심화 기법

- [15장. 질의 재작성과 검색 확장](15-query-rewriting/chapter.md) — 원래 질문의 제약을 보존하며 검색어를 확장한다.
- [16장. 리랭킹으로 근거 후보 정밀화하기](16-reranking/chapter.md) — 빠른 후보 검색과 정밀한 재정렬을 분리한다.
- [17장. 문맥을 보존하는 검색 구조](17-context-retrieval/chapter.md) — 검색 단위와 생성에 제공할 근거 단위를 설계한다.
- [18장. 질의 라우팅과 여러 데이터 소스 연결](18-routing/chapter.md) — 문서·SQL·전용 API의 역할을 요구에 맞게 나눈다.
- [19장. 다단계 질문과 Multi-hop Retrieval](19-multi-hop/chapter.md) — 여러 근거를 연결해야 하는 질문을 분해한다.

### 5부. 근거를 활용해 답변 생성하기

- [20장. 컨텍스트 구성과 토큰 예산](20-context-budget/chapter.md) — 검색 후보와 최종 생성 근거를 분리한다.
- [21장. 근거 중심 프롬프트와 답변 정책](21-grounded-prompt/chapter.md) — 지시·질문·문서 데이터를 구분한다.
- [22장. 인용과 답변 검증](22-citations/chapter.md) — 출처 존재·정확한 인용·주장 지지를 구분한다.
- [23장. 대화형 RAG와 메모리](23-conversation/chapter.md) — 생략된 후속 질문을 검색 가능한 질의로 해석한다.

### 6부. RAG를 측정하고 개선하기

- [24장. 평가 데이터셋 만들기](24-evaluation-data/chapter.md) — 질문·관련 문서·정답·거절 기대값을 구분한다.
- [25장. 검색 품질 평가](25-retrieval-evaluation/chapter.md) — Precision·Recall·MRR·nDCG를 직접 계산한다.
- [26장. 답변과 인용 품질 평가](26-answer-evaluation/chapter.md) — 정확성·충실성·완전성·관련성을 따로 평가한다.
- [27장. LLM 평가자와 사람 평가 설계](27-llm-judge/chapter.md) — 평가 기준표와 입력을 재현 가능하게 고정한다.
- [28장. 실험 설계와 실패 원인 분석](28-experiments/chapter.md) — 변수·snapshot·평가셋을 고정해 개선 원인을 찾는다.

### 7부. 서비스 구현과 운영

- [29장. RAG API와 사용자 인터페이스](29-api-ui/chapter.md) — 검색·질문·문서 관리 API의 경계를 정한다.
- [30장. 문서 갱신과 인덱스 수명 관리](30-index-lifecycle/chapter.md) — 문서 수정·삭제·권한 변경을 파생 데이터에 반영한다.
- [31장. 접근 권한과 RAG 보안](31-security/chapter.md) — 검색·리랭킹·생성·로그에 같은 권한 경계를 적용한다.
- [32장. 성능과 비용 최적화](32-latency-cost/chapter.md) — 색인·질의·평가 비용을 따로 집계한다.
- [33장. 관측·배포·품질 모니터링](33-observability-deployment/chapter.md) — 운영 장애와 품질 변화를 다른 신호로 관찰한다.

### 8부. 고급 RAG 아키텍처

- [34장. Agentic RAG](34-agentic-rag/chapter.md) — 고정 흐름과 동적인 검색 도구 선택을 비교한다.
- [35장. GraphRAG와 지식 그래프](35-graph-rag/chapter.md) — 개체·관계·원문 근거를 연결하는 구조를 이해한다.
- [36장. 멀티모달 RAG](36-multimodal/chapter.md) — 텍스트만으로 잃는 표·그림·레이아웃을 구분한다.
- [37장. 도메인 특화와 검색 모델 개선](37-domain-adaptation/chapter.md) — 데이터·검색·모델 중 병목에 맞는 개선을 선택한다.

### 9부. 종합 프로젝트: 근거를 제시하는 문서 지식 서비스

- [38장. 요구사항·문서·평가셋 설계](38-capstone-design/chapter.md) — 종합 서비스의 데이터·권한·품질 계약을 작성한다.
- [39장. 수집부터 답변까지 전체 파이프라인 구현](39-capstone-pipeline/chapter.md) — 색인·검색·리랭킹·생성·API를 같은 계약으로 연결한다.
- [40장. 품질 개선부터 배포와 운영 검증까지](40-capstone-validation/chapter.md) — 실제로 실행한 검사와 아직 확인하지 않은 범위를 남긴다.

## 부록과 실습 자료

- [학습 경로](appendices/learning-roadmap.md)
- [핵심 용어](appendices/glossary.md)
- [확인 문제 해설](appendices/answers.md)
- [지표 계산과 평가 규칙](appendices/metrics.md)
- [프레임워크 연결](appendices/frameworks.md)
- [실패 진단](appendices/troubleshooting.md)
- [논문·공식 참고 자료](appendices/references.md)
- [생성과 검증 기록](appendices/verification.md)
- [작성 입력과 승인 목차](generation-input.json)
- [종합 프로젝트의 구현 범위](examples/ARCHITECTURE.md)

## 다운로드

- [책 원고와 실행 예제 ZIP](downloads/rag-book.zip)
- [실행 예제 ZIP](downloads/rag-examples.zip)

## 생성과 검수

2026-10-14 사용자 승인 목차로 Codex가 직접 집필했다. 정확한 저작 모델은 확인하지 못해 null로 기록했다. 전체 독립 사람 검수는 미수행이다. 실제 모델 실행은 작은 가상 데이터의 제한된 검증이며 실서비스 품질·보안·운영 인증으로 일반화하지 않는다. 인용의 원문 존재 검사와 의미적 뒷받침 평가도 구분한다.

원고·창작 예제·가상 데이터는 books 저장소의 CC0 조건을 따른다. 제삼자 패키지와 모델은 각 라이선스를 따르며 모델 가중치·실행 DB·가상환경은 배포에 넣지 않는다.
