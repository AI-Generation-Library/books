---
title: "21장. 모델 성능을 정확히 평가하기"
description: "분류·회귀 지표와 그래프를 문제 목적에 연결한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 21
part: 4
---

# 21장. 모델 성능을 정확히 평가하기

평가 지표는 모델이 어떤 오류를 얼마나 만드는지 설명한다. 숫자 하나를 보고 모든 성능을 판단하지 않는다. 분류에서는 양성 클래스와 임계값을, 회귀에서는 단위와 오차의 정의를 먼저 정한다.

## 1. 혼동행렬과 양성 클래스

이 책에서 1은 이탈, 0은 유지다. 실제 1을 0으로 예측하면 놓친 이탈이며 실제 0을 1로 예측하면 잘못된 경보다. 같은 오류 개수라도 업무 영향이 다를 수 있다. `confusion_matrix`의 라벨 순서를 지정하면 행·열의 의미를 확인하기 쉽다.

```python
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, classification_report,
    roc_auc_score, ConfusionMatrixDisplay)
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
model = Pipeline([("prep",preprocessor()),("clf",LogisticRegression(max_iter=1000))])
model.fit(X_train,y_train)
pred = model.predict(X_val)
classes = list(model.named_steps["clf"].classes_)
prob = model.predict_proba(X_val)[:,classes.index(1)]
matrix = confusion_matrix(y_val,pred,labels=[0,1])
assert matrix.sum() == len(y_val)
print(classification_report(y_val,pred,zero_division=0))
print("ROC AUC:",roc_auc_score(y_val,prob))
ConfusionMatrixDisplay(matrix,display_labels=[0,1]).plot()
plt.show()
plt.close("all")
```

행은 실제값, 열은 예측값이라는 설정을 확인한다. 이 예의 그래프는 Matplotlib·scikit-learn 구현의 표시 기준이다. 표의 순서를 추측해 설명하지 않는다.

## 2. 정밀도·재현율·F1

정밀도는 양성으로 예측한 것 중 실제 양성의 비율이고, 재현율은 실제 양성 중 찾아낸 비율이다. F1은 두 지표를 조화평균으로 묶는다. 양성 예측이나 실제 양성이 없는 조건에서는 지표가 정의되지 않을 수 있으므로 처리 설정과 상황을 확인한다.

`zero_division=0`은 해당 상황의 출력 규칙이지 모델이 충분히 평가되었다는 의미가 아니다. 다중 클래스에서는 각 클래스와 평균 방식이 무엇인지 설명한다. 가중 평균 하나로 소수 클래스의 실패를 가리지 않는다.

## 3. ROC AUC와 확률

ROC AUC에는 라벨보다 점수·확률을 제공한다. 이 책에서는 클래스 1의 확률 열을 명시적으로 찾는다. 평가 자료에 한 클래스만 있으면 ROC AUC 계산이 성립하지 않을 수 있다. 클래스 분포와 표본을 확인한다.

ROC AUC가 높아도 특정 임계값의 재현율·정밀도가 원하는 조건을 만족하지 않을 수 있다. 확률이 실제 위험 확률로 잘 맞는지도 별도 문제다. 이 책의 기본 예에서 그 확률의 보정 성능까지 검증한 것으로 표시하지 않는다.

## 4. 회귀 지표와 그래프

회귀에서는 MAE·RMSE·R²와 실제값 대 예측값, 잔차 그림을 볼 수 있다. 타깃을 변환했다면 원래 단위로 평가한다. 두 배열의 길이와 행 순서, 차원을 확인하고 결측·무한값도 점검한다.

검증에서 지표와 임계값을 선택했다면 테스트는 그 조건을 고정해 평가한다. 여러 지표 중 가장 보기 좋은 하나만 골라 보고하지 않는다. 문제에서 지표가 지정되었다면 정확히 그 값을 산출한다.

## 연습과 해설

1. 실제 이탈을 많이 놓친다면 무엇을 보는가? **해설:** 양성 클래스 재현율과 FN, 선택한 임계값을 확인한다.
2. ROC AUC에 `predict` 라벨을 주면 충분한가? **해설:** 연속 점수·확률을 제공하는 평가 목적과 라벨의 차이를 이해해야 한다.

다음 부에서는 같은 자료를 신경망 입력으로 바꿔 학습한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 20장 과적합을 확인하고 성능 개선하기](../20-chapter/chapter.md) · [22장 TensorFlow·Keras 시작하기 →](../22-chapter/chapter.md)
