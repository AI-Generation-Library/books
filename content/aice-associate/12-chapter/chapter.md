---
title: "12장. 범주형 변수 인코딩하기"
description: "라벨·원핫 인코딩과 새로운 범주를 처리한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 12
part: 3
---

# 12장. 범주형 변수 인코딩하기

모델은 문자열을 그대로 받지 못하는 경우가 많다. 범주를 숫자로 바꾸되 실제로 없는 순서와 거리 의미를 만들지 않도록 선택한다. 훈련과 예측 자료의 범주가 다를 수 있다는 점도 준비해야 한다.

## 1. 라벨과 입력의 차이

`LabelEncoder`는 주로 타깃 라벨을 정수로 변환할 때 사용한다. 입력의 순서 있는 범주에는 순서를 명시한 인코딩을 검토할 수 있다. 순서 없는 계약 유형을 0·1·2로 바꾸면 일부 모델이 그 숫자의 순서를 이용할 수 있다.

문제에서 특정 인코딩을 요구하면 조건을 따른다. 어떤 변수에 적용하는지와 변환 결과를 확인한다. 단순히 모든 문자 열에 같은 코드를 반복하지 않는다.

## 2. 원핫 인코딩과 새로운 범주

```python
import numpy as np
from sklearn.preprocessing import OneHotEncoder, LabelEncoder

train = np.array([["monthly"], ["yearly"], ["monthly"]])
new = np.array([["trial"]])
encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
encoded = encoder.fit_transform(train)
unknown = encoder.transform(new)
assert encoded.shape == (3, 2)
assert unknown.shape == (1, 2)
assert unknown.sum() == 0
labels = LabelEncoder().fit_transform(["stay", "leave", "stay"])
assert len(set(labels)) == 2
print(encoder.get_feature_names_out(), encoded, labels)
```

학습하지 않은 범주를 무시하면 이 예에서는 해당 특성의 원핫 값이 모두 0이 된다. 이것이 새 범주를 이해했다는 뜻은 아니다. 운영에서는 새 범주의 의미와 빈도를 확인하고 필요하면 변환을 갱신한다.

## 3. 열의 일관성

훈련·테스트에 각각 `get_dummies`를 실행하면 열 집합이 달라질 수 있다. 학습한 encoder를 재사용하거나 훈련 열 기준으로 일관되게 정렬한다. 열 수만 같아도 열의 의미와 순서가 다르면 모델 입력이 잘못된다.

기준 범주 하나를 제거하는 방식은 특정 선형 모델의 해석과 중복 열 처리에 도움이 될 수 있다. 그러나 새 범주를 모두 0으로 처리하면 제거한 기준 범주와 구분되지 않을 수 있다. `drop`과 `handle_unknown`의 조합을 이해하고 선택한다. 이 책 기본 예는 범주를 제거하지 않는다.

## 4. 결측과 희소 배열

범주의 결측은 대체 후 인코딩하거나 별도 범주로 다룰 수 있다. 결측과 실제 문자열 `'missing'`이 의미상 같은지 확인한다. 많은 범주는 열 수를 크게 늘릴 수 있으며 희소 표현이 메모리에 유리할 수 있다.

이 책의 `sparse_output=False`는 작은 가상 자료와 딥러닝의 dense 입력을 단순화하는 선택이다. 큰 실제 자료에서 같은 설정을 적용하면 메모리 사용이 커질 수 있다. 설치 버전에 따라 인수명이 다를 수 있으므로 공식 문서와 버전을 확인한다.

## 연습과 해설

1. 두 자료의 원핫 열 수가 같으면 항상 안전한가? **해설:** 열 이름과 순서, 학습한 범주가 일치하는지도 확인한다.
2. 새 범주를 `ignore`하면 모델이 의미를 학습한 것인가? **해설:** 오류를 피하는 출력 규칙이며 의미 학습은 아니다.

다음 장에서는 변환의 학습 범위를 결정하는 데이터 분할을 다룬다. 참고: [OneHotEncoder 공식 API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 11장 이상치와 잘못된 데이터 처리하기](../11-chapter/chapter.md) · [13장 훈련·검증·테스트 데이터 나누기 →](../13-chapter/chapter.md)
