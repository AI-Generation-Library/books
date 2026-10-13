---
title: "05장. pandas로 데이터 불러오고 선택하기"
description: "CSV·DataFrame·행과 열 선택·조건 필터링을 수행한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 5
part: 2
---

# 05장. pandas로 데이터 불러오고 선택하기

DataFrame은 행과 열의 이름을 가진 표다. 파일을 읽었다면 행 수, 열 이름, 자료형과 몇 개의 값을 확인한다. 문제에 없는 열을 가정하거나 다른 파일을 읽은 채 진행하면 모델 단계까지 잘못된 흐름을 이어갈 수 있다.

## 1. 읽은 표의 의미 확인하기

`read_csv`는 파일의 구분자·인코딩·헤더와 자료형에 영향을 받는다. ID가 숫자로 저장되어 있어도 계산할 특성이 아닐 수 있다. 앞의 5행만 보고 품질을 확정하지 말고 전체 형태와 결측·중복을 확인한다.

이 책의 고객 자료는 600행·8열이다. `customer_id`는 식별자, `churn`은 이진 타깃, 나머지는 설명 변수다. 실제 고객이 아닌 가상 독립 행이다. [데이터 사전](../examples/data-dictionary.md)을 먼저 읽는다.

## 2. 이름과 위치로 선택하기

`loc`는 라벨과 조건으로, `iloc`는 정수 위치로 선택한다. `df['monthly_fee']`는 Series이고 `df[['monthly_fee']]`는 DataFrame이다. 모델의 한 특성을 선택할 때는 2차원 형태를 유지해야 할 수 있다.

```python
from lab import load_customers

df = load_customers()
columns = ["customer_id", "tenure_months", "monthly_fee"]
selected = df.loc[df["tenure_months"] >= 12, columns]
first = df.iloc[:3, :2]
single = df[["monthly_fee"]]
assert single.shape == (600, 1)
assert selected["tenure_months"].ge(12).all()
assert list(first.columns) == ["customer_id", "tenure_months"]
print(selected.head())
```

같은 숫자라도 행 라벨과 위치는 다를 수 있다. 필터 후 인덱스가 0부터 연속이 아니어도 오류는 아니다. 원래 행과 타깃을 연결하는 중요한 정보일 수 있다.

## 3. 조건을 결합하기

여러 조건은 각각 괄호로 묶고 `&`, `|`를 사용한다. `and`와 `or`는 Series 전체의 조건 결합에 맞지 않는다. 포함 여부는 `isin`, 결측은 `isna`로 표현한다. 금액이 결측인 행을 숫자 비교에서 제외할지 별도 처리할지 정한다.

한 조건이 모든 행에 적용되는지, 행마다 적용되는지 구분한다. `df['churn'].eq(1)`은 행별 마스크이며 `.all()`과 `.any()`는 하나의 판단으로 줄인다. 결과가 비어 있을 수도 있으므로 행 수를 확인한다.

## 4. 수정은 명시적으로 하기

연속된 선택을 여러 번 이어서 대입하면 원본을 수정했는지 애매해질 수 있다. `df.loc[조건, '열'] = 값`처럼 한 번에 지정하거나 작업용 복사본을 만든다. pandas 버전별 동작 차이가 있으므로 경고를 무시하지 않는다.

원본 데이터를 다시 사용할 계획이면 `copy()`로 분리한다. 변수 이름도 `raw`, `cleaned`, `X_train`처럼 목적을 드러낸다. 같은 `df`를 계속 덮어쓰면 무엇을 평가하고 있는지 추적하기 어렵다.

## 5. 문제의 선택 조건을 대조하기

“12개월 이상”은 `>=12`, “12개월 초과”는 `>12`다. 제외할 열과 유지할 열도 구분한다. 먼저 조건 문장을 코드로 옮기고 경계값이 포함되는지 작은 예시로 확인한다. 행 필터 후 타깃을 다른 순서로 가져오지 않는다.

## 연습과 해설

1. `df.iloc[:3]`은 몇 행인가? **해설:** 위치 0·1·2의 세 행이다.
2. 한 열의 2차원 입력을 만들려면? **해설:** 이중 대괄호로 DataFrame을 선택하고 `shape`를 확인한다.

다음 장에서 행을 묶고 다른 표와 결합한다. 참고: [pandas 선택 공식 안내](https://pandas.pydata.org/docs/getting_started/intro_tutorials/03_subset_data.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 04장 Jupyter 실습 환경 익히기](../04-chapter/chapter.md) · [06장 데이터 집계와 결합하기 →](../06-chapter/chapter.md)
