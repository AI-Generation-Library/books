---
title: "27장. 회귀 실습: 서비스 이용량 예측"
description: "머신러닝·딥러닝을 같은 분할에서 비교한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 27
part: 6
---

# 27장. 회귀 실습: 서비스 이용량 예측

가상 서비스 관측의 `usage_hours`를 예측한다. 자료는 독립 행이며 실제 월별 시계열이 아니다. 동일한 개발·테스트 분할에서 선형 회귀와 신경망을 비교하고 원래 시간 단위의 RMSE로 평가한다.

## 1. 비교 조건

허용 입력은 활동 사용자 수, 활동 일수, 저장량과 요금제·지역이다. ID와 타깃을 제외한다. 저장량 결측을 훈련 중앙값으로 채우고 숫자 스케일과 범주를 일관되게 처리한다.

신경망은 훈련 타깃을 표준화하고 평가 때 역변환한다. 선형 회귀의 원래 단위 RMSE와 표준화 타깃의 손실을 직접 비교하지 않는다. 두 모델의 검증 예측을 모두 원래 단위로 맞춘다.

## 2. 검증 비교와 최종 학습

```python
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from lab import split_task, preprocessor, keras_model, fit_dense, dense_predict, dataset

X_train, X_val, X_test, y_train, y_val, y_test = split_task("regression")
linear = Pipeline([("prep",preprocessor("regression")),("reg",LinearRegression())])
linear.fit(X_train,y_train)
prep = preprocessor("regression")
train = prep.fit_transform(X_train).astype("float32")
val = prep.transform(X_val).astype("float32")
mean, std = y_train.mean(), y_train.std(ddof=0)
assert std > 0
neural = keras_model(train.shape[1],"regression")
fit_dense(neural,train,((y_train-mean)/std).to_numpy(dtype="float32"),
          val,((y_val-mean)/std).to_numpy(dtype="float32"),epochs=12)
scores = {"linear":root_mean_squared_error(y_val,linear.predict(X_val)),
          "neural":root_mean_squared_error(y_val,dense_predict(neural,val)*std+mean)}
winner = min(scores,key=scores.get)
X_dev, y_dev = pd.concat([X_train,X_val]), pd.concat([y_train,y_val])
if winner == "linear":
    final = Pipeline([("prep",preprocessor("regression")),("reg",LinearRegression())])
    final.fit(X_dev,y_dev)
    prediction = final.predict(X_test)
else:
    prep_final = preprocessor("regression")
    dev = prep_final.fit_transform(X_dev).astype("float32")
    test = prep_final.transform(X_test).astype("float32")
    mean_final, std_final = y_dev.mean(), y_dev.std(ddof=0)
    final = keras_model(dev.shape[1],"regression")
    final.fit(dataset(dev,((y_dev-mean_final)/std_final).to_numpy(dtype="float32"),True),
              epochs=12,verbose=0)
    prediction = dense_predict(final,test)*std_final+mean_final
assert np.isfinite(prediction).all() and prediction.shape == y_test.shape
print("Validation RMSE:",scores,"selected:",winner)
print("Test RMSE hours:",root_mean_squared_error(y_test,prediction))
```

선택을 검증에서 완료하고 테스트는 고정 조건에서 평가한다. 신경망이 선택되면 epoch를 고정해 개발 자료 전체로 다시 학습한다. 이때 최종 테스트를 콜백의 검증 자료로 사용하지 않는다.

## 3. 해석과 한계

학습 자료는 인위적으로 만든 관계와 잡음을 가진다. 한 모델이 잘 맞는 것은 생성한 구조와 관련될 수 있다. 실제 서비스 이용량 성능이나 모델 전반의 우열로 일반화하지 않는다.

RMSE 외에 큰 오차의 사례·잔차를 확인할 수 있다. 하지만 최종 결과를 보고 반복적으로 고치면 더 이상 마지막 확인이 아니다. 실제 프로젝트에서는 새 확인 자료나 사전 합의한 평가 절차가 필요하다.

## 연습과 해설

1. 신경망의 `val_loss`와 선형 모델 RMSE를 그대로 비교하면? **해설:** 정의·단위가 다르므로 원래 단위의 같은 지표로 맞춘다.
2. 개발 자료로 다시 학습할 때 전처리·타깃 통계는? **해설:** 개발 자료에서 새로 학습하고 테스트에는 적용만 한다.

다음 장에서는 이런 코드를 문항의 지정 조건과 연결한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 26장 분류 실습: 고객 이탈 예측](../26-chapter/chapter.md) · [28장 문제의 요구사항을 코드로 옮기기 →](../28-chapter/chapter.md)
