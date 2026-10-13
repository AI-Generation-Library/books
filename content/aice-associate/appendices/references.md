---
title: "공식 자료와 확인 범위"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 공식 자료와 확인 범위

확인일: 2026-10-13. 본문·자체 데이터·문항·해설은 저자 작성이다. 외부 공식 자료의 전체 코드·데이터·이미지를 복제하지 않고 필요한 API·개념과 안내를 확인했다.

## AICE

- [Associate 소개·출제범위](https://aice.study/info/aice/asso): 브라우저에서 14문항·90분·80점, 제한적 오픈북·Jupyter와 분석·전처리·모델링의 영역·배점을 확인했다.
- [수험자 가이드](https://aice.study/certi/examGuide): Associate 탭의 응시 중 유의사항 이미지에서 로딩·커널, 답안 셀과 파일명·확장자 안내를 확인했다. 공통·등급·회차의 모든 금지·허용 조건을 이 책에서 완전 재현한 것은 아니다. 실제 응시 전에 전체 최신 안내를 직접 확인한다.
- [공식 일정](https://aice.study/certi/examSchedule): 회차별 일정의 공식 확인 경로다. 책에 일정·요금을 고정하지 않는다.
- [공개 샘플 경로](https://aice.study/certi/practice): 공식 학습 자료를 제공 조건에 맞춰 직접 확인하는 경로다. 이 책의 모의고사에 해당 문제를 복제하지 않았다.

## 데이터·시각화

- [pandas 시작 안내](https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html), [선택](https://pandas.pydata.org/docs/getting_started/intro_tutorials/03_subset_data.html), [결합](https://pandas.pydata.org/docs/user_guide/merging.html): 표 선택·집계·결합 관련 API 확인.
- [Matplotlib 시작 안내](https://matplotlib.org/stable/users/explain/quick_start.html), [Seaborn 분포 안내](https://seaborn.pydata.org/tutorial/distributions.html): Figure·Axes와 분포 그림 API 확인.

## 전처리·모델·평가

- [scikit-learn 흔한 오류](https://scikit-learn.org/stable/common_pitfalls.html): 전처리 일관성·훈련 범위·누수와 난수 관련 참고.
- [결측 처리](https://scikit-learn.org/stable/modules/impute.html), [OneHotEncoder](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html), [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html): 학습 상태·변환·인수 확인.
- [train_test_split](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html), [ColumnTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html): 분할·열별 변환 API 확인.
- [평가 지표](https://scikit-learn.org/stable/modules/model_evaluation.html): 지표의 입력·평균·단위·점수 방향 관련 참고.
- [TensorFlow 학습 안내](https://www.tensorflow.org/tutorials/keras/classification), [Keras Sequential](https://keras.io/guides/sequential_model/), [확률 손실](https://keras.io/api/losses/probabilistic_losses/), [EarlyStopping](https://keras.io/api/callbacks/early_stopping/): 구성·손실·학습·콜백 관련 API 확인. 이미지 데이터 예제 자체를 이 책의 정형 자료에 복제하지 않았다.

공식 문서의 현재 안정 버전과 책의 고정 실행 버전은 다를 수 있다. 실제 예제는 `requirements.txt`에 적은 환경에서 실행해 확인하고 그 버전을 검증 기록에 남긴다. 시험 제공 환경에서는 해당 API·문항 조건을 우선 확인한다.

외부 자료와 라이브러리는 원출처의 라이선스를 따른다. 책의 CC0 배포가 외부 자료의 이용 조건을 바꾸지 않는다. 공식 시험·브랜드의 승인 교재라고 표시하지 않는다.
