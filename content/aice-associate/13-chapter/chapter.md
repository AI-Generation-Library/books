---
title: "13장. 훈련·검증·테스트 데이터 나누기"
description: "입력·타깃·분할·층화·시간 순서를 구분한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 13
part: 3
---

# 13장. 훈련·검증·테스트 데이터 나누기

훈련 자료는 모델과 변환을 학습하는 데, 검증 자료는 설정을 비교하는 데, 테스트 자료는 최종 확인에 사용한다. 이름만 세 개로 나눈 뒤 테스트 결과를 반복해서 보며 설정을 고르면 독립적인 최종 평가가 되지 않는다.

## 1. 입력과 타깃 분리

고객 이탈 자료의 타깃은 `churn`이다. 입력에서는 타깃과 `customer_id`를 제외한다. 열 목록을 명시하면 자료에 새 열이 추가되어도 임의로 입력에 들어가지 않는다. 행을 선택하거나 정렬할 때 입력과 타깃의 대응을 유지한다.

```python
from sklearn.model_selection import train_test_split
from lab import load_customers, clean_customers, NUM_CLASS, CAT_CLASS

df = clean_customers(load_customers())
X = df[NUM_CLASS+CAT_CLASS]
y = df["churn"]
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev, test_size=0.25, random_state=42, stratify=y_dev)
assert (len(X_train), len(X_val), len(X_test)) == (360, 120, 120)
assert set(X_train.index).isdisjoint(X_val.index)
assert set(X_train.index).isdisjoint(X_test.index)
assert X_train.index.equals(y_train.index)
print(len(X_train), len(X_val), len(X_test))
```

두 번째 분할의 0.25는 남은 80%의 25%이므로 전체의 20%가 검증에 들어간다. 전체 비율은 60·20·20이다. `random_state`를 고정해 같은 비교 분할을 만들지만 환경을 초월한 모든 모델 결과의 완전 동일성을 보장하지 않는다.

## 2. 층화와 표본 수

분류에서 `stratify=y`는 클래스 비율을 비슷하게 유지하는 데 도움이 된다. 클래스 표본이 너무 적으면 분할이 실패하거나 안정적인 평가가 어려울 수 있다. 연속 타깃의 모든 숫자를 그대로 층화 라벨로 쓰지 않는다.

문제에서 Train/Test만 요구하면 그 구조와 지정 비율·난수를 따른다. 검증이나 교차검증을 추가할 때에는 요구한 산출물과 조건을 바꾸지 않도록 구분한다. 이 책의 3분할은 모델 비교의 원칙을 배우는 실습 구성이다.

## 3. 시간과 그룹

미래 기간 예측에서는 훈련보다 뒤의 기간을 평가에 두는 방식이 필요할 수 있다. 무작위 분할로 미래 정보가 과거 학습에 섞이지 않는지 확인한다. 같은 고객·장비가 반복되는 자료라면 그룹 분할도 고려한다.

이 책의 서비스 이용량 자료는 독립적인 가상 서비스 관측이며 시계열 데이터가 아니다. 이름에 이용량이 있다고 실제 월별 시계열을 가정하지 않는다. 실제 적용 시 행의 단위와 예측 시점에 맞게 분할을 다시 설계한다.

## 4. 분할 다음에 학습할 것

고정된 자료 정의 위반의 정리는 분할 전에도 적용할 수 있지만, 중앙값·스케일·분위수·특성 선택처럼 데이터에서 계산하는 처리는 훈련에서 학습한다. 검증·테스트에는 그 변환을 적용한다. 전체 자료를 먼저 정규화한 뒤 나누는 실수를 피한다.

## 연습과 해설

1. 1000행에서 테스트 20%, 남은 자료의 검증 25%면? **해설:** 훈련 600·검증 200·테스트 200행이다.
2. 같은 고객의 여러 행이 서로 다른 집합에 있으면? **해설:** 고객 특성을 기억해 평가가 낙관적일 수 있다. 목적에 맞는 그룹·기간 분할을 검토한다.

다음 장에서 훈련 범위 안에서 스케일을 학습한다. 참고: [train_test_split 공식 API](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 12장 범주형 변수 인코딩하기](../12-chapter/chapter.md) · [14장 스케일링과 데이터 누수 방지하기 →](../14-chapter/chapter.md)
