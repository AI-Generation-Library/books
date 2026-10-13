---
title: "17장. 분류 모델 만들기"
description: "로지스틱 회귀와 의사결정나무를 학습한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 17
part: 4
---

# 17장. 분류 모델 만들기

분류 모델의 결과는 클래스 라벨이다. 이탈 여부라면 0과 1의 뜻을 확인하고, 어떤 클래스가 중요한지 정한다. 높은 정확도가 중요한 클래스를 잘 찾는다는 뜻은 아닐 수 있으므로 혼동행렬과 여러 지표를 함께 본다.

## 1. 로지스틱 회귀

로지스틱 회귀는 이름에 회귀가 있지만 분류 모델로 사용한다. 입력의 선형 결합을 분류 확률과 연결한다. 규제 설정과 특성의 크기가 학습에 영향을 줄 수 있어 이 책에서는 전처리와 함께 사용한다.

```python
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, recall_score
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
models = {"logistic":LogisticRegression(max_iter=1000),
          "tree":DecisionTreeClassifier(max_depth=4,random_state=42)}
for name, estimator in models.items():
    model = Pipeline([("prep",preprocessor()),("clf",estimator)])
    model.fit(X_train,y_train)
    prediction = model.predict(X_val)
    print(name, accuracy_score(y_val,prediction), recall_score(y_val,prediction))
    assert set(prediction).issubset({0,1})
```

`max_iter`는 반복의 상한이고 수렴을 무조건 보장하지 않는다. 수렴 경고가 있으면 입력·스케일·설정과 반복을 확인한다. 학습이 빨랐다는 이유로 경고를 무시하지 않는다.

## 2. 의사결정나무

나무는 특성의 조건으로 자료를 나눠 예측한다. 깊이가 커지면 복잡한 패턴을 표현하지만 훈련 자료를 지나치게 기억할 수 있다. `max_depth`, `min_samples_leaf` 같은 설정은 복잡도와 관련된다. 검증 결과와 훈련 결과의 차이를 본다.

분기 조건을 해석할 때 전처리된 입력 이름을 연결한다. 원핫 열의 0·1 조건과 표준화된 요금 조건은 원래 자료의 단위와 다르다. 나무가 단순해 보여도 그 조건이 원인이라고 확정할 수 없다.

## 3. 라벨과 확률

`predict_proba`의 열 순서는 모델의 `classes_`와 연결된다. 무조건 두 번째 열이 원하는 양성 클래스라고 가정하지 말고 라벨을 확인한다. 이 책의 타깃은 0·1이지만 다른 문제에서는 문자열이나 다른 숫자일 수 있다.

임계값을 바꾸면 재현율과 정밀도 등이 달라질 수 있다. 테스트 자료에서 가장 좋은 임계값을 고르면 최종 평가가 개발에 사용된다. 임계값 비교는 검증에서 하고, 문제에서 조건을 지정했다면 그 조건을 따른다.

## 4. 공정한 비교

두 모델은 같은 입력·분할·평가 지표에서 비교한다. 모델마다 전처리기를 새로 만든 이유는 학습 상태를 독립적으로 유지하기 위해서다. 높은 점수 하나 외에 오류 유형과 재현율, 수행 시간도 볼 수 있다.

교재 코드의 특정 깊이와 반복 수는 실습 설정이다. 실제 시험 출제 설정이나 모든 데이터의 최적값으로 받아들이지 않는다.

## 연습과 해설

1. 정확도가 비슷한 두 모델 중 어느 것이 낫다고 말할 수 있는가? **해설:** 중요한 클래스의 오류·지표와 목적, 복잡도를 함께 확인해야 한다.
2. 확률 배열의 열 이름이 필요한 이유는? **해설:** 각 열이 어떤 클래스의 확률인지 확인해야 올바른 평가·임계값을 적용할 수 있다.

다음 장에서는 연속값을 예측하는 회귀를 다룬다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 16장 머신러닝 학습의 기본 흐름](../16-chapter/chapter.md) · [18장 회귀 모델 만들기 →](../18-chapter/chapter.md)
