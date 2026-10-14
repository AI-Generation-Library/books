---
title: "38장. 요구사항·문서·평가셋 설계"
description: "종합 서비스의 데이터·권한·품질 계약을 작성한다. 학습용 범위와 운영 확장을 분리한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 38
part: 9
enableToc: true
---

# 38장. 요구사항·문서·평가셋 설계

## 학습 목표

- 종합 서비스의 데이터·권한·품질 계약을 작성한다.
- 학습용 범위와 운영 확장을 분리한다.

## 완성할 서비스

가상 회사 문서를 색인하고 질문에 근거와 함께 답하는 지식 서비스다. 독자는 공개 역할 문서만 검색하고 관리자는 같은 tenant의 문서를 수정·삭제한다. API·화면·CLI·평가 명령을 제공한다. 수치와 규정은 교육용 창작 자료이며 실제 법률이나 회사 규정이 아니다.

데이터는 공개 역할 문서 5개, 관리자 전용 1개, 다른 tenant 1개다. 평가 질문은 dev 4개·test 4개다. 이 작은 구성은 권한·갱신·거절·평가 단위를 재현하기 위한 fixture이지 실제 지식 서비스의 규모와 사용자 품질을 대표하지 않는다.

## 불변식

| 조건 | 실제 확인할 결과 |
| --- | --- |
| 비인가 문서 | 검색·리랭커·프롬프트 후보에서 제외 |
| 개정 | 이전 청크를 새 청크로 원자적 교체 |
| 삭제 | 문서와 청크 제거, 이후 답변에서 제외 |
| 생성 중 변경 | context_changed로 이전 근거 답변 차단 |
| 위조 인용 | 없는 ID·quote·잘못된 타입 거부 |
| 모델 혼합 | embedding signature·차원 불일치 거부 |
| 모델 실패 | 안전한 오류·기한·비밀정보 미출력 |

보안·데이터 불변식과 검색 품질을 분리한다. 검색 Recall이 높아도 타인 자료가 나오면 실패다. 인용 형식 검사가 통과해도 의미적으로 틀린 주장이 있을 수 있음을 테스트와 응답에 명시한다.

## 구현과 모드

SQLite와 표준 라이브러리 검색으로 먼저 파이프라인을 읽는다. CharacterEmbedder와 ExtractiveGenerator는 오프라인 데모다. 실제 모델 모드는 FastEmbed 다국어 embedding·선택형 cross-encoder·Ollama 생성기를 연결한다. 프레임워크 어댑터는 같은 권한 검색 함수를 감싼다.

이 설계는 벤더 계정·유료 API 키 없이 로컬에서 핵심 원리와 실제 모델을 시험하게 한다. 모델 다운로드와 로컬 계산 자원은 필요하다. 로컬 모델이 없는 독자는 발췌 모드로 기능 테스트를 재현할 수 있다.

## 완료 기준과 한계

기본 테스트·모델 연결 smoke·검색 지표 계산·권한/삭제 검증·원고 메타데이터·링크·ZIP을 확인한다. 실제 모델의 작은 실험은 광범위한 품질 인증으로 쓰지 않는다. OCR·pgvector·GraphRAG·Agentic·멀티모달·파인튜닝·공개 클라우드·전체 사람 검수는 별도 범위로 기록한다.

향후 규모를 늘릴 때는 인증 제공자·요청 바이트 제한·분산 실행·비밀 관리·백업 복원·업무 평가셋을 추가한다. 학습용 기본값을 그대로 공개 서비스로 올리는 배포 가이드가 아니다.

## 실습과 평가

예제 README를 읽고 기본 색인과 query를 실행한다. ARCHITECTURE.md에서 구현된 부분과 확장 항목을 비교한다. tests의 각 조건이 위 표와 어떻게 대응하는지 표시한다.

평가 질문의 split과 qrels를 확인하고, 실제 사용자 도입을 위한 추가 질문 유형과 라벨 검토 계획을 작성한다.

## 확인 문제

발췌 데모 테스트가 통과했으니 실제 LLM의 다양한 한국어 답변 품질도 검증되었다고 기록해도 되는가?

[해설](../appendices/answers.md#장-38)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [unittest — Unit testing framework — Python 3.15.0 documentation](https://docs.python.org/3/library/unittest.html)
- [Generate a chat message - Ollama](https://docs.ollama.com/api/chat)

---

[이전 장](../37-domain-adaptation/chapter.md) · [책 목차](../index.md) · [다음 장](../39-capstone-pipeline/chapter.md)
