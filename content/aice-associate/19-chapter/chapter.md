---
title: "19장. 앙상블 모델 활용하기"
description: "랜덤 포레스트와 부스팅의 설정과 결과를 비교한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 19
part: 4
---

# 19장. 앙상블 모델 활용하기

앙상블은 여러 모델의 결과를 결합하는 방식이다. 랜덤 포레스트는 다양한 나무를 결합하고, 부스팅은 이전 모델에서 남은 문제를 순차적으로 보완하는 구성을 사용한다. 복잡도가 늘어나는 만큼 학습 시간과 과적합, 설정을 함께 살펴본다.

## 1. 랜덤 포레스트

여러 나무가 서로 다른 자료·특성 선택을 활용하도록 만들어 결과를 결합한다. 나무 수를 늘리면 안정성에 도움이 될 수 있지만 계산 비용도 늘며, 모든 데이터에서 성능이 계속 개선되는 것은 아니다. 깊이와 리프의 최소 표본도 중요하다.

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
estimators = {
    "forest":RandomForestClassifier(n_estimators=80,max_depth=6,random_state=42,n_jobs=1),
    "boosting":GradientBoostingClassifier(n_estimators=60,learning_rate=0.05,max_depth=2,random_state=42),
}
for name, estimator in estimators.items():
    model = Pipeline([("prep",preprocessor()),("clf",estimator)]).fit(X_train,y_train)
    prediction = model.predict(X_val)
    value = f1_score(y_val,prediction,zero_division=0)
    assert 0 <= value <= 1
    print(name, "validation F1:",value)
```

`n_jobs=1`은 작은 실습의 계산 자원을 제한하는 선택이다. 성능 지표를 맞추기 위해 난수를 무작정 바꿔 좋은 결과만 선택하지 않는다.

## 2. 부스팅의 설정

학습률과 단계 수가 함께 영향을 준다. 작은 학습률을 쓰면 더 많은 단계가 필요할 수 있지만 무조건 같은 결과가 되지는 않는다. 깊이가 커지면 각 단계가 더 복잡해진다. 제한된 후보로 시작하고 검증에서 비교한다.

이 책은 기본 scikit-learn 구현으로 연습한다. 추가 패키지의 모델은 설치·API·환경 조건이 다르므로 필요할 때 공식 문서를 확인한다. 여러 이름을 늘리는 것보다 하나의 학습·평가 흐름을 정확히 수행하는 것이 먼저다.

## 3. 특성 중요도 해석

일부 나무 모델의 특성 중요도는 모델이 해당 표현을 사용한 정도를 보여주며 인과관계가 아니다. 원핫 인코딩한 열은 원래 범주 변수 하나에서 나왔을 수 있다. 이름과 그룹을 연결하고 어떤 계산의 중요도인지 설명한다.

특성 중요도가 높다고 예측 시점에 사용할 수 없는 열을 허용하지 않는다. 타깃 누수는 좋은 중요도와 높은 점수로 드러날 수도 있다. 자료 정의·시점·권한은 모델 지표와 별도로 확인한다.

## 4. 후보 수를 제한하기

시험 연습의 목적은 시간 안에 요구조건을 수행하는 것이다. 모든 파라미터의 조합을 큰 격자로 탐색하면 학습 시간을 소모한다. 명확한 가설과 작은 후보를 두고 비교 지표·자료를 고정한다.

## 연습과 해설

1. 포레스트 나무 수를 두 배로 늘리면 점수도 두 배가 되는가? **해설:** 아니다. 지표와 계산 비용의 관계를 실제 검증해야 한다.
2. 중요도가 높은 열은 원인인가? **해설:** 모델의 사용과 원인 해석은 다르며 누수·자료 정의를 확인해야 한다.

다음 장에서 훈련과 검증의 차이를 활용해 복잡도를 조정한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 18장 회귀 모델 만들기](../18-chapter/chapter.md) · [20장 과적합을 확인하고 성능 개선하기 →](../20-chapter/chapter.md)
