---
title: "03장. 가장 작은 RAG 파이프라인 만들기"
description: "색인과 질문 흐름을 독립적으로 실행한다. 출처를 추적하는 응답 구조를 만든다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 3
part: 1
enableToc: true
---

# 03장. 가장 작은 RAG 파이프라인 만들기

## 학습 목표

- 색인과 질문 흐름을 독립적으로 실행한다.
- 출처를 추적하는 응답 구조를 만든다.

## 최소 구현의 구성 요소

문서 몇 개를 읽고 청크로 나눈 뒤, 질문과 관련된 청크를 선택한다. 선택한 근거를 생성기에 넘기고 응답에 사용한 청크 ID와 원문 위치를 연결한다. 이 흐름을 작은 함수로 분리하면 한 단계의 개선을 다른 단계와 독립적으로 시험할 수 있다.

```python
from ragbook.cli import make_engine
from ragbook.data import Principal
engine = make_engine('var/index-demo.sqlite3')
reader = Principal('acme', frozenset({'reader'}))
result = engine.answer('연차 휴가는 며칠인가요?', reader)
print(result['generator'], result['answer'])
```

먼저 CLI의 index 명령으로 자료를 넣어야 한다. import만으로 서버를 열거나 외부 모델을 내려받지 않게 했다. 신경망 embedding이나 Ollama 모델은 명시적으로 선택할 때만 연결한다.

## 문서에서 응답까지 ID를 잇는다

문서 ID는 업무상 같은 자료를 가리키고, version은 개정판을 가리킨다. 청크 ID는 tenant·문서·버전·메타데이터·본문 위치와 내용을 반영한다. 답변에 문서 제목만 넣으면 어떤 버전의 어느 문장이 근거였는지 재현하기 어렵다.

응답은 answer·claims·citations·generator·abstained를 구분한다. 각 claim에는 사용한 chunk_id와 quote를 둔다. citations는 문서 ID·버전·source·정규화 본문의 start/end를 제공한다. PDF 화면 좌표를 저장한 구현은 아니므로 그 범위를 과장하지 않는다.

## 생성 전후의 검사

질문의 사용자 권한으로 후보를 좁힌 뒤 검색한다. 검색 후 필터만 적용하면 비인가 문서가 랭커·외부 모델·로그에 먼저 들어갈 수 있다. 선택한 근거만 컨텍스트로 전달하고 모델이 지어낸 출처 ID는 거부한다.

생성 중 문서가 삭제되거나 권한이 회수될 수도 있다. 예제는 반환 직전에 현재 허용 청크 ID를 다시 확인해 이전 근거가 바뀌었으면 context_changed로 거절한다. 이것은 검사 시점의 보호이며 분산 시스템 전체의 원자적 권한 변경 프로토콜을 구현했다는 뜻은 아니다.

## 작은 구현에서 먼저 볼 실패

빈 질문·없는 근거·잘못된 인용·권한 없는 자료·수정된 버전·모델 연결 오류를 각각 확인한다. 정상 질문 하나가 맞았다는 사실과 모든 질문에 신뢰할 수 있다는 주장을 구분한다. 이 작은 경계를 고정한 뒤 검색 모델과 프레임워크를 교체한다.

기본 발췌 생성기는 원문을 그대로 반환하므로 검색·인용 연결을 확인하기 쉽다. 실제 LLM은 문장을 바꾸고 종합할 수 있어 의미적 뒷받침 평가가 추가된다. 두 단계의 결과를 같은 정확도 표에 무심코 합치지 않는다.

## 실습과 평가

index → query → search API → query API 순서로 실행한다. API는 `python serve.py`로 열고 학습용 reader 토큰을 사용한다. 정확한 설치·인증 예시는 예제 README를 따른다.

`python -m unittest discover -s tests -v`에서 잘못된 인용·문서 삭제·권한 회수 시 응답을 막는 테스트를 찾는다. 함수마다 어떤 불변식을 유지하는지 표시한다.

## 확인 문제

프롬프트에 넘긴 문서가 답변 생성 도중 삭제되었다. 최초 검색 때 허용되었으므로 그대로 응답해도 되는가?

[해설](../appendices/answers.md#장-03)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [sqlite3 — DB-API 2.0 interface for SQLite databases — Python 3.15.0 documentation](https://docs.python.org/3/library/sqlite3.html)
- [Tutorial - User Guide - FastAPI](https://fastapi.tiangolo.com/tutorial/)

---

[이전 장](../02-llm-embedding/chapter.md) · [책 목차](../index.md) · [다음 장](../04-baseline/chapter.md)
