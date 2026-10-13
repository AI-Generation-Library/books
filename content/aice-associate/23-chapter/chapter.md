---
title: "23장. 딥러닝 분류 모델 만들기"
description: "출력층·라벨·손실의 조합을 맞춘다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 23
part: 5
---

# 23장. 딥러닝 분류 모델 만들기

라벨 표현, 출력층과 손실의 조합은 분류 모델의 기본 계약이다. 이진 타깃 0·1, 정수 다중 클래스와 원핫 다중 클래스는 형태가 다르다. 코드가 실행되는지와 올바른 문제를 학습하는지 함께 확인한다.

## 1. 기본 조합

| 문제·타깃 | 출력 예 | 손실 예 |
| --- | --- | --- |
| 이진 0·1 | 노드 1, sigmoid | binary_crossentropy |
| 다중 클래스 정수 | 클래스 수, softmax | sparse_categorical_crossentropy |
| 다중 클래스 원핫 | 클래스 수, softmax | categorical_crossentropy |

이는 확률 출력을 쓰는 일반적인 학습 조합이다. logits를 출력한다면 손실의 `from_logits` 등 설정을 맞춰야 한다. 서로 다른 조합을 무조건 같은 것으로 바꾸지 않는다.

## 2. 구조 직접 작성하기

```python
from lab import dense_data, fit_dense, dense_predict
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score

X_train, X_val, X_test, y_train, y_val, y_test, prep = dense_data()
tf.keras.backend.clear_session()
tf.keras.utils.set_random_seed(42)
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32,activation="relu"),
    tf.keras.layers.Dense(16,activation="relu"),
    tf.keras.layers.Dense(1,activation="sigmoid"),
])
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.01),
              loss="binary_crossentropy",metrics=["accuracy"])
history = fit_dense(model,X_train,y_train,X_val,y_val,epochs=12)
prob = dense_predict(model,X_val)
pred = (prob >= 0.5).astype(int)
assert model.output_shape[-1] == 1
print(accuracy_score(y_val,pred),f1_score(y_val,pred,zero_division=0))
```

학습 손실과 분류 F1은 같은 지표가 아니다. 모델을 업데이트하는 손실과 결과를 해석하는 지표를 구분한다. 검증 결과를 기록하고 원하는 점수가 나올 때까지 테스트를 반복해서 보지 않는다.

## 3. 확률을 클래스로 바꾸기

sigmoid 출력은 이 예에서 클래스 1의 확률 후보다. 0.5 기준으로 라벨을 만든다. 다중 클래스 softmax 출력에서는 각 열이 어떤 라벨에 해당하는지 확인하고 가장 큰 열을 선택할 수 있다. 이진 출력 하나에 `argmax`를 적용하면 모두 같은 클래스가 될 수 있다.

예측 배열이 `(n,1)`이라면 라벨 변환과 평가 전에 필요한 형태를 맞춘다. helper의 `ravel`은 이진·단일 회귀 출력에 사용한다. 다중 클래스 확률까지 펼치면 샘플과 클래스 구조가 깨지므로 그대로 사용하지 않는다.

## 4. 검증과 선택

모델 크기, 학습률과 epoch 후보는 검증에서 비교한다. 클래스 불균형이 있으면 정확도 외에 필요한 지표를 본다. 가중치나 샘플링을 추가할 때에도 적용 범위와 평가 분포를 유지한다. 기본 실습은 별도의 균형 보정 없이 동작을 익히는 구성이다.

## 연습과 해설

1. 클래스가 3개이고 라벨이 정수라면 일반적인 출력·손실은? **해설:** 3개 softmax와 sparse categorical crossentropy 조합이다.
2. sigmoid 출력 한 열에 argmax를 쓰면? **해설:** 비교할 열이 하나여서 모두 인덱스 0이 될 수 있다. 이진 임계값을 적용한다.

다음 장에서는 연속값을 신경망으로 예측한다. 참고: [Keras Sequential 안내](https://keras.io/guides/sequential_model/), [Keras 확률 손실 API](https://keras.io/api/losses/probabilistic_losses/).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 22장 TensorFlow·Keras 시작하기](../22-chapter/chapter.md) · [24장 딥러닝 회귀 모델 만들기 →](../24-chapter/chapter.md)
