---
title: "15장. 전처리 흐름 완성하기"
description: "열 구성과 변환을 일관되게 유지하는 파이프라인을 만든다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 15
part: 3
---

# 15장. 전처리 흐름 완성하기

숫자는 대체·스케일링, 범주는 대체·원핫 인코딩을 적용할 수 있다. 서로 다른 열의 변환을 연결하고 모델과 함께 학습하면 전처리를 빠뜨리는 실수를 줄일 수 있다. 입력 계약과 평가 자료의 역할도 유지해야 한다.

## 1. ColumnTransformer와 Pipeline

`ColumnTransformer`는 열 그룹마다 다른 변환을 적용한다. `Pipeline`은 앞 단계의 출력을 다음 단계로 이어 준다. 모델까지 묶으면 `fit`에서 훈련 변환과 모델을 학습하고 `predict`에서 같은 변환을 적용한다.

```python
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
model = Pipeline([("prep", preprocessor()),
                  ("clf", LogisticRegression(max_iter=1000))])
model.fit(X_train, y_train)
prediction = model.predict(X_val)
features = model.named_steps["prep"].get_feature_names_out()
assert len(prediction) == len(y_val)
assert len(features) == model.named_steps["clf"].n_features_in_
assert np.isfinite(model.named_steps["prep"].transform(X_val)).all()
print(features)
```

`lab.preprocessor()`는 숫자 중앙값·표준화와 범주 최빈값·원핫을 묶은 학습용 함수다. [lab.py](../examples/lab.py)의 구현을 읽고 같은 구성을 직접 작성해 본다. 이름만 호출할 수 있는 것과 각 단계의 의미를 이해하는 것은 다르다.

## 2. 입력 계약 유지하기

새 자료에 필요한 열이 있는지, 자료형과 단위가 맞는지 확인한다. 열이 없다는 오류를 피하려고 임의 0열을 추가하지 않는다. 누락이 허용된 값인지 입력 자체가 잘못된 것인지 구분한다.

열 이름 기반 선택은 입력 열 순서의 일부 변화에 대응할 수 있지만, 같은 이름의 의미나 단위가 바뀌면 여전히 문제가 생긴다. 자료 사전과 원본·변환본의 역할을 유지한다.

## 3. 교차검증에서의 변환

파이프라인을 교차검증에 전달하면 각 훈련 폴드 안에서 변환을 다시 학습한다. 전체 자료를 미리 변환한 배열을 교차검증에 넣으면 검증 폴드 정보가 섞일 수 있다. 이 차이는 20장에서 직접 확인한다.

설정을 바꿀 때는 단계 이름과 인수명을 연결해 `clf__C`처럼 지정한다. 파이프라인 안의 모델과 바깥 변수의 다른 모델을 혼동하지 않는다. 어떤 객체가 최종 예측에 사용되는지 확인한다.

## 4. 순서와 자료 추적

학습 후 원래 입력 DataFrame에 예측을 붙일 때 인덱스를 확인한다. 배열로 바뀌면 원래 행 라벨이 사라지므로 별도로 보존할 수 있다. 결과 저장에 ID를 포함할 때는 예측과 같은 행 순서에서 가져온다.

문제에서 수작업 단계별 변수 생성과 특정 전처리를 요구하면 그 조건을 따른다. 파이프라인은 학습을 정리하는 도구이며 지정된 문제를 다른 인터페이스로 바꾸라는 뜻은 아니다.

## 연습과 해설

1. 교차검증 전에 전체 자료를 중앙값으로 채우면? **해설:** 폴드 검증 부분의 정보가 대체 통계에 포함될 수 있다.
2. 모델 객체가 여러 개일 때 결과를 어떻게 추적하는가? **해설:** 명확한 변수명, 단계 이름과 학습·평가 기록을 사용한다.

다음 부에서는 이 입력을 기준 모델부터 머신러닝 학습으로 연결한다. 참고: [ColumnTransformer 공식 API](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 14장 스케일링과 데이터 누수 방지하기](../14-chapter/chapter.md) · [16장 머신러닝 학습의 기본 흐름 →](../16-chapter/chapter.md)
