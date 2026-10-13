---
title: "04장. Jupyter 실습 환경 익히기"
description: "라이브러리·셀 실행·오류 확인과 처음부터 재실행을 연습한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 4
part: 1
---

# 04장. Jupyter 실습 환경 익히기

노트북은 설명과 코드, 결과를 함께 볼 수 있어 학습에 유용하다. 하지만 화면의 셀 순서와 실제 실행 순서가 다를 수 있다. 예전에 만든 변수가 남아 있으면 코드를 고쳤어도 정상처럼 보일 수 있다. 실습 완료 전에 새 커널에서 처음부터 실행한다.

## 1. 학습 환경을 분리하기

이 책의 다운로드에는 고정한 주요 의존성을 적은 `examples/requirements.txt`가 있다. 검증 환경은 Python 3.12와 CPU다. 로컬 가상환경에서 설치하고 노트북 커널이 그 환경을 사용하는지 확인한다. 시험 환경의 패키지 버전이 이 책과 같다고 가정하지 않는다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r examples/requirements.txt
.\.venv\Scripts\python.exe -m ipykernel install --user --name aice-book
```

마지막 명령은 로컬 Jupyter에 커널을 등록하는 선택 단계다. Colab을 사용한다면 파일 업로드·작업 위치와 라이브러리 버전을 확인한다. 시험에서는 임의 환경 설치보다 제공된 지시를 따른다.

## 2. 데이터와 작업 위치

책의 코드·노트북은 `examples` 디렉토리에서 실행하는 기준으로 작성했다. `lab.py`가 자체 경로의 `data` 폴더에서 CSV를 읽는다. 노트북을 다른 위치로 옮기면 필요한 코드와 자료를 함께 가져가거나 경로를 명시적으로 바꿔야 한다.

```python
from pathlib import Path
import sys
import pandas as pd
import sklearn
from lab import load_customers

print(sys.executable)
print(pd.__version__, sklearn.__version__)
df = load_customers()
assert df.shape == (600, 8)
assert Path("data/customers.csv").is_file()
print(df.head(2))
```

커널의 Python 경로와 설치한 Python 경로가 다르면 “설치했는데 import가 안 됨”이 발생할 수 있다. 무작정 여러 번 설치하기 전에 `sys.executable`을 확인한다.

## 3. 셀의 상태와 실행 순서

변수를 만드는 셀, 전처리 셀, 학습 셀, 평가 셀을 논리적인 순서로 배치한다. 데이터 로딩을 다시 실행하면 이미 처리한 DataFrame이 원본으로 바뀔 수 있다. 학습 셀만 재실행하면 이전 입력을 사용할 수도 있다.

실습에서는 구역을 나눠 이해한 뒤 처음부터 실행한다. 시험 답안의 셀 수와 저장 규칙은 공식 가이드와 문항에 따른다. 이 책의 노트북 셀 구성을 시험 답안 제출 규칙으로 옮기지 않는다.

## 4. 오류와 출력 관리

오류를 읽을 때 traceback의 마지막 메시지와 실제 코드 위치를 확인한다. 길이가 다른 입력·타깃, 잘못된 열 이름과 문자열 입력은 자주 발생한다. 디버깅 출력은 필요한 부분만 보이고 제출·공유 전에는 불필요한 출력과 임시 파일을 정리한다.

패키지 변경이 필요하다면 학습 환경에서 검증하고 버전을 기록한다. 다른 버전의 예제를 사용할 때는 `OneHotEncoder`의 인수명처럼 API 차이를 확인한다. 뒤의 코드가 요구하는 버전을 먼저 확인하면 무의미한 수정이 줄어든다.

## 연습과 해설

1. 파일은 있는데 `FileNotFoundError`가 난다. 첫 확인은? **해설:** 현재 작업 위치와 코드가 해석한 실제 경로를 확인한다.
2. 셀 하나를 삭제했는데 모델이 계속 학습된다. 왜 가능한가? **해설:** 커널에 이전 변수가 남아 있을 수 있다. 새 커널에서 전체 실행해 확인한다.

다음 부에서 DataFrame을 선택·집계하고 자료의 품질을 살펴본다.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 03장 실습에 필요한 Python과 NumPy](../03-chapter/chapter.md) · [05장 pandas로 데이터 불러오고 선택하기 →](../05-chapter/chapter.md)
