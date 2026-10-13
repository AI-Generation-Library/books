---
title: "자체 제작 모의고사 1회"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 자체 제작 모의고사 1회

공식 기출·샘플을 복제하지 않은 저자 작성 문제다. 90분 학습 연습이며 실제 합격·채점 결과와 다르다. examples 폴더에서 실행한다. 1~5번 각 6점, 6~10번 각 6점, 11~14번 각 10점의 자가평가 예시를 사용한다. 자동 확인 외에 요구조건과 그래프를 직접 대조한다.

## 01. 자료 불러오기 (6점)

data/customers.csv를 df에 읽고 첫 3행을 표시한다.

## 02. 구조 확인 (6점)

행·열 수를 shape_result에, 자료형을 dtype_result에 저장한다.

## 03. 결측 확인 (6점)

열별 결측 수를 missing_counts에 저장하고 내림차순으로 표시한다.

## 04. 조건 선택 (6점)

tenure_months가 12 이상인 행에서 customer_id·monthly_fee·churn을 selected에 저장한다.

## 05. 그룹 집계 (6점)

결측 계약 유형도 포함해 고객 수와 이탈 비율을 contract_summary에 저장한다.

## 06. 정의 위반 정리 (6점)

df 복사본 cleaned에서 음수 monthly_fee와 0~100 밖 last_usage를 결측으로 바꾼다. 큰 양수 요금은 유지한다.

## 07. 입력·타깃 (6점)

숫자 특성 tenure_months·monthly_fee·support_calls·last_usage, 범주 contract_type·region만 X로 선택하고 churn을 y에 저장한다.

## 08. 3분할 (6점)

훈련·검증·테스트 60·20·20 비율, 두 분할 random_state=42, stratify를 적용한다.

## 09. 숫자 변환 (6점)

numeric_prep에 중앙값 대체·StandardScaler를 연결하고 훈련에서만 fit한다. num_train·num_val·num_test를 만든다.

## 10. 범주 변환 (6점)

최빈값 대체·새 범주 ignore·dense 원핫을 category_prep에 연결한다. 숫자와 합쳐 train_data·val_data·test_data를 만든다.

## 11. 머신러닝 분류 (10점)

LogisticRegression(max_iter=1000)을 clf로 학습하고 검증 클래스 pred와 클래스 1 확률 prob를 만든다.

## 12. 지표 (10점)

검증 정확도 accuracy·F1 f1·ROC AUC auc와 [0,1] 순서 혼동행렬 cm을 저장한다.

## 13. 딥러닝 분류 (10점)

Input→Dense(16,relu)→Dense(1,sigmoid), Adam(0.01), binary_crossentropy로 model을 만들고 4 epoch·배치 32로 학습한다. 검증을 제공한다.

## 14. 딥러닝 평가·그림 (10점)

검증 확률을 0.5 기준 클래스로 바꿔 dl_f1을 계산하고 훈련·검증 손실을 범례와 함께 그린다.

풀이 후 [해설](mock-01-solutions.md)과 비교하고 완료·오류·조건 누락과 시간을 기록한다.
