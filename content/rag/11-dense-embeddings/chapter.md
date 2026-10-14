---
title: "11장. 임베딩과 의미 기반 검색"
description: "질문·문서 인코딩 계약과 검색 모델의 학습 목적을 확인한다. 실제 신경망 결과와 문자 벡터 실험을 구분한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 11
part: 3
enableToc: true
---

# 11장. 임베딩과 의미 기반 검색

## 학습 목표

- 질문·문서 인코딩 계약과 검색 모델의 학습 목적을 확인한다.
- 실제 신경망 결과와 문자 벡터 실험을 구분한다.

## 비슷한 의미를 찾는 좌표

질문과 문서가 서로 다른 단어를 사용해도 관련된 내용을 가리킬 수 있다. 학습한 임베딩은 이런 관계를 벡터 공간에 반영하려고 한다. 그러나 비슷한 주제와 질문에 답하는 근거는 다르다. 휴가 정책 전체가 비슷하더라도 특정 예외 조항이 빠지면 답할 수 없다.

질문과 문서에 별도 인코더를 쓰거나 다른 접두어를 요구하는 모델이 있다. 모델 카드의 query·passage 규칙을 확인하고 색인과 질의 경로에 일관되게 적용한다. 임의 접두어를 모든 모델에 붙이는 것도 올바른 범용 규칙이 아니다.

## 직접 실행하는 다국어 모델

예제는 FastEmbed의 다국어 MiniLM ONNX 모델을 선택형 어댑터로 제공한다. 모델 파일과 토크나이저 해시를 signature에 포함하고, 같은 캐시에는 해당 모델만 둔다. 첫 실행은 네트워크 다운로드가 필요하며 모델 가중치는 원고 ZIP에 넣지 않는다.

```python
from ragbook.embedding import FastEmbedder, cosine
embedder = FastEmbedder(cache_dir='model-cache')
vectors = embedder.embed(['연차 휴가 안내', '휴가는 며칠인가요?'])
print(len(vectors[0]), cosine(vectors[0], vectors[1]))
```

이 숫자를 답변 확신도로 사용자에게 표시하지 않는다. 모델과 데이터가 바뀌면 같은 임계값이 유지된다는 보장도 없다. 질의별 관련 문서의 순위와 오검색을 확인한다.

## 차원·입력·정규화

차원이 크면 표현 용량이 늘 수 있지만 저장량·전송·내적 비용도 늘고 항상 품질이 좋아지지는 않는다. 모델이 지원하는 차원 축소나 양자화가 있더라도 별도 평가가 필요하다. 길이 초과 입력을 조용히 잘라내는지 반드시 확인한다.

정규화 벡터의 코사인은 내적으로 계산할 수 있다. 0벡터·NaN·차원 불일치를 처리하고, 질문과 문서에 다른 변환이 적용되지 않게 한다. 예제는 유한 값과 차원을 검사하고 인덱스 모델 signature 불일치를 거부한다.

## 언어와 도메인 실험

한국어 질문·영문 약어·혼합 코드·짧은 질문·긴 설명을 나누어 본다. 다국어라는 표시가 모든 언어·도메인에서 같은 성능이라는 뜻은 아니다. 철자 차이·부정 표현·수치·시점·유사 제품명을 포함한 hard negative로 구별 능력을 확인한다.

실제 작은 dev 관측에서는 BM25의 MRR이 1.0이고 dense는 0.75였다. 이 값은 네 질문의 교육용 결과다. 단어 일치가 강한 자료와 모델 선택의 영향을 보여 주며, 임베딩 모델 전체의 품질 순위로 일반화하지 않는다.

## 실습과 평가

새 neural DB를 만든 후 동일 dev 질문에서 bm25·dense·hybrid를 비교한다. 결과는 `appendices/neural-results.json`에 저장한 실행과 연결한다. 질문별 순위를 먼저 보고 평균을 읽는다.

실행을 재현할 때 모델 이름·파일 해시·FastEmbed 버전·전처리·문서 snapshot을 함께 확인한다. 모델 소개의 벤치마크 수치를 자신의 가상 데이터 결과로 바꾸어 적지 않는다.

## 확인 문제

유사도 높은 문서를 찾았지만 질문의 날짜 조건이 없다. 그 점수만으로 충분한 근거라고 판단할 수 있는가?

[해설](../appendices/answers.md#장-11)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [[2004.04906] Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906)
- [Semantic Search — Sentence Transformers documentation](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)
- [FastEmbed](https://qdrant.github.io/fastembed/)

---

[이전 장](../10-bm25/chapter.md) · [책 목차](../index.md) · [다음 장](../12-ann-index/chapter.md)
