---
title: "25장. 학습 곡선과 성능 개선하기"
description: "검증 손실·EarlyStopping·Dropout을 활용한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 25
part: 5
---

# 25장. 학습 곡선과 성능 개선하기

epoch별 훈련·검증 손실을 보면 학습이 진행되는지와 과적합의 신호를 살펴볼 수 있다. 한 epoch의 작은 변동에 반응하기보다 추세와 지표, 자료를 함께 확인한다. 손실을 줄이는 것과 최종 업무 지표를 개선하는 것은 항상 같지 않다.

## 1. History 읽기

`fit`이 반환하는 History의 `history`에는 손실·지표 목록이 있다. 키는 컴파일 설정에 따라 달라진다. `val_loss`가 없다면 검증 자료를 전달했는지 확인한다. 학습 곡선에 최종 테스트 자료를 넣지 않는다.

```python
import matplotlib.pyplot as plt
from lab import dense_data, keras_model, fit_dense
import tensorflow as tf

X_train, X_val, X_test, y_train, y_val, y_test, prep = dense_data()
model = keras_model(X_train.shape[1],dropout=0.2)
early = tf.keras.callbacks.EarlyStopping(monitor="val_loss",patience=2,
                                         restore_best_weights=True)
history = fit_dense(model,X_train,y_train,X_val,y_val,epochs=20,callbacks=[early])
assert len(history.history["loss"]) <= 20
assert len(history.history["loss"]) == len(history.history["val_loss"])
plt.plot(history.history["loss"],label="train")
plt.plot(history.history["val_loss"],label="validation")
plt.xlabel("Epoch index")
plt.ylabel("Loss")
plt.legend()
plt.show()
plt.close("all")
print("Completed epochs:",len(history.history["loss"]))
```

이 코드가 반드시 조기 종료된다고 단정하지 않는다. 주어진 실행에서 모니터 값의 개선 조건과 patience를 만족했는지에 따라 끝나는 epoch가 달라진다.

## 2. EarlyStopping

지정 지표가 개선되지 않으면 학습을 멈추는 콜백이다. 손실은 보통 낮아지는 방향이며 지표의 방향과 `monitor`를 확인한다. `restore_best_weights=True`는 가장 좋았던 모니터 시점의 가중치를 복원하는 설정이다. 마지막 epoch의 가중치와 같다고 가정하지 않는다.

검증을 반복해 모델 선택에 사용했다면 그 점수는 개발 결과다. 설정을 고정한 최종 테스트가 별도로 필요하다. 콜백을 붙였다는 사실만으로 과적합이 완전히 해결되지는 않는다.

## 3. Dropout과 복잡도

Dropout은 학습 중 일부 활성값을 제외하는 방식으로 규제에 활용된다. 추론 시의 동작은 학습과 다르다. 비율을 너무 높이면 필요한 정보 학습을 어렵게 할 수 있다. 모델 크기·학습률·데이터와 함께 비교한다.

작은 정형 자료에서는 계층과 노드 수를 줄이는 것도 후보가 된다. 데이터를 늘릴 수 없는 상황에서는 누수·분포·특성과 설정을 먼저 확인한다. 훈련·검증 모두 나쁘다면 과적합만의 문제라고 단정하지 않는다.

## 4. 한 번에 제한된 변경

계층, 학습률, Dropout과 전처리를 동시에 바꾸면 무엇이 영향을 줬는지 해석하기 어렵다. 기준 설정을 기록하고 후보를 제한한다. 실제 시험에서는 요구한 노드·활성화·손실·epoch 등 조건을 임의로 바꾸지 않는다.

학습이 불안정하면 입력의 유한값·스케일·타깃 형태와 손실 조합을 먼저 확인한다. NaN 손실을 그림에서 제외하고 성공처럼 표시하지 않는다.

## 연습과 해설

1. 훈련 손실은 줄고 검증 손실은 커지면? **해설:** 과적합 신호일 수 있다. 자료·분포·평가와 복잡도를 함께 확인한다.
2. 검증 대신 테스트 손실로 EarlyStopping을 해도 되는가? **해설:** 테스트가 선택 과정에 사용된다. 개발용 검증과 최종 테스트를 분리한다.

다음 부에서 분석부터 마지막 평가까지 통합한다. 참고: [EarlyStopping 공식 API](https://keras.io/api/callbacks/early_stopping/).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 24장 딥러닝 회귀 모델 만들기](../24-chapter/chapter.md) · [26장 분류 실습: 고객 이탈 예측 →](../26-chapter/chapter.md)
