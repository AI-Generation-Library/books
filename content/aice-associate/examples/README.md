---
title: "코드·데이터·노트북 사용 안내"
description: ""
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 코드·데이터·노트북 사용 안내

다운로드 ZIP의 `examples` 폴더에서 실행한다. 자체 제작 분류·회귀 자료와 완성된 모의고사 해설을 포함한다. AI API 키와 외부 데이터 다운로드는 필요하지 않다. 라이브러리 설치에는 패키지 다운로드가 필요할 수 있다.

## 파일

| 자료 | 내용 |
| --- | --- |
| [데이터 사전](data-dictionary.md) | 3개 CSV의 열·가정·품질 |
| [데이터 생성기](create_data.py) | 가상 자료 재생성 |
| [공통 실습 함수](lab.py) | 로딩·정리·분할·변환·Keras 학습 |
| [주요 의존성](requirements.txt) | 고정 버전 |
| [자동 검사](test_lab.py) | 분할·대체·범주·형태의 경계 |
| [1회 문제](mock-01-questions.md) / [해설](mock-01-solutions.md) | 분류 14문항 |
| [2회 문제](mock-02-questions.md) / [해설](mock-02-solutions.md) | 회귀 14문항 |
| notebooks/ | 파트별 예제 7개·모의 답안 2개·해설 2개 |

책의 장 코드와 파트별 노트북은 같은 Python 블록을 사용한다. 각 장은 필요한 입력을 새로 준비하므로 장 순서에 맞춰 읽되 코드는 독립적으로 실행할 수 있다. 모의고사 해설은 Q01부터 차례로 실행해야 한다.

## 설치·실행

ZIP의 책 루트에서 가상환경을 만들고 requirements를 설치한다. 4장의 커널 등록을 선택한 뒤 노트북에서 그 커널을 고른다. 실행 디렉토리는 `examples`다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r examples/requirements.txt
cd examples
..\.venv\Scripts\python.exe -B -m unittest discover -s . -p "test_*.py" -v
..\.venv\Scripts\python.exe -B mock-01-solution.py
..\.venv\Scripts\python.exe -B mock-02-solution.py
```

노트북 첫 셀은 `examples` 또는 그 아래 `notebooks`에서 실행한 경우 공통 코드·데이터를 찾도록 구성한다. 다른 폴더로 파일 하나만 옮기면 전체 실습 구조가 없어질 수 있다. 원고 ZIP과 코드 ZIP 모두 원래 폴더 관계를 유지한다.

## 노트북 구분

`part-01`~`part-07`은 완성된 장 예제다. `mock-01-practice`·`mock-02-practice`는 문제와 직접 작성할 답안 셀을 가진 학습지다. `mock-01-solutions`·`mock-02-solutions`는 완성된 풀이이며 독립 풀이 후 확인한다. 배포 노트북의 결과는 비워 두어 새 실행을 유도한다.

학습용 다중 셀 구성은 실제 시험 답안 제출 규칙이 아니다. 공식 가이드·문항에 따라 셀·변수·파일명을 맞춘다. 자체 배점·검사는 실제 채점 규칙이나 합격 보장이 아니다.

## 실행과 결과

Python 3.12·CPU에서 고정 주요 의존성으로 검사한다. 숫자는 난수·라이브러리·하드웨어에 따라 달라질 수 있으므로 가상 자료에서의 실행 범위를 기록한다. 판정은 행·열·학습 범위·출력·유한값 등 요구조건 중심이며 특정 정확도를 실제 사업 성과로 주장하지 않는다.

검사 상세와 확인 범위는 [검증 기록](../appendices/verification.md)에 있다. 외부 공식 시험 서버·감독 환경에서 이 코드를 실행한 기록은 아니다.
