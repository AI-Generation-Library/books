---
title: "18장. 회귀 모델 만들기"
description: "선형 회귀와 트리 회귀의 예측을 비교한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 18
part: 4
---

# 18장. 회귀 모델 만들기

회귀는 이용량·시간·가격처럼 연속값을 예측한다. 예측의 단위를 확인하고 실제값과의 오차를 그 단위에서 평가한다. 분류의 정확도를 그대로 적용하거나 숫자를 임의 구간으로 바꿔 문제를 다른 형태로 만들지 않는다.

## 1. 선형 회귀와 트리 회귀

선형 회귀는 입력과 타깃 사이의 선형 관계를 표현한다. 트리 회귀는 조건으로 나눈 영역의 예측값을 사용한다. 구조가 다른 모델을 같은 분할에서 비교하면 자료에 어떤 관계가 있는지 살펴볼 수 있다.

```python
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task("regression")
models = {"linear":LinearRegression(),
          "tree":DecisionTreeRegressor(max_depth=5,random_state=42)}
for name, estimator in models.items():
    model = Pipeline([("prep",preprocessor("regression")),("reg",estimator)])
    model.fit(X_train,y_train)
    prediction = model.predict(X_val)
    assert prediction.shape == y_val.shape
    print(name, "MAE:",mean_absolute_error(y_val,prediction),
          "RMSE:",root_mean_squared_error(y_val,prediction))
```

`root_mean_squared_error`는 이 책의 scikit-learn 버전에서 사용한다. 이전 환경이라면 지원 API를 확인해야 한다. 함수명을 바꾸면서 평가 정의까지 바꾸지 않는다.

## 2. 오차의 단위와 영향

MAE는 절대 오차의 평균이며 원래 타깃 단위다. MSE는 제곱 오차 평균이라 단위도 제곱이고 큰 오차의 영향을 더 크게 받는다. RMSE는 제곱근을 취해 원래 단위로 표현한다. 어떤 오차가 중요한지에 따라 지표를 선택한다.

R²는 기준 대비 설명 성능을 보는 지표이며 음수가 나올 수 있다. 0~1 범위로 강제로 잘라 표시하지 않는다. 다른 데이터의 R²와 MAE를 숫자 크기만으로 직접 비교하지 않는다.

## 3. 잔차와 예측 범위

잔차를 실제값에서 예측값을 뺀 것으로 정의하고 일관되게 사용한다. 예측값에 따라 잔차가 한쪽으로 치우치면 모델이 놓친 패턴일 수 있다. 특정 집단의 오차와 극단값도 확인한다.

선형 모델은 학습 범위 밖에도 숫자를 예측할 수 있지만 그 결과의 타당성은 별도 문제다. 트리는 학습 자료의 영역과 구조에 영향을 받는다. 물리적으로 불가능한 음수 예측을 임의로 0으로 바꾸려면 규칙과 평가 영향을 명시해야 한다.

## 4. 기준과 선택

훈련 평균을 사용하는 기준 모델과 비교한다. 검증에서 모델·설정을 고른 뒤 최종 테스트를 본다. 타깃을 스케일링했다면 예측을 원래 단위로 되돌려 지표를 계산한다. 표준화된 타깃의 MAE를 원래 이용 시간으로 발표하지 않는다.

## 연습과 해설

1. MSE가 100이라면 평균적으로 100시간 틀린 것인가? **해설:** 제곱 단위다. 원래 단위의 오차를 설명하려면 MAE·RMSE 등의 정의를 확인한다.
2. R²가 음수면 출력 오류인가? **해설:** 기준보다 나쁜 결과일 수 있다. 평가 자료와 정의를 확인하고 그대로 보고한다.

다음 장에서 여러 모델을 결합하는 앙상블을 익힌다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 17장 분류 모델 만들기](../17-chapter/chapter.md) · [19장 앙상블 모델 활용하기 →](../19-chapter/chapter.md)
