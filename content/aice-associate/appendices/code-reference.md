---
title: "핵심 코드 찾아보기"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 핵심 코드 찾아보기

실행 맥락은 연결된 장을 확인한다. 아래는 탐색용 목록이며 코드 한 줄만 가져와 모든 입력에 적용하는 정답표가 아니다.

| 작업 | 찾아볼 도구·속성 | 장 |
| --- | --- | --- |
| 형태·유한값 | shape, np.isfinite | [3](../03-chapter/chapter.md) |
| 환경 | sys.executable, 버전 | [4](../04-chapter/chapter.md) |
| 선택 | loc, iloc, isin | [5](../05-chapter/chapter.md) |
| 집계·결합 | groupby, agg, merge(validate=...) | [6](../06-chapter/chapter.md) |
| 품질 | dtypes, isna, duplicated | [7](../07-chapter/chapter.md) |
| 그림 | subplots, histplot, countplot | [8](../08-chapter/chapter.md) |
| 타깃·상관 | value_counts, corr | [9](../09-chapter/chapter.md) |
| 대체 | SimpleImputer | [10](../10-chapter/chapter.md) |
| 범위·분위수 | between, quantile | [11](../11-chapter/chapter.md) |
| 범주 | OneHotEncoder, LabelEncoder | [12](../12-chapter/chapter.md) |
| 분할 | train_test_split | [13](../13-chapter/chapter.md) |
| 표준화 | StandardScaler | [14](../14-chapter/chapter.md) |
| 흐름 | Pipeline, ColumnTransformer | [15](../15-chapter/chapter.md) |
| 기준 | DummyClassifier | [16](../16-chapter/chapter.md) |
| 분류 | LogisticRegression, DecisionTreeClassifier | [17](../17-chapter/chapter.md) |
| 회귀 | LinearRegression, DecisionTreeRegressor | [18](../18-chapter/chapter.md) |
| 앙상블 | RandomForest, GradientBoosting | [19](../19-chapter/chapter.md) |
| 설정 비교 | GridSearchCV, StratifiedKFold | [20](../20-chapter/chapter.md) |
| 평가 | classification_report, confusion_matrix | [21](../21-chapter/chapter.md) |
| 신경망 | Input, Dense, compile, fit | [22~24](../22-chapter/chapter.md) |
| 학습 조절 | History, EarlyStopping, Dropout | [25](../25-chapter/chapter.md) |

## 함수의 역할

`fit`은 상태를 학습하고 `transform`은 학습된 변환을 적용한다. `predict`는 모델 예측, `predict_proba`는 지원 모델의 클래스 확률이다. 모델의 `score` 기본 지표와 직접 계산한 지표를 구분한다. `summary`는 구조 정보이며 학습 완료가 아니다.

문항에서 지정한 변수·파일·설정과 설치 버전의 API를 대조한다. 이 자료가 시험 중 허용되는지는 최신 공식 규정을 확인한다.
