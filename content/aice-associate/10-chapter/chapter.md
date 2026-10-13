---
title: "10장. 결측치 처리하기"
description: "삭제·대체의 기준과 학습 데이터에 맞춘 처리 방법을 익힌다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 10
part: 3
---

# 10장. 결측치 처리하기

결측은 값이 없다는 표시이지 항상 0이라는 뜻은 아니다. 요금의 결측을 0으로 채우면 무료 고객이라는 새로운 의미를 만들 수 있다. 삭제와 대체는 자료의 뜻, 손실되는 행과 모델의 입력 조건을 고려해 선택한다.

## 1. 열별로 선택하기

타깃이 없으면 일반 지도학습에서 해당 행의 정답을 알 수 없다. 타깃을 임의로 채우지 말고 제외·재수집 등의 조건을 확인한다. 입력 숫자는 평균·중앙값 같은 대체가 후보이고 범주는 최빈값이나 별도의 누락 범주를 검토할 수 있다.

삭제는 간단하지만 특정 집단의 행이 많이 빠질 수 있다. 대체도 분포를 바꾸며 결측 원인을 해결하지 않는다. 어떤 처리가 적합한지는 문제 조건과 검증으로 확인한다. 이 책의 예제에서는 숫자 중앙값과 범주 최빈값을 기본으로 사용한다.

## 2. 훈련에서 통계를 학습하기

```python
import numpy as np
from sklearn.impute import SimpleImputer
from lab import split_task, NUM_CLASS

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
imputer = SimpleImputer(strategy="median")
train_numeric = imputer.fit_transform(X_train[NUM_CLASS])
val_numeric = imputer.transform(X_val[NUM_CLASS])
assert np.isfinite(train_numeric).all()
assert np.isfinite(val_numeric).all()
expected = X_train["monthly_fee"].median()
assert np.isclose(imputer.statistics_[NUM_CLASS.index("monthly_fee")], expected)
print(imputer.statistics_)
```

검증 자료를 따로 `fit`하면 다른 중앙값을 사용할 수 있다. 전체 자료의 중앙값을 사용하면 평가 자료의 정보가 훈련에 들어간다. 훈련 통계를 보존하고 다른 자료에는 `transform`만 적용한다.

## 3. DataFrame과 배열의 연결

`SimpleImputer`는 기본적으로 배열을 반환한다. 열 이름이 사라졌다면 어떤 순서로 입력했는지 기록한다. 배열을 DataFrame으로 다시 만들 때 열과 인덱스를 함께 연결한다. 새 DataFrame의 기본 인덱스와 원래 타깃 인덱스가 다르면 행 대응이 어긋날 수 있다.

전체가 결측인 열은 대체 통계가 정의되지 않는 등 별도 동작이 있을 수 있다. 실제 자료와 라이브러리 버전에서 반환 열을 확인한다. 이 책의 기본 자료에는 전체 결측 열이 없다.

## 4. 결측 자체가 정보일 때

결측 여부를 별도 특성으로 사용할 수 있지만 생성 시점과 의미를 확인한다. 답이 결정된 뒤에만 값이 사라지는 구조라면 누수일 수 있다. 누락 여부를 추가한다고 항상 성능이 개선되지는 않는다.

전처리의 목적은 입력을 일관되게 만드는 것이다. 모델 종류가 결측을 처리할 수 있어도 문제에서 특정 대체 방식을 요구하면 그 조건을 따른다. 해당 모델이 어떤 자료형과 결측 형태를 지원하는지도 확인한다.

## 연습과 해설

1. 검증 요금 평균이 훈련과 다르다. 어느 값을 대체에 쓰는가? **해설:** 훈련에서 학습한 값을 검증에도 적용한다.
2. 결측 행을 삭제한 후 `y`도 같은 행을 삭제해야 하는가? **해설:** 입력과 타깃의 행 대응을 유지해야 한다. 마스크나 인덱스로 함께 선택한다.

다음 장에서 값은 있지만 잘못되거나 극단적인 자료를 다룬다. 참고: [scikit-learn 결측 처리 안내](https://scikit-learn.org/stable/modules/impute.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 09장 상관관계와 타깃 분석하기](../09-chapter/chapter.md) · [11장 이상치와 잘못된 데이터 처리하기 →](../11-chapter/chapter.md)
