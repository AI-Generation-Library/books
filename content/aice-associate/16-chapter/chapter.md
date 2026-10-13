---
title: "16장. 머신러닝 학습의 기본 흐름"
description: "문제 유형·기준 모델·학습·예측의 순서를 익힌다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 16
part: 4
---

# 16장. 머신러닝 학습의 기본 흐름

모델 학습은 `fit` 한 줄로 표현할 수 있지만 그 앞의 문제 정의와 입력, 뒤의 예측·평가까지 맞아야 한다. 분류는 클래스, 회귀는 연속값을 예측한다. 문제의 타깃과 평가 목적을 먼저 확인한다.

## 1. 기준 모델 만들기

복잡한 모델을 학습하기 전에 단순 기준을 둔다. 분류는 가장 많은 클래스, 회귀는 훈련 타깃 평균 같은 기준과 비교할 수 있다. 모델 점수가 높아 보여도 기준을 이기지 못할 수 있다.

```python
from sklearn.dummy import DummyClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
baseline = DummyClassifier(strategy="most_frequent").fit(X_train,y_train)
model = Pipeline([("prep",preprocessor()),
                  ("clf",LogisticRegression(max_iter=1000))]).fit(X_train,y_train)
baseline_score = accuracy_score(y_val,baseline.predict(X_val))
model_score = accuracy_score(y_val,model.predict(X_val))
assert 0 <= baseline_score <= 1 and 0 <= model_score <= 1
print({"baseline_accuracy":baseline_score, "model_accuracy":model_score})
```

이 실습의 점수는 가상 자료와 지정 환경의 결과다. 실제 고객 이탈 성능이나 시험 합격 가능성을 나타내지 않는다. 모델이 기준을 이기도록 검사 조건을 만들기보다 결과를 보고 원인을 분석한다.

## 2. 학습과 예측

`fit(X_train,y_train)`은 입력·타깃 대응을 사용해 상태를 학습한다. `predict(X_val)`은 학습된 모델로 새 입력을 예측한다. 평가에는 예측과 같은 행 순서의 실제값이 필요하다. `score`의 기본 지표는 모델 종류에 따라 다르므로 무조건 정확도로 부르지 않는다.

학습 자료의 높은 점수만 보고 모델을 선택하지 않는다. 학습에서 본 패턴을 기억한 것과 새로운 자료에 일반화하는 것은 다르다. 검증에서 비교한 뒤 최종 설정을 고정하고 테스트를 확인한다.

## 3. 파라미터와 학습된 상태

모델 설정에는 반복 횟수·깊이·규제 등이 있다. `get_params()`는 설정을, 학습 후의 `coef_` 같은 속성은 학습 상태를 보여준다. 설정값을 요구하는 문제와 학습 결과를 확인하는 문제를 구분한다.

난수는 비교를 재현하는 데 도움이 된다. 같은 분할에서 후보를 비교하고 반복성이 필요한 모델에는 지정한 `random_state`를 사용한다. 모든 라이브러리·하드웨어에서 결과가 완전히 같다는 뜻은 아니다.

## 4. 기록할 최소 정보

모델 이름·설정, 특성 목록, 분할, 전처리와 평가 지표를 함께 기록한다. 후보마다 다른 자료나 지표를 쓰고 가장 큰 숫자를 고르지 않는다. 실행 오류와 미학습 상태를 성공 점수처럼 기록하지 않는다.

## 연습과 해설

1. `score`가 0.8이면 분류 정확도인가? **해설:** 객체의 기본 지표를 확인한다. 회귀에서는 R²일 수 있다.
2. 기준 모델보다 낮은 점수가 나왔다. 무조건 코드 오류인가? **해설:** 오류일 수 있지만 특성·설정·분포와 실제 문제 난이도를 함께 확인한다.

다음 장에서는 대표 분류 모델을 학습하고 예측을 비교한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 15장 전처리 흐름 완성하기](../15-chapter/chapter.md) · [17장 분류 모델 만들기 →](../17-chapter/chapter.md)
