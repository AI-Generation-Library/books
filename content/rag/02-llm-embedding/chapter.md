---
title: "02장. RAG에 필요한 LLM과 임베딩 기초"
description: "생성 모델과 검색용 임베딩의 역할을 구분한다. 토큰·벡터·유사도를 올바른 단위로 해석한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 2
part: 1
enableToc: true
---

# 02장. RAG에 필요한 LLM과 임베딩 기초

## 학습 목표

- 생성 모델과 검색용 임베딩의 역할을 구분한다.
- 토큰·벡터·유사도를 올바른 단위로 해석한다.

## 서로 다른 두 모델 역할

생성 모델은 주어진 문맥 뒤에 이어질 텍스트를 만든다. 임베딩 모델은 질문이나 문서를 숫자 벡터로 바꾸어 가까운 자료를 찾는 데 사용한다. 같은 회사의 모델이거나 둘 다 언어 모델에서 출발했다고 서로 교체 가능한 것은 아니다. 반환 차원·입력 길이·전처리·질문과 문서의 인코딩 규칙이 다를 수 있다.

검색 모델은 학습 목표에 영향을 받는다. 문장 유사도 모델, 질문-답변 검색 모델, 코드 검색 모델은 잘 구분하는 관계가 다르다. 한국어·영어 혼합 자료와 제품 코드가 많은 자료에서도 결과가 달라진다. 모델 소개의 단일 점수보다 자신의 질문과 관련 문서로 비교한다.

## 토큰은 문자 수가 아니다

토크나이저는 문자열을 모델이 사용하는 단위로 분해한다. 한글 한 글자가 한 토큰이라는 보장은 없다. 질문·지시·근거·대화 이력·출력 예약량이 컨텍스트 예산을 함께 차지한다. 임베딩 모델의 입력 길이와 생성 모델의 컨텍스트 길이는 별개다.

예제의 기본 청킹과 컨텍스트 예산은 재현이 쉬운 **문자 수**를 사용한다. 이것을 토큰 제한이라고 부르지 않는다. 실제 모델에서는 그 모델의 토크나이저로 다시 계산하고 초과·절단 정책을 명시해야 한다. 긴 청크가 조용히 잘리면 끝부분 근거가 검색에 반영되지 않을 수 있다.

## 유사도는 정답 확률이 아니다

두 벡터의 코사인 유사도는 방향의 유사성을 계산한다. 벡터를 단위 길이로 정규화하면 내적으로 같은 값을 구할 수 있다. 하지만 0.8이라는 값이 정답일 확률 80%라는 뜻은 아니다. 모델·거리 함수·문서 분포가 바뀌면 점수 범위도 달라진다.

```python
from ragbook.embedding import cosine, unit
assert round(cosine([1, 0], [1, 0]), 6) == 1
assert cosine([1, 0], [0, 1]) == 0
```

정규화는 수학적 비교 방식을 맞추는 작업이지 모든 모델을 같은 의미 공간으로 만드는 작업이 아니다. 서로 다른 모델의 같은 차원 벡터를 한 인덱스에 섞으면 안 된다.

## 재현 가능한 모델 기록

모델 이름뿐 아니라 버전·가중치·토크나이저·접두어·정규화·차원을 함께 기록한다. 예제의 실제 임베딩은 FastEmbed와 다국어 MiniLM ONNX 가중치를 사용하고 파일 해시를 색인 signature에 반영한다. 모델 파일을 ZIP이나 PR에 넣지 않는다.

기본 CharacterEmbedder는 문자 2-gram을 해시한 결정적 벡터다. 코사인·색인·융합을 학습하기 위한 장치이며 학습된 의미 임베딩이 아니다. 실제 모델 평가와 구분해야 검색 결과를 정직하게 해석할 수 있다.

## 실습과 평가

기본 모드로 색인한 DB를 `--embedding neural`로 열면 signature 불일치로 거부되어야 한다. 신경망 실습에는 새 DB 경로를 사용한다.

`python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 index`를 실행하면 처음에는 공개 모델 파일을 내려받는다. 이후 검색 명령에도 같은 embedding·DB·cache 설정을 사용한다. 실제 실행 모델과 해시는 검증 기록에 있다.

## 확인 문제

벡터 차원이 둘 다 384라면 서로 다른 모델의 문서 벡터와 질문 벡터를 섞어 검색해도 되는가?

[해설](../appendices/answers.md#장-02)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Quickstart — Sentence Transformers documentation](https://www.sbert.net/docs/quickstart.html)
- [Supported Models - FastEmbed](https://qdrant.github.io/fastembed/examples/Supported_Models/)
- [sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 · Hugging Face](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)

---

[이전 장](../01-why-rag/chapter.md) · [책 목차](../index.md) · [다음 장](../03-minimal-pipeline/chapter.md)
