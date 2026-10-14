---
title: "07장. 정규화·중복 제거·문서 버전 관리"
description: "검색 편의를 위한 변환과 원문 보존을 구분한다. 중복·개정·삭제를 다른 데이터 사건으로 처리한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 7
part: 2
enableToc: true
---

# 07장. 정규화·중복 제거·문서 버전 관리

## 학습 목표

- 검색 편의를 위한 변환과 원문 보존을 구분한다.
- 중복·개정·삭제를 다른 데이터 사건으로 처리한다.

## 정규화는 의미를 바꿀 수도 있다

공백·줄바꿈·Unicode 형태가 다르면 같은 검색어를 다르게 취급할 수 있다. 예제는 NFKC와 줄바꿈·연속 공백 정규화를 사용한다. 전각 영문과 일반 영문을 맞추기 편하지만 코드·수학·식별자에서는 호환 문자 변환이 구분을 없앨 수도 있다. 도메인별 보존 규칙을 정한다.

```python
from ragbook.data import normalize
assert normalize('Ａ  B\r\n  안내 ') == 'A B\n안내'
assert normalize(normalize('Ａ  B')) == normalize('Ａ  B')
```

같은 함수를 반복 적용해 값이 더 바뀌지 않는 성질은 파이프라인 재실행을 안정적으로 만든다. 그러나 이 성질이 변환의 의미적 안전성을 증명하지는 않는다. 원문과 정규화본을 구분하고 인용 위치가 어느 쪽 기준인지 표시한다.

## 반복 텍스트와 중복 문서

페이지마다 같은 머리말·법적 고지·메뉴가 붙으면 검색 순위에 영향을 준다. 반복 위치와 문서 구조를 이용해 제거하되 원문에서 중요한 조건 문장을 지우지 않았는지 확인한다. 숫자나 날짜가 다른 문서를 유사하다는 이유로 합치면 정책 변경을 잃을 수 있다.

정확한 내용 해시는 동일 바이트나 정규화 텍스트의 중복을 찾는 데 유용하다. 근사 중복은 별도 유사도·구간·검토가 필요하다. 서로 다른 출처가 같은 내용을 제공하는 경우 출처별 권한과 유효성은 유지해야 한다.

## 논리 문서와 revision

document_id는 논리적인 문서, version은 특정 개정이다. 수정된 문서를 새 ID로만 추가하면 오래된 개정도 계속 검색될 수 있다. 최신판만 검색할지 질문 시점에 유효했던 판을 검색할지 정한다. 수집 시각과 업무 적용 시각도 같지 않을 수 있다.

예제는 같은 tenant·문서 ID를 upsert하면 기존 청크를 삭제하고 새 청크로 교체한다. 임베딩은 쓰기 트랜잭션 전에 만들고 DB 교체만 원자적으로 수행한다. 추론이 실패하면 이전판을 유지한다. 대규모 외부 벡터 저장소까지 하나의 원자적 트랜잭션으로 묶은 구현은 아니다.

## 삭제와 권한 변경

원문 삭제는 검색 인덱스·청크·캐시·요약·파생 그래프에도 반영해야 한다. 개인정보 삭제 요구에서 원문 파일만 지우고 임베딩과 캐시를 남기는 것으로 충분하다고 가정하지 않는다. 구체적인 보관 의무는 서비스 조건과 적용 규칙에 따라 별도로 확인한다.

역할 변경도 단순 텍스트 갱신과 다르다. 예제는 청크 ID에 권한 메타데이터를 반영하고 생성 직전과 반환 전 권한을 확인한다. 캐시를 추가하면 사용자별 권한 revision과 무효화 정책이 새로 필요하다.

## 실습과 평가

문서 v1을 넣고 v2로 바꾼 뒤 이전 청크 ID가 남지 않는지 테스트한다. 임베딩 실패·차원 불일치를 의도적으로 만들어 이전판이 보존되는지 확인한다.

정규화 start/end는 원본 PDF 바이트 위치가 아니다. 실제 페이지 하이라이트 기능을 추가하려면 파서에서 좌표와 원문 대응을 보존해야 한다.

## 확인 문제

비슷한 문서 두 개에서 숫자만 다르다. 검색 중복이므로 하나로 합쳐도 되는가?

[해설](../appendices/answers.md#장-07)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [unicodedata — Unicode Database — Python 3.15.0 documentation](https://docs.python.org/3/library/unicodedata.html)
- [sqlite3 — DB-API 2.0 interface for SQLite databases — Python 3.15.0 documentation](https://docs.python.org/3/library/sqlite3.html)
- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)

---

[이전 장](../06-parsing/chapter.md) · [책 목차](../index.md) · [다음 장](../08-chunking/chapter.md)
