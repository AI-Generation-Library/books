---
title: "28장. 문제의 요구사항을 코드로 옮기기"
description: "변수명·조건·설정·출력을 체크 가능한 계약으로 바꾼다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 28
part: 6
---

# 28장. 문제의 요구사항을 코드로 옮기기

요구사항을 읽는 능력은 알고리즘 지식만큼 중요하다. 타깃, 행 조건, 변수명, 분할 설정과 저장 이름을 체크 가능한 목록으로 바꾼다. 익숙한 예제를 그대로 붙여 넣으면 현재 문항의 조건을 놓칠 수 있다.

## 1. 요구 계약 작성하기

예를 들어 “타깃은 churn, 식별자는 입력에서 제외, 지정 난수로 분할, 로지스틱 회귀 학습, 클래스 예측을 지정 파일에 저장”이라는 학습 문제를 생각한다. 입력·산출물·설정·저장을 따로 적는다. 파라미터 이름과 값도 표시한다.

| 분류 | 확인할 내용 | 코드 확인 |
| --- | --- | --- |
| 입력 | 파일·타깃·사용·제외 열 | columns·shape |
| 전처리 | 방법·대상·학습 범위 | fit 대상·변환 상태 |
| 학습 | 모델·변수·설정 | 객체·get_params |
| 결과 | 클래스·확률·지표 | 형태·dtype·범위 |
| 저장 | 파일명·확장자·열 | 재로딩·행 수·순서 |

## 2. 산출물을 검사하며 저장하기

```python
from pathlib import Path
import tempfile
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from lab import split_task, preprocessor, load_customers

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
clf = Pipeline([("prep",preprocessor()),("model",LogisticRegression(max_iter=1000))])
clf.fit(X_train,y_train)
pred = clf.predict(X_val)
score = accuracy_score(y_val,pred)
output = pd.DataFrame({"customer_id":load_customers().loc[X_val.index,"customer_id"].to_numpy(),
                       "prediction":pred})
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)/"predictions.csv"
    output.to_csv(path,index=False)
    saved = pd.read_csv(path)
    assert len(saved) == len(y_val)
    assert list(saved.columns) == ["customer_id","prediction"]
    assert saved["customer_id"].tolist() == output["customer_id"].tolist()
assert "churn" not in X_train.columns and "customer_id" not in X_train.columns
assert 0 <= score <= 1
print("Required outputs validated:",len(output),score)
```

여기서는 저장 동작을 연습하고 공유 폴더를 어지럽히지 않도록 임시 디렉토리를 사용했다. 실제 문항에서 파일을 저장해야 하면 지정 경로에 남겨야 하며 임시 폴더가 삭제되도록 제출하지 않는다. 학습 예제의 경로 선택과 실제 요구조건을 구분한다.

## 3. 한 문항의 상태를 다음과 연결하기

전처리 변수와 원본 자료를 이름으로 구분한다. 로딩 셀을 다시 실행해 이전 변환을 초기화했는지 확인한다. 앞 문항의 객체를 재사용하라는 요구가 있으면 새로 만들며 조건을 바꾸지 않는다.

공식 가이드와 실제 문항에 따라 답안 셀과 저장 방식을 맞춘다. 학습용 노트북은 구역을 나누지만 시험의 제출 규칙은 별개다. 파일명·확장자·변수명 규칙은 마지막에 추측해 맞추지 말고 처음 읽을 때 표시한다.

## 4. 부분 완료와 실행 오류

실행이 실패했다면 필요한 변수가 만들어졌는지 확인한다. 중간 결과가 없는데 다음 문항을 계속 실행하면 연쇄 오류가 생길 수 있다. 오류 원인을 좁혀 수정하고 관련 앞 단계부터 다시 실행한다. 제출 과정의 장애는 공식 감독·지원 경로를 따른다.

좋은 점수보다 요구조건 준수가 우선인 문항도 있다. 다른 모델로 바꾸어 높은 점수를 얻었어도 지정 모델·설정과 다르면 다른 답을 만든 것이다.

## 연습과 해설

1. 확률을 요구했는데 클래스 라벨을 저장하면? **해설:** 산출물 계약이 다르다. 라벨·확률의 정의와 열을 확인한다.
2. 결과 CSV에 ID를 붙일 때 첫 n개 ID를 쓰면? **해설:** 분할 후 순서와 다를 수 있다. 현재 입력 인덱스로 같은 순서의 ID를 선택한다.

다음 장에서 반복 실수를 정리하고 제한 시간 안의 확인 순서를 만든다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 27장 회귀 실습: 서비스 이용량 예측](../27-chapter/chapter.md) · [29장 실수 점검과 제한 시간 운영 →](../29-chapter/chapter.md)
