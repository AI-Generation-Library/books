---
title: "24장. 딥러닝 회귀 모델 만들기"
description: "연속 타깃의 학습과 원래 단위의 평가를 수행한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 24
part: 5
---

# 24장. 딥러닝 회귀 모델 만들기

연속값 회귀의 출력은 보통 단일 선형 노드다. 이용 시간을 0~1의 이진 확률처럼 제한하면 타깃 의미가 달라진다. 출력·손실·타깃의 단위를 연결하고 결과를 원래 단위에서 평가한다.

## 1. 입력과 타깃 준비

입력 전처리는 훈련에서 학습한다. 타깃 크기가 학습에 영향을 주면 훈련 타깃의 평균·표준편차로 변환할 수 있다. 타깃 변환도 검증·테스트에서 새로 학습하지 않는다. 일정한 타깃처럼 표준편차가 0인 경우는 별도로 처리해야 한다.

```python
import numpy as np
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from lab import dense_data, keras_model, fit_dense, dense_predict

X_train, X_val, X_test, y_train, y_val, y_test, prep = dense_data("regression")
mean, std = y_train.mean(), y_train.std()
assert std > 0
train_scaled = (y_train-mean)/std
val_scaled = (y_val-mean)/std
model = keras_model(X_train.shape[1],task="regression")
history = fit_dense(model,X_train,train_scaled,X_val,val_scaled,epochs=12)
pred = dense_predict(model,X_val)*std+mean
assert pred.shape == y_val.shape
assert np.isfinite(pred).all()
print("MAE hours:",mean_absolute_error(y_val,pred))
print("RMSE hours:",root_mean_squared_error(y_val,pred))
```

이 helper의 회귀 출력은 linear, 손실은 MSE다. 학습 중의 MAE는 표준화된 타깃 기준이다. 위의 평가처럼 역변환한 예측으로 계산해야 원래 시간 단위를 설명할 수 있다.

## 2. 출력 범위와 도메인

선형 출력은 음수도 낼 수 있다. 음수가 불가능한 타깃이라면 출력·변환·사후 규칙의 대안을 검토하되 임의 클리핑을 숨기지 않는다. 클리핑 전후 지표와 가정이 다를 수 있다. 시험에서는 지정한 출력층·손실·처리 조건을 따른다.

로그 타깃을 쓰는 경우에는 역변환과 평균 예측의 해석을 확인한다. 이 책의 기본 예는 평균·표준편차 변환만 사용한다. 타깃 변환을 무조건 성능 개선으로 가정하지 않는다.

## 3. 단순 모델과 비교

정형 자료에서는 선형 모델이나 트리 모델이 신경망보다 잘 맞을 수도 있다. 같은 분할과 원래 단위의 지표로 비교한다. 신경망이 더 최신 기술이라는 이유로 승자를 정하지 않는다.

모델 비교에서 학습 시간·설정 수·검증 결과를 기록한다. 후보의 전처리와 데이터가 다르면 그 차이도 함께 설명한다. 27장에서 같은 서비스 이용량 자료로 비교한다.

## 4. 형태 오류 찾기

예측 `(n,1)`과 타깃 `(n,)`의 수작업 차이는 방송 연산으로 `(n,n)`이 될 수 있다. 이 예는 예측을 1차원으로 맞추고 형태를 검사한다. 라이브러리 지표를 쓰더라도 행 순서와 길이, 유한값을 먼저 확인한다.

## 연습과 해설

1. 타깃을 표준화한 모델의 MAE를 그대로 시간이라고 부르면? **해설:** 단위가 다르다. 원래 단위로 역변환해 평가한다.
2. 이용량 예측 출력에 sigmoid를 쓰면 어떤 제약이 생기는가? **해설:** 출력이 0~1로 제한된다. 타깃·변환 정의와 맞는지 확인해야 한다.

다음 장에서 학습 곡선과 검증을 통해 학습을 조정한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 23장 딥러닝 분류 모델 만들기](../23-chapter/chapter.md) · [25장 학습 곡선과 성능 개선하기 →](../25-chapter/chapter.md)
