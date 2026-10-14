---
title: "15장. 질의 재작성과 검색 확장"
description: "원래 질문의 제약을 보존하며 검색어를 확장한다. 생성한 검색 보조 텍스트를 사실 근거와 구분한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 15
part: 4
enableToc: true
---

# 15장. 질의 재작성과 검색 확장

## 학습 목표

- 원래 질문의 제약을 보존하며 검색어를 확장한다.
- 생성한 검색 보조 텍스트를 사실 근거와 구분한다.

## 질문과 문서의 표현 차이

사용자는 약어·오탈자·대화 속 생략 표현으로 묻는다. 문서는 공식 용어를 사용할 수 있다. 재작성은 이런 차이를 줄이기 위해 질문을 검색에 적합한 형태로 바꾸는 단계다. 원문의 수치·시점·대상·부정 조건을 잃지 않아야 한다.

간단한 사전 규칙은 투명하고 비용이 작다. LLM 재작성은 표현을 넓힐 수 있지만 잘못된 제품명과 가정을 추가할 수 있다. 원래 질문도 함께 유지하고 재작성 결과가 없거나 실패하면 기준 검색으로 돌아가는 경로를 둔다.

## Multi-query와 후보 결합

여러 재표현을 만들고 각각 검색한 뒤 중복을 제거하거나 RRF로 합칠 수 있다. 질의 수가 늘면 검색 호출과 생성 비용도 늘고 비슷한 후보만 반복될 수 있다. 질문 유형별로 추가 호출이 실제 Recall을 개선하는지 측정한다.

```python
def expand_query(question, dictionary):
    alternatives = [question]
    for short, full in dictionary.items():
        if short in question:
            alternatives.append(question.replace(short, full))
    return list(dict.fromkeys(alternatives))[:3]
```

이 코드는 사전 확장의 개념 조각이다. 본문 예제 서비스는 질의를 자동으로 무한 확장하지 않는다. 어떤 확장을 실제 적용했는지 실행 기록에 남긴다.

## HyDE의 역할

HyDE는 질문에 대한 가상의 답변 문서를 생성하고 이를 인코딩해 관련 문서를 찾는 접근이다. 가상 문서에는 사실이 틀릴 수 있다. 검색을 돕는 중간 표현으로 사용하고 사용자에게 검증된 근거로 인용하지 않는다. 최종 답변은 실제로 검색한 원문을 바탕으로 만든다.

질문이 모호하면 가상 문서가 하나의 해석으로 편향될 수 있다. 특히 고유명사·날짜·숫자가 생성되면 원래 질문과 다른 자료로 검색이 이동할 수 있다. 원 질문 기반 검색과 결합하거나 확인 질문을 하는 정책을 비교한다.

## 평가할 실패

재작성 전후 관련 문서 순위·검색된 고유 ID·질문 조건 보존을 확인한다. 평균이 좋아져도 특정 약어의 잘못된 확장으로 큰 오류가 생길 수 있다. 질의 생성 모델·프롬프트·버전과 호출 수를 기록하고 비용·지연도 합산한다.

대화 이력이나 사용자 질문에 개인정보가 있으면 재작성 모델에도 전달된다. 외부 전송 경계와 보관 정책을 검토한다. 재작성은 인증된 검색 범위를 넓히는 권한이 아니다.

## 실습과 평가

가상 문서의 정산을 비용 처리로 바꾼 질문, 약어와 오탈자가 있는 질문을 dev에 추가한다. 사전 확장과 원 질문 기준선을 비교하고 실패 사례를 따로 보관한다.

HyDE·LLM Multi-query는 이 책의 설계 설명이며 종합 서비스의 기본 경로에 자동 실행되는 기능은 아니다. 실행하지 않은 확장을 검증 완료로 기록하지 않는다.

## 확인 문제

HyDE가 만든 가상 답변이 그럴듯하다. 그 문장을 최종 근거로 인용해도 되는가?

[해설](../appendices/answers.md#장-15)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [[2212.10496] Precise Zero-Shot Dense Retrieval without Relevance Labels](https://arxiv.org/abs/2212.10496)
- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)

---

[이전 장](../14-hybrid-rrf/chapter.md) · [책 목차](../index.md) · [다음 장](../16-reranking/chapter.md)
