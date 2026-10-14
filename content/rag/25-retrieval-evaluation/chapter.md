---
title: "25장. 검색 품질 평가"
description: "Precision·Recall·MRR·nDCG를 직접 계산한다. 관련성 단위·분모·빈 정답의 정책을 명시한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 25
part: 6
enableToc: true
---

# 25장. 검색 품질 평가

## 학습 목표

- Precision·Recall·MRR·nDCG를 직접 계산한다.
- 관련성 단위·분모·빈 정답의 정책을 명시한다.

## 서로 다른 질문을 하는 지표

Precision@k는 상위 k개 중 관련한 항목의 비율이다. Recall@k는 전체 관련 항목 중 상위 k에서 찾은 비율이다. MRR은 첫 관련 항목의 순위 역수를 질문별로 평균한다. nDCG는 관련성 등급과 높은 순위의 가치를 반영해 이상적인 순위와 비교한다.

```text
관련 문서: A(등급2), B(등급1)
검색 순위: X, A, B / k=3
Precision=2/3, Recall=2/2, RR=1/2
DCG=3/log2(3) + 1/log2(4)
IDCG=3/log2(2) + 1/log2(3), nDCG=DCG/IDCG
```

예제 metrics.py는 이 값을 테스트로 검증한다. 같은 ID가 반복되어도 여러 관련 항목으로 세지 않는다. 구현의 gain 함수는 2^grade-1이다. 다른 평가 도구와 비교할 때 할인·gain·중복·빈 라벨 처리가 같은지 확인한다.

## k와 평가 단위

문서 단위 qrels라면 중복 청크를 문서 ID로 합친 뒤 순위를 평가한다. 예제 평가는 최대 20개 후보 청크에서 고유 문서를 뽑아 상위 k개를 계산한다. 생성에는 별도 k개 청크를 넣으므로 검색 지표가 생성 근거의 모든 성질을 대신하지 않는다.

Precision 분모는 이 구현에서 k다. 반환 결과가 k보다 적더라도 분모를 자동으로 줄이지 않는다. 그래서 관련 문서가 하나인 질문의 P@3은 최고 순위가 맞아도 1/3일 수 있다. 낮은 숫자만 보고 검색이 실패했다고 결론 내리지 않는다.

## 답이 없는 질문

관련 문서가 없는 질문에서 Recall과 nDCG는 분모를 정의하기 어렵다. 예제는 null로 표현하고 답변 가능한 질문의 순위 지표 평균에서 거절 질문을 제외한다. 별도로 should_abstain과 실제 거절을 비교한다. 답이 없는 질문을 강제로 0이나 1 Recall로 바꿔 평균을 꾸미지 않는다.

## 지표의 한계

MRR은 첫 근거 뒤의 누락을 잘 드러내지 못한다. 여러 근거가 필요한 질문은 Recall과 사실별 충분성도 봐야 한다. qrels 자체가 불완전하면 라벨에 없지만 유용한 문서가 오답처럼 계산될 수 있다. 새로운 관련 문서를 검토하고 평가셋 버전을 올린다.

검색 top-k를 늘리면 Recall이 좋아져도 지연·리랭킹 비용·생성 잡음이 늘 수 있다. 수치의 방향 하나만 최적화하지 말고 목표와 예산을 함께 둔다.

## 실습과 평가

tests/test_core.py의 known_values 테스트에서 nDCG를 손으로 계산한다. 빈 검색·빈 qrels·중복 ID·k=0의 동작도 확인한다.

실제 모델 결과는 neural-results.json을 읽는다. 평균은 answerable 사례만, 거절 정확도는 해당 평가 split 전체라는 집계 정책을 확인한다.

## 확인 문제

첫 관련 문서를 1위로 찾았으니 여러 문서가 필요한 질문의 근거도 모두 확보했다고 볼 수 있는가?

[해설](../appendices/answers.md#장-25)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Evaluation of ranked retrieval results](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)
- [Develop a RAG Solution on Azure - Information-Retrieval Phase - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-information-retrieval)

---

[이전 장](../24-evaluation-data/chapter.md) · [책 목차](../index.md) · [다음 장](../26-answer-evaluation/chapter.md)
