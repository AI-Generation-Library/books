---
title: "오류 메시지별 해결 순서"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 오류 메시지별 해결 순서

| 오류·증상 | 확인 | 설명 |
| --- | --- | --- |
| ModuleNotFoundError | sys.executable·설치 환경 | 커널과 설치 Python이 다를 수 있음 |
| FileNotFoundError | 작업 폴더·파일명·확장자 | 노트북 위치와 데이터 구조 확인 |
| KeyError | columns·공백·대소문자 | 원본과 전처리 변수 혼동 확인 |
| could not convert string | 자료형·범주 열 | 문자열 인코딩 대상 점검 |
| Input contains NaN | 결측·변환 순서 | 대체·타깃 결측·학습 상태 확인 |
| inconsistent numbers of samples | 행 필터·정렬·분할 | X·y의 인덱스·길이 확인 |
| Expected 2D array | shape | 하나의 특성도 2차원 입력일 수 있음 |
| feature names mismatch | 원핫·선택·순서 | 훈련 변환과 입력 계약 유지 |
| NotFittedError | 실제 사용 객체·실행 순서 | 다른 모델을 fit했는지 확인 |
| ConvergenceWarning | 입력 스케일·반복·설정 | 경고를 숨기지 말고 원인 점검 |
| NaN loss | 유한값·스케일·손실 조합 | 전처리·라벨·학습률 확인 |
| 모든 클래스가 0 | sigmoid·argmax·불균형 | 출력 해석과 임계값 확인 |
| 그림의 한글 깨짐 | 폰트·환경 | 검증 그림은 영어 레이블 사용 |

오류 문자열은 라이브러리 버전에 따라 달라질 수 있다. 실패 줄과 전체 traceback의 마지막 메시지, 관련 입력의 형태·자료형을 함께 확인한다. 설명을 인터넷에서 찾더라도 현재 버전의 공식 API와 실제 입력으로 검증한다.

## 수정 후 확인

필요한 앞 단계부터 다시 실행하고 원본·변환·모델 객체가 맞는지 본다. 학습 완료 전에 새 커널에서 전체 순서를 확인한다. 시험 중 장애·재시작·제출 행동은 공식 감독·가이드의 지시를 따른다.

형태 검사 통과가 자료 시점·도메인·테스트 선택 누수까지 해결하지는 않는다. 판단 오류는 [분할](../13-chapter/chapter.md)·[누수](../14-chapter/chapter.md)·[요구사항](../28-chapter/chapter.md)의 설명과 함께 검토한다.
