---
title: "16장. 리랭킹으로 근거 후보 정밀화하기"
description: "빠른 후보 검색과 정밀한 재정렬을 분리한다. 리랭커의 입력 범위·점수·비용을 검증한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 16
part: 4
enableToc: true
---

# 16장. 리랭킹으로 근거 후보 정밀화하기

## 학습 목표

- 빠른 후보 검색과 정밀한 재정렬을 분리한다.
- 리랭커의 입력 범위·점수·비용을 검증한다.

## 후보를 넓게 찾고 다시 비교한다

bi-encoder는 질문과 문서를 따로 인코딩해 많은 문서를 빠르게 비교하기 좋다. cross-encoder는 질문과 후보를 함께 읽고 관련성을 점수화하므로 개별 후보의 세부 관계를 더 정밀하게 판단할 수 있다. 대신 후보마다 추론 비용이 든다.

리랭커는 후보 안에서 순서를 바꾼다. 검색 단계가 관련 문서를 전혀 찾지 못했다면 리랭킹만으로 그 문서를 새로 만들 수 없다. 먼저 후보 Recall을 확인하고, 그다음 상위 순위와 최종 답변의 이득을 측정한다.

## 실제 어댑터

선택형 FastCrossEncoder는 BAAI의 다국어 리랭커 int8 ONNX 모델을 사용한다. 최초 실행에는 별도 모델 다운로드가 필요하다. CLI의 --rerank는 후보를 최대 20개 모아 재정렬하고 limit만큼 반환한다. 권한 필터는 리랭킹보다 먼저 적용한다.

FastEmbed 0.9의 rerank 반환값은 입력 후보 순서의 점수다. 정렬된 객체 목록이라고 가정하면 다른 문서에 점수를 붙이는 버그가 생긴다. 예제는 개수·유한 값을 검사한 뒤 입력과 zip하고 내림차순 정렬한다. 라이브러리 이름이 같아도 버전별 인터페이스를 확인해야 한다.

## 점수의 의미

실제 한국어 한 질문에서 휴가 문서는 약 1.62, 나머지 후보는 음수 점수였다. 이 값은 보정된 정답 확률이 아니다. 모델·질문·길이에 따라 달라지며 그 수치 하나를 모든 질문의 거절 임계값으로 정하지 않는다.

문서가 길면 리랭커의 입력에서 중요한 구간이 잘릴 수 있다. 질문·문서 길이·최대 토큰·추론 batch를 기록한다. 겹치는 청크를 많이 보내면 같은 내용에 반복 비용을 쓸 수 있어 중복·문서별 후보 정책도 함께 본다.

## 다른 재정렬 방식

LLM으로 후보를 평가하거나 pairwise/listwise 순위를 만들 수도 있지만 비용·출력 파싱·순서 편향·프롬프트 주입을 검증해야 한다. ColBERT 같은 late interaction은 여러 토큰 표현을 활용하는 별도 접근이다. 모든 정밀 검색을 같은 cross-encoder라는 이름으로 섞지 않는다.

리랭커를 추가하면 추가 지연과 모델 수명 관리가 생긴다. 정상 질문 하나의 순위 개선을 전체 평가 결과로 주장하지 않는다. 이번 검증은 실제 한국어 한 질문의 재정렬 실행과 권한 후보 테스트를 포함하고 대규모 품질 평가는 포함하지 않는다.

## 실습과 평가

`python -m ragbook.cli --rerank query "연차 휴가는 연간 며칠인가요?"`로 선택형 리랭커를 실행한다. 기본 문자 검색과 결합한 실행도 가능하며 신경망 검색과 비교할 때 같은 DB·모델 설정을 유지한다.

리랭커에 관리자 전용 후보가 들어가지 않는 테스트를 읽는다. 성능 실험은 후보 수·추론 길이·지연과 MRR/nDCG를 함께 기록한다.

## 확인 문제

리랭커가 아주 좋아도 후보 20개에 정답 근거가 하나도 없다면 해결할 수 있는가?

[해설](../appendices/answers.md#장-16)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [[1910.14424] Multi-Stage Document Ranking with BERT](https://arxiv.org/abs/1910.14424)
- [[2004.12832] ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT](https://arxiv.org/abs/2004.12832)
- [Supported Models - FastEmbed](https://qdrant.github.io/fastembed/examples/Supported_Models/)
- [BAAI/bge-reranker-v2-m3 · Hugging Face](https://huggingface.co/BAAI/bge-reranker-v2-m3)

---

[이전 장](../15-query-rewriting/chapter.md) · [책 목차](../index.md) · [다음 장](../17-context-retrieval/chapter.md)
