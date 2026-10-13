---
title: "20장. 과적합을 확인하고 성능 개선하기"
description: "훈련·검증 차이·교차검증·설정 탐색을 이해한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 20
part: 4
---

# 20장. 과적합을 확인하고 성능 개선하기

훈련에서 높은 점수를 얻고 검증에서 낮아지는 현상은 과적합의 신호일 수 있다. 하지만 분포 차이·전처리 불일치·표본 부족도 함께 확인해야 한다. 모델 복잡도를 줄이는 것만이 모든 오류의 해결책은 아니다.

## 1. 같은 지표로 차이 보기

훈련과 검증에 같은 지표를 계산한다. 두 집합을 섞어 점수를 내면 일반화를 확인할 수 없다. 작은 표본에서의 차이가 얼마나 안정적인지도 검토한다. 훈련 점수는 최종 성능의 독립 확인이 아니다.

## 2. 교차검증의 역할

교차검증은 개발 자료를 여러 폴드로 나눠 학습·검증을 반복한다. 작은 자료의 설정 비교에 도움이 될 수 있다. 변환도 각 폴드의 훈련 부분에서 학습해야 하므로 전체 자료를 미리 바꾸는 대신 Pipeline을 전달한다.

```python
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
pipeline = Pipeline([("prep",preprocessor()),
                     ("clf",DecisionTreeClassifier(random_state=42))])
cv = StratifiedKFold(n_splits=3,shuffle=True,random_state=42)
search = GridSearchCV(pipeline, {"clf__max_depth":[2,4,6]},
                      scoring="f1",cv=cv,n_jobs=1)
search.fit(X_train,y_train)
best = search.best_estimator_
print(search.best_params_, search.best_score_)
print("train accuracy:",accuracy_score(y_train,best.predict(X_train)))
print("validation accuracy:",accuracy_score(y_val,best.predict(X_val)))
assert search.best_params_["clf__max_depth"] in [2,4,6]
```

이 실습은 훈련 부분 안에서 후보를 찾고 별도 검증을 본다. 필요하면 개발 자료 전체를 활용하는 다른 설계를 선택할 수 있지만 최종 테스트는 마지막 확인용으로 유지한다.

## 3. 탐색 결과 읽기

`best_score_`는 선택한 교차검증 지표의 결과다. 위의 F1 점수를 정확도라고 부르지 않는다. 후보별 평균과 변동, 학습 시간과 오류를 확인할 수 있다. 여러 후보를 비교하면 선택의 낙관성도 생길 수 있으므로 최종 확인이 필요하다.

scikit-learn의 일부 손실 지표는 점수 최대화 인터페이스에 맞춰 음수 부호로 제공된다. `neg_mean_absolute_error`의 부호를 이해하고 보고할 때 원래 오류 방향으로 바꾼다. 무조건 숫자가 큰 것을 오차가 크다고 해석하지 않는다.

## 4. 개선의 순서

먼저 타깃·자료형·누수·전처리·분할을 확인한다. 다음으로 복잡도·규제·학습 설정과 특성을 검토한다. 테스트를 반복해서 들여다보며 마지막 숫자를 올리는 작업을 성능 개선이라고 부르지 않는다.

시간이 제한된 연습에서는 큰 탐색보다 요구한 모델을 정확히 학습하고 평가하는 것이 우선일 수 있다. 교차검증과 탐색은 원리를 이해하는 보충 학습이며 모든 시험 문제에서 실행해야 하는 단계는 아니다.

## 연습과 해설

1. 전체 자료를 스케일링한 뒤 GridSearchCV에 넣으면? **해설:** 폴드 검증 정보가 변환에 들어간다. Pipeline 안에 변환을 넣는다.
2. `best_score_`와 최종 테스트 결과는 같은가? **해설:** 선택에 사용한 교차검증 결과와 독립 확인 결과는 다르다.

다음 장에서 목적에 맞는 지표와 그래프를 선택한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 19장 앙상블 모델 활용하기](../19-chapter/chapter.md) · [21장 모델 성능을 정확히 평가하기 →](../21-chapter/chapter.md)
