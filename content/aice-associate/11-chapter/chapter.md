---
title: "11장. 이상치와 잘못된 데이터 처리하기"
description: "불가능한 값과 드문 정상값을 구분하고 자료형을 변환한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 11
part: 3
---

# 11장. 이상치와 잘못된 데이터 처리하기

이상치는 다른 값과 멀리 떨어져 보이는 관측이다. 입력 오류일 수도 있지만 드문 정상 사례일 수도 있다. 음수 나이 같은 정의 위반과 큰 정상 금액을 같은 이유로 삭제하지 않는다. 처리 기준을 설명할 수 있어야 한다.

## 1. 고정 규칙과 학습한 기준

자료 사전에 요금은 0 이상, 이용 지수는 0~100이라고 정의했다면 그 범위를 벗어난 값은 확인 대상이다. 이런 규칙은 데이터의 평균으로 정한 것이 아니다. 반면 IQR이나 분위수로 기준을 정하면 훈련 자료에서 계산하고 다른 자료에 같은 기준을 적용한다.

```python
import numpy as np
from lab import load_customers, clean_customers, split_task

raw = load_customers()
cleaned = clean_customers(raw)
assert raw.loc[0, "monthly_fee"] == -10
assert np.isnan(cleaned.loc[0, "monthly_fee"])
assert cleaned.loc[2, "monthly_fee"] == 10000
X_train, X_val, X_test, y_train, y_val, y_test = split_task()
q1, q3 = X_train["monthly_fee"].quantile([0.25, 0.75])
iqr = q3-q1
lower, upper = q1-1.5*iqr, q3+1.5*iqr
flag = ~X_train["monthly_fee"].between(lower, upper) & X_train["monthly_fee"].notna()
print("Investigation candidates:", int(flag.sum()), "bounds:", lower, upper)
```

이 코드는 조사 후보를 찾으며 해당 행을 삭제하지 않는다. 큰 요금 10000은 별도 확인이 필요한 값으로 남긴다. 실제 모델에서는 유지·대체·클리핑을 비교할 수 있지만 선택은 검증 자료에서 하고 최종 테스트에 맞추지 않는다.

## 2. 자료형 변환

숫자 열이 문자열이면 공백·단위 기호·잘못된 값을 살펴본다. `pd.to_numeric(..., errors='coerce')`는 변환 불가능한 값을 결측으로 만들므로 새로 생긴 결측을 확인한다. 무조건 변환하고 결측을 채우면 원래 오류를 숨길 수 있다.

날짜에는 `pd.to_datetime`을 쓰되 형식·시간대·오류 처리와 의미를 정한다. 실제 시계열에서 미래를 예측할 때에는 시간 순서의 분할을 검토한다. 문자열 날짜를 임의 정수로 라벨 인코딩해 시간 의미를 대체하지 않는다.

## 3. 삭제와 클리핑의 영향

행을 삭제하면 입력과 타깃을 함께 선택한다. 타깃의 극단값을 보고 테스트 행을 지우면 평가 대상이 바뀐다. 클리핑은 범위를 벗어난 값을 경계값으로 바꾸며 실제 차이를 줄일 수 있다. 처리 이유와 대상, 전후 행 수·값 범위를 기록한다.

훈련에서 정한 경계를 검증·테스트에 적용할 때도 같은 순서로 수행한다. 수작업 전처리가 복잡해지면 파이프라인이나 변환 함수로 묶어 반복 가능한 상태로 만든다. 문제에서 요구한 방법이 있으면 우선 그 조건을 따른다.

## 4. 로그 변환과 왜도

큰 양수 범위의 변수를 로그 변환하는 것은 후보가 될 수 있다. 0·음수의 정의와 역변환을 확인한다. 로그를 썼다고 분포가 반드시 정규분포가 되거나 모든 모델에 유리한 것은 아니다. 회귀 타깃을 변환하면 평가 때 원래 단위로 돌릴 필요도 있다.

## 연습과 해설

1. IQR 바깥 값은 모두 입력 오류인가? **해설:** 통계적 조사 후보이며 자료 정의와 원인을 확인해야 한다.
2. 테스트 타깃을 보고 큰 값을 삭제하면? **해설:** 평가 대상과 난이도가 바뀌고 평가를 낙관적으로 만들 수 있다.

다음 장에서는 숫자로 표현되지 않은 범주를 모델 입력으로 바꾼다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 10장 결측치 처리하기](../10-chapter/chapter.md) · [12장 범주형 변수 인코딩하기 →](../12-chapter/chapter.md)
