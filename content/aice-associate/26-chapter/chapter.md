---
title: "26장. 분류 실습: 고객 이탈 예측"
description: "정형 가상 데이터로 탐색부터 최종 평가까지 연결한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 26
part: 6
---

# 26장. 분류 실습: 고객 이탈 예측

이 장은 앞의 여러 작업을 하나의 실험으로 연결한다. 600행 가상 고객 자료에서 이탈 여부를 예측한다. 실제 고객과 사업 성과를 검증하는 프로젝트가 아니라, 입력·타깃·전처리·모델 선택·평가의 관계를 익히는 학습 실습이다.

## 1. 문제와 자료

타깃은 `churn`, 1은 이탈이다. ID를 제외한 허용 특성만 사용한다. 원자료의 음수 요금·이용 지수는 데이터 사전의 고정 조건에 따라 결측으로 바꾼다. 큰 요금은 자동 삭제하지 않고 분석 대상으로 남긴다.

훈련 360·검증 120·테스트 120행을 사용한다. 훈련에서 대체·스케일·범주를 학습한다. 검증 F1으로 두 후보를 비교하며 같은 분할과 지표를 유지한다. 선택 후 개발 자료로 다시 학습하고 최종 테스트를 평가한다.

## 2. 전체 실행

```python
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report
from lab import split_task, preprocessor

X_train, X_val, X_test, y_train, y_val, y_test = split_task()
candidates = {
    "logistic":LogisticRegression(max_iter=1000),
    "forest":RandomForestClassifier(n_estimators=80,max_depth=6,random_state=42,n_jobs=1),
}
scores = {}
for name, estimator in candidates.items():
    model = Pipeline([("prep",preprocessor()),("clf",estimator)]).fit(X_train,y_train)
    scores[name] = f1_score(y_val,model.predict(X_val),zero_division=0)
winner = max(scores,key=scores.get)
X_dev = pd.concat([X_train,X_val])
y_dev = pd.concat([y_train,y_val])
final = Pipeline([("prep",preprocessor()),("clf",candidates[winner])])
final.fit(X_dev,y_dev)
prediction = final.predict(X_test)
assert X_dev.index.equals(y_dev.index)
assert len(prediction) == len(y_test) == 120
print("Validation:",scores,"selected:",winner)
print(classification_report(y_test,prediction,zero_division=0))
```

최종 학습에서 전처리를 새로 개발 자료에 맞춘 이유는 테스트를 보지 않고 사용할 학습 자료가 늘었기 때문이다. 검증용으로 학습한 변환에 테스트를 별도로 `fit`하지 않는다.

## 3. 결과 해석

검증에서 선택한 모델의 테스트 점수가 반드시 더 좋을 필요는 없다. 표본과 선택의 변동이 있기 때문이다. 두 클래스의 오류와 지표를 기록하고, 테스트 결과를 보고 같은 테스트에 맞춰 설정을 계속 바꾸지 않는다.

이 책의 다른 장은 같은 가상 자료를 여러 개념의 독립 연습에 사용한다. 장마다 얻는 테스트 수치를 실제 독립 벤치마크 여러 회로 합치지 않는다. 실제 실험에서는 최종 평가의 사용 이력을 관리해야 한다.

## 4. 저장과 재실행

예측 파일을 저장한다면 테스트 행의 ID를 같은 인덱스로 가져온다. 전체 원자료의 첫 120개 ID를 붙이면 잘못된 고객과 예측이 연결된다. 파일명·열 이름·확장자가 지정되면 그대로 따른다.

새 커널에서 처음부터 실행하며 선택 모델과 입력 목록, 분할·지표를 기록한다. 값이 달라졌다면 버전·난수·데이터 변경을 확인한다. 이 실습의 점수는 가상 자료에서의 교육용 결과다.

## 연습과 해설

1. 검증 승자를 선택한 뒤 테스트로 두 후보를 다시 고르면? **해설:** 테스트가 추가 선택에 사용되어 독립 확인의 의미가 약해진다.
2. 테스트 예측에 ID를 붙일 때 기준은? **해설:** 테스트 입력의 인덱스와 같은 행 순서다.

다음 장은 연속값 회귀에서 같은 흐름을 수행한다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 25장 학습 곡선과 성능 개선하기](../25-chapter/chapter.md) · [27장 회귀 실습: 서비스 이용량 예측 →](../27-chapter/chapter.md)
