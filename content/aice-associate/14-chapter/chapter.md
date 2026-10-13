---
title: "14장. 스케일링과 데이터 누수 방지하기"
description: "훈련에서 학습한 변환을 검증·테스트에 적용한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 14
part: 3
---

# 14장. 스케일링과 데이터 누수 방지하기

요금과 이용 지수처럼 단위와 크기가 다른 특성은 모델의 학습에 다르게 영향을 줄 수 있다. 스케일링은 수치의 표현을 바꾸는 작업이며 값의 의미와 행 대응은 유지해야 한다. 평가 데이터에 새로운 기준을 학습하지 않는 것이 중요하다.

## 1. 표준화와 범위 변환

`StandardScaler`는 훈련의 평균과 표준편차를 기준으로 값을 바꾼다. `MinMaxScaler`는 훈련에서 본 최소·최대에 따른 범위 변환을 수행한다. 둘 다 데이터가 정규분포가 되도록 보장하는 작업은 아니다.

거리·최적화에 영향을 받는 모델에서는 스케일이 중요할 수 있다. 트리 모델은 일반적으로 같은 단조 변환에 덜 민감하지만, 전처리의 필요는 자료와 문제 조건에 따라 정한다. 시험에서 스케일러를 지정했다면 그 설정을 따른다.

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from lab import split_task, NUM_CLASS

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
numeric = Pipeline([("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler())])
train = numeric.fit_transform(X_train[NUM_CLASS])
val = numeric.transform(X_val[NUM_CLASS])
assert np.allclose(train.mean(axis=0), 0, atol=1e-6)
assert train.shape[1] == val.shape[1] == 4
print("Train means:", train.mean(axis=0))
print("Validation means:", val.mean(axis=0))
```

검증 평균이 0이 아니어도 정상일 수 있다. 훈련 기준으로 변환했기 때문이다. 검증을 별도로 맞춰 평균 0으로 만드는 것은 서로 다른 표현을 모델에 제공하는 일이 된다.

## 2. `fit`과 `transform`

`fit`은 평균·범주·중앙값처럼 필요한 상태를 학습한다. `transform`은 그 상태로 자료를 바꾼다. `fit_transform`은 같은 자료에 두 단계를 수행한다. 검증·테스트에서 `fit_transform`을 사용하면 평가 정보가 전처리에 들어간다.

결측 대체 다음 스케일링처럼 순서도 중요하다. 처리 전후의 열 수·행 수·유한 값 여부를 확인한다. 스케일링으로 문자열 입력이나 누락된 열 문제를 해결할 수는 없다.

## 3. 누수의 여러 형태

전체 자료의 통계로 전처리하는 것뿐 아니라 타깃을 입력에 포함하거나, 미래 정보를 사용하거나, 테스트 점수에 맞춰 계속 설정을 고르는 것도 평가를 왜곡한다. 파이프라인은 변환 순서를 관리하는 데 도움이 되지만 미래 열을 자동으로 식별하지 않는다.

이 책은 타깃·ID를 제외하는 허용 특성 목록과 분할 후 변환을 함께 사용한다. 어떤 정보가 예측 시점에 가능한지는 사람이 자료 사전과 수집 과정을 확인해야 한다.

## 4. 변환 후 확인

MinMax 변환의 새 관측이 훈련 범위 밖이면 0~1을 벗어날 수 있다. 오류라고 단정하지 말고 자료와 설정을 본다. 스케일이 바뀐 숫자를 원래 단위로 해석하지 않는다. 회귀 타깃까지 바꾸었다면 결과를 원래 단위로 되돌린 뒤 필요한 지표를 계산한다.

## 연습과 해설

1. 테스트 평균이 0이 되도록 다시 `fit`해도 되는가? **해설:** 훈련 표현과 달라지므로 학습된 변환을 적용해야 한다.
2. Pipeline을 썼는데 입력에 해지 이후 정보가 있다. 안전한가? **해설:** 아니다. 데이터 시점 누수는 입력 선택에서 점검해야 한다.

다음 장에서 숫자·범주 변환을 하나의 흐름으로 묶는다. 참고: [StandardScaler 공식 API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 13장 훈련·검증·테스트 데이터 나누기](../13-chapter/chapter.md) · [15장 전처리 흐름 완성하기 →](../15-chapter/chapter.md)
