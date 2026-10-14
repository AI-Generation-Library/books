---
title: "지표 계산과 평가 규칙"
description: "손계산·집계·빈 라벨 정책을 고정합니다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# 지표 계산과 평가 규칙

관련 문서 A(등급 2)·B(등급 1), 검색 X·A·A·B, k=3일 때 중복 제거 후 X·A·B다. Precision=2/3, Recall=1, RR=1/2다. gain=2^grade-1과 log2(rank+1) 할인으로 nDCG를 계산한다.

```python
from ragbook.metrics import retrieval_metrics
print(retrieval_metrics(['X','A','A','B'], {'A':2,'B':1}, 3))
```

## 예제의 집계 계약

- qrels는 문서 ID 단위다. 최대 20개 후보 청크에서 고유 문서 순위를 얻어 상위 k를 평가한다.
- Precision 분모는 k다. 관련 문서가 1개면 P@3이 1/3이어도 1위를 맞힐 수 있다.
- qrels가 비면 Recall·nDCG는 null이다. mean_retrieval은 answerable 사례만 집계한다.
- abstention_accuracy는 해당 split 전체의 expected 거절 여부와 비교한다.
- 생성의 의미적 정확성·전체 인용 충실성·사람 점수는 이 지표에 포함하지 않는다.

dev/test는 각각 4질문이고 같은 저자가 만든 작은 fixture다. test에는 answerable 2개와 거절 2개가 있다. 이 숫자로 실서비스 성능이나 신뢰 구간을 일반화하지 않는다.

실제 신경망 dev MRR은 BM25 1.0, dense 0.75, hybrid 1.0이었다. 질문별 결과와 모델 signature는 neural-results.json을 따른다. 평균만으로 어떤 기법이 필수인지 결론 내리지 않는다.
