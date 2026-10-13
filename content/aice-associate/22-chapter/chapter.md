---
title: "22장. TensorFlow·Keras 시작하기"
description: "입력 형태·Dense 계층·학습 설정을 확인한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 22
part: 5
---

# 22장. TensorFlow·Keras 시작하기

정형 데이터 신경망은 각 샘플의 특성을 입력으로 받아 층을 통과하며 출력을 만든다. 입력의 열 수와 출력·타깃의 형태, 손실함수가 연결되어야 한다. 모델 구조를 만든 것과 학습을 완료한 것은 다르다.

## 1. 입력과 Dense 계층

`Input(shape=(특성 수,))`는 샘플 하나의 형태를 지정한다. 전체 샘플 수를 입력 특성 수에 넣지 않는다. Dense 계층은 입력과 가중치·편향을 결합하고 활성화 함수를 적용한다. 은닉층 크기는 표현력·계산 비용에 영향을 준다.

```python
import numpy as np
from lab import dense_data, keras_model, fit_dense, dense_predict

X_train, X_val, X_test, y_train, y_val, y_test, prep = dense_data()
assert X_train.dtype == np.float32
model = keras_model(X_train.shape[1])
model.summary()
history = fit_dense(model,X_train,y_train,X_val,y_val,epochs=2)
probability = dense_predict(model,X_val)
assert probability.shape == (120,)
assert np.isfinite(probability).all()
assert "val_loss" in history.history
print("Input features:",X_train.shape[1])
```

`dense_data`는 훈련에서 전처리를 학습하고 다른 집합에 적용한 float32 배열을 만든다. 신경망에 문자열과 결측을 그대로 넣지 않는다. 작은 자료이므로 dense 배열을 쓰며 실제 큰 원핫 자료에는 메모리 확인이 필요하다.

## 2. 모델 구성·컴파일·학습

구성은 계층과 형태를, `compile`은 최적화·손실·평가 지표를 정한다. `fit`은 실제 학습을 수행한다. `summary`가 출력되었다고 학습이 완료된 것은 아니다. `evaluate`와 `predict`도 역할이 다르다.

이 책의 helper는 Adam·은닉층 32와 16·이진 출력 하나를 구성한다. 23장에서 구조를 직접 작성하고 손실과 출력의 조합을 확인한다. 설정이 고정된 helper를 실습 편의로 사용하지만 실제 문제의 지정 조건이 우선이다.

## 3. 배치와 epoch

epoch는 훈련 자료를 한 번 학습하는 단위이며 배치는 한 번의 업데이트에 사용하는 묶음이다. epoch를 늘리면 훈련 손실이 줄 수 있지만 검증 성능이 계속 좋아지는 것은 아니다. 학습률과 배치 크기도 함께 영향을 준다.

이 책은 CPU의 작은 실습을 위해 배치 32와 제한된 epoch를 사용한다. `lab.dataset`은 TensorFlow Dataset의 작업 스레드 수도 제한한다. 이는 실습 환경 설정이며 시험에서 반드시 같은 Dataset 구성을 써야 한다는 뜻은 아니다.

## 4. 재현과 상태

모델을 새로 비교할 때 이전 가중치를 계속 학습하는지 새 모델인지 구분한다. helper는 세션을 정리하고 seed를 지정한 새 모델을 만든다. 난수와 하드웨어·라이브러리 차이로 수치가 달라질 수 있다.

학습 곡선, 입력 형태와 설정을 기록한다. 간단한 실습에서는 GPU가 필요하지 않으며 환경별 지원은 공식 설치 안내로 확인한다. 학습 환경의 버전을 실제 시험 환경과 동일하다고 가정하지 않는다.

## 연습과 해설

1. 입력이 `(360,9)`라면 Input의 shape는? **해설:** 샘플의 특성 9개를 나타내는 `(9,)`다.
2. 같은 모델에 다시 `fit`하면 초기 상태인가? **해설:** 일반적으로 기존 가중치에서 이어간다. 새 비교라면 새 모델을 만든다.

다음 장에서 분류의 출력층과 손실을 직접 맞춘다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 21장 모델 성능을 정확히 평가하기](../21-chapter/chapter.md) · [23장 딥러닝 분류 모델 만들기 →](../23-chapter/chapter.md)
