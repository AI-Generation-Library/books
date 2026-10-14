---
title: "24장. 평가 데이터셋 만들기"
description: "질문·관련 문서·정답·거절 기대값을 구분한다. 누출과 저자 편향을 줄이는 분할을 설계한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 24
part: 6
enableToc: true
---

# 24장. 평가 데이터셋 만들기

## 학습 목표

- 질문·관련 문서·정답·거절 기대값을 구분한다.
- 누출과 저자 편향을 줄이는 분할을 설계한다.

## 질문 하나에 필요한 필드

검색 평가는 질문과 qrels가 필요하다. 답변 정확성 평가는 정답 사실·허용 표현·필요 조건이 추가된다. 거절 평가는 답할 수 없는 이유와 기대 동작이 필요하다. 한 개의 expected 문자열이 모든 평가를 대신하지는 않는다.

```json
{
  "id": "q1",
  "question": "연차 휴가는 연간 며칠인가요?",
  "qrels": {"leave": 2},
  "should_abstain": false,
  "split": "dev"
}
```

이 예제의 qrels는 문서 ID 단위, 관련성 등급 2다. 청크 ID 정답으로 바꾸면 청킹 변경 때 라벨 관리도 바뀐다. 문서가 관련되었다고 그 문서의 모든 청크가 답변 근거는 아니라는 점을 유지한다.

## 질문의 종류

정확한 용어·재표현·오탈자·수치·날짜·예외·여러 근거·상충 문서·오래된 자료·답이 없는 질문을 포함한다. 권한 때문에 답할 수 없는 질문은 원문이 존재하지 않는 질문과 별도 이유지만 공개 응답에서는 존재를 드러내지 않을 수 있다.

실패 비용이 높은 유형은 개별 지표로 본다. 흔한 질문이 많아 평균이 높아도 권한 누출이나 오래된 규정 사용이 가려질 수 있다. 실제 분포와 균형 잡힌 진단셋을 서로 다른 목적으로 유지할 수 있다.

## 합성 질문과 사람 검수

문서에서 LLM으로 질문을 만들면 초기 범위를 넓히기 쉽다. 하지만 원문의 표현을 그대로 사용하는 쉬운 질문과 정답 오류가 생길 수 있다. 생성 모델이 자기 답변을 평가하면 편향도 공유할 수 있다. 실제 사용자 질문과 전문가의 필요 사실 검토로 보완한다.

이 책의 8개 질문은 저자가 직접 만든 가상 fixture이며 독립 사람 평가가 아니다. dev 4개, test 4개를 제공하지만 같은 저자·자료·작은 표본이라는 한계를 명시한다. 실제 고객 성능이나 신뢰 구간을 이 수치로 추정하지 않는다.

## 누출과 분할

거의 같은 질문을 문장만 바꿔 train·test에 나누면 독립성이 약하다. 문서군·주제·시간·사용자 흐름을 기준으로 분리하고 중복을 확인한다. test의 정답을 보며 모델·프롬프트·임계값을 고르면 그 셋은 더 이상 최종 독립 평가가 아니다.

개정 문서를 평가할 때는 질문 시점과 문서 revision을 고정한다. 정답은 이전 버전인데 인덱스는 최신판이면 모델 오류처럼 보일 수 있다. 권한 principal과 색인 snapshot도 평가 입력이다.

## 실습과 평가

data/evaluation.json의 답변 가능 질문과 거절 질문을 나눈다. 토성 질문은 자료 밖, 비공개 코드는 reader 권한 밖이라는 차이를 기록한다.

현재 qrels는 문서 단위다. 더 세밀한 실험을 위해 필요한 원문 구간과 정답 사실을 추가하고 변경 이력·검토자·라벨 기준을 함께 남긴다.

## 확인 문제

합성 질문 1000개가 있으면 사람 검수한 실제 사용자 질문을 완전히 대체할 수 있는가?

[해설](../appendices/answers.md#장-24)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [Evaluating | Developer Documentation](https://developers.llamaindex.ai/python/framework/module_guides/evaluating/)
- [Testset Generation for RAG - Ragas](https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/)

---

[이전 장](../23-conversation/chapter.md) · [책 목차](../index.md) · [다음 장](../25-retrieval-evaluation/chapter.md)
