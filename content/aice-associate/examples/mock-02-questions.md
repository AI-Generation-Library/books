---
title: "자체 제작 모의고사 2회"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 자체 제작 모의고사 2회

공식 기출·샘플을 복제하지 않은 저자 작성 문제다. 90분 학습 연습이며 실제 합격·채점 결과와 다르다. examples 폴더에서 실행한다. 1~5번 각 6점, 6~10번 각 6점, 11~14번 각 10점의 자가평가 예시를 사용한다. 자동 확인 외에 요구조건과 그래프를 직접 대조한다.

## 01. 자료 불러오기 (6점)

data/service_usage.csv를 df에 읽고 첫 3행을 표시한다.

## 02. 품질 확인 (6점)

열별 결측 수 missing_counts와 record_id 중복 수 duplicate_count를 저장한다.

## 03. 집계 (6점)

plan별 행 수·usage_hours 평균을 plan_summary에 저장한다.

## 04. 조건 선택 (6점)

active_days가 15 이상인 행의 record_id·active_days·usage_hours를 selected에 저장한다.

## 05. 분포 그림 (6점)

전체 usage_hours의 히스토그램을 bins=15로 그리고 시간 단위 축 제목을 표시한다.

## 06. 입력·타깃 (6점)

숫자 active_users·active_days·storage_gb, 범주 plan·region을 X에 선택하고 usage_hours를 y로 둔다.

## 07. 분할 (6점)

훈련·검증·테스트 60·20·20, 두 단계 random_state=42로 나눈다. 연속 타깃에 stratify를 적용하지 않는다.

## 08. 숫자 결측 대체 (6점)

median_imputer를 훈련 숫자에만 학습하고 num_train·num_val·num_test를 만든다.

## 09. 표준화 (6점)

scaler를 num_train에만 학습하고 세 숫자 배열을 같은 기준으로 변환한다.

## 10. 원핫·결합 (6점)

새 범주 ignore·dense OneHotEncoder를 훈련 범주에 학습한다. 숫자와 합쳐 train_data·val_data·test_data를 만든다.

## 11. 회귀 학습 (10점)

LinearRegression을 reg로 학습하고 검증 예측 pred를 만든다.

## 12. 오차 평가 (10점)

검증 MAE mae·RMSE rmse·R² r2를 저장하고 잔차 actual−prediction을 residual에 저장한다.

## 13. 딥러닝 회귀 (10점)

훈련 타깃 평균·표준편차로 타깃을 변환한다. Input→Dense(16,relu)→Dense(1,linear), Adam(0.01), mse로 4 epoch 학습한다.

## 14. 역변환·그림 (10점)

검증 예측을 원래 시간 단위로 돌려 dl_pred·dl_rmse를 만들고 실제값 대 예측값 산점도를 그린다.

풀이 후 [해설](mock-02-solutions.md)과 비교하고 완료·오류·조건 누락과 시간을 기록한다.
