---
title: "06장. 데이터 집계와 결합하기"
description: "그룹별 집계·병합·파생변수의 단위를 확인한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 6
part: 2
---

# 06장. 데이터 집계와 결합하기

집계는 원래 행을 어떤 단위로 묶는 작업이고, 결합은 표 사이의 관계를 연결하는 작업이다. 결과의 행 수와 단위를 확인하지 않으면 한 고객이 여러 번 복제되거나 타깃과 설명 변수가 어긋날 수 있다.

## 1. 질문을 집계 단위로 바꾸기

계약 유형별 평균 요금은 계약 유형이 그룹이고 요금이 요약 대상이다. 고객 수는 행 수인지 ID의 고유 개수인지 정한다. `count`는 결측이 아닌 값의 수이며 `size`는 그룹 행 수다. 둘이 다른 것은 오류가 아니라 정의의 차이일 수 있다.

```python
import pandas as pd
from lab import ROOT, load_customers

df = load_customers()
summary = df.groupby("contract_type", dropna=False).agg(
    customers=("customer_id", "size"),
    mean_fee=("monthly_fee", "mean"),
    churn_rate=("churn", "mean"),
)
lookup = pd.read_csv(ROOT / "data/regions.csv")
joined = df.merge(lookup, on="region", how="left", validate="many_to_one")
assert len(joined) == len(df)
assert joined["zone"].notna().all()
ranked = df.sort_values("tenure_months", ascending=False)
assert ranked["tenure_months"].is_monotonic_decreasing
print(summary)
```

이진 타깃 0·1의 평균은 해당 표본의 1 비율이다. 표본 구성과 결측 처리, 그룹별 수를 함께 본다. 가상 데이터에서 계산한 차이를 실제 고객 행동의 인과관계로 해석하지 않는다.

## 2. 결합 키와 관계

고객 표에 지역 설명을 붙일 때 지역 사전은 지역별 한 행이어야 한다. 사전의 키가 중복되면 고객 행이 늘어날 수 있다. `validate='many_to_one'`처럼 예상 관계를 검사한다. `left` 결합은 왼쪽 행을 유지하고 찾지 못한 값은 결측으로 남긴다.

문제에서 `inner` 결합을 요구했다면 누락 행이 생길 수 있다. 방식과 행 수를 대조하고, 병합 후 같은 이름의 열에 접미사가 붙었는지 확인한다. 이름만 비슷한 열을 자동으로 키로 삼지 않는다.

## 3. 파생변수의 계산 시점

필요한 변수는 이미 가진 정보로 계산한다. 요금과 이용량의 비율에는 0 분모와 결측 처리 기준이 필요하다. 이탈 이후에 생기는 정보나 미래의 실제값을 사용하면 예측 시점에 알 수 없는 자료가 들어간다.

그룹별 평균으로 새 특성을 만들 때 전체 데이터의 타깃 평균을 그대로 붙이면 누수가 생길 수 있다. 단순 탐색용 집계와 모델 입력용 변환을 구분한다. 이 책의 기본 경로에서는 복잡한 타깃 인코딩을 사용하지 않는다.

## 4. 인덱스와 정렬

`groupby` 결과는 그룹 값이 인덱스가 될 수 있다. 파일에 저장하거나 다시 결합할 때는 `reset_index()`의 필요를 확인한다. 정렬은 행 순서를 바꾸므로 별도로 분리해 둔 타깃의 순서를 임의로 유지하면 안 된다.

원래 자료를 여러 표로 나누었다면 고유 키로 정합성을 확인한다. `concat`으로 행을 붙이는 것과 키로 `merge`하는 것은 다르다. 행 수, 키 고유성과 필요한 열이 결과에 있는지 확인한다.

## 연습과 해설

1. 그룹마다 결측을 포함한 고객 수가 필요하다면? **해설:** 행 단위가 고객 한 명임을 확인한 뒤 `size`를 사용한다. 중복 고객이면 고유 ID 수를 검토한다.
2. 결합 후 600행이 900행으로 늘었다면? **해설:** 오른쪽 키의 중복과 관계, 결합 조건을 먼저 확인한다.

다음 장에서는 집계 전후 자료의 품질을 점검한다. 참고: [pandas 병합 공식 안내](https://pandas.pydata.org/docs/user_guide/merging.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 05장 pandas로 데이터 불러오고 선택하기](../05-chapter/chapter.md) · [07장 데이터 구성과 품질 점검하기 →](../07-chapter/chapter.md)
