---
title: "09장. 메타데이터와 문서 식별 체계"
description: "인용·권한·버전·필터를 위한 필드를 정의한다. 식별자와 점수의 의미를 다른 계층에서 유지한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 9
part: 2
enableToc: true
---

# 09장. 메타데이터와 문서 식별 체계

## 학습 목표

- 인용·권한·버전·필터를 위한 필드를 정의한다.
- 식별자와 점수의 의미를 다른 계층에서 유지한다.

## 본문만 저장하면 생기는 일

답변에 필요한 문장을 찾았어도 누가 읽을 수 있는지, 어느 버전인지, 원문 어디에 있는지 모르면 서비스로 쓰기 어렵다. 메타데이터는 부가 장식이 아니라 인가·추적·갱신·인용의 핵심 계약이다.

문서 ID와 청크 ID를 분리한다. 하나의 문서가 여러 청크를 가지며 분할 전략이 바뀌면 청크도 달라진다. 제목과 URL을 ID로만 사용하면 이름 변경·주소 변경·다른 tenant의 동명 문서를 혼동할 수 있다.

## 예제의 데이터 모델

Document는 id·tenant·roles·title·source·version·text를 갖는다. Chunk는 이 문서의 일부 텍스트와 start/end·벡터를 갖는다. SQLite에서 documents와 chunks를 연결하고 문서 삭제 시 청크도 제거한다. 권한은 문서와 연결해 질문 시 현재 값으로 확인한다.

tenant는 사용자가 질문 본문에 임의로 적은 값을 신뢰하지 않는다. API 인증에서 얻은 Principal을 검색에 전달한다. roles가 비어 있으면 아무 문서도 볼 수 없다. 관리자도 자신의 tenant 범위에서만 문서를 변경한다.

## 안정적인 식별과 변환 추적

청크 ID는 tenant·문서 ID·version·제목·source·권한·시작 위치·내용을 해시한다. 내용이 같아도 권한과 원본 경계가 다르면 다른 객체다. 이것은 중복 제거 키와 같은 의미가 아니다. 정확 중복 내용 해시는 별도로 둘 수 있다.

원본 페이지·문단 경로·문서 유효 시점·수집 시점·파서 버전은 실제 문서 시스템에서 추가할 필드다. 예제는 source와 정규화 문자 범위를 제공하며 페이지 좌표까지 구현했다고 표시하지 않는다. 표현하지 않은 메타데이터를 UI에서 추측해 인용하면 안 된다.

## 필터와 검색 점수

권한과 tenant는 후보 생성 이전에 적용한다. 주제·날짜·문서 종류 필터는 질문 의도와 유효성 정책에 따라 추가한다. 필터가 검색 Recall을 낮출 수도 있으므로 누락 원인으로 추적한다. 모델이 만든 필터는 허용 필드와 값 범위를 검증한다.

BM25·코사인·RRF·리랭커 점수는 같은 척도가 아니다. 결과에 score가 있다고 동일 임계값으로 거절 판단을 하면 안 된다. 검색 방식과 index revision을 함께 기록하고 점수를 확률로 표현하지 않는다.

## 메타데이터도 검증한다

ID 길이·허용 문자·roles·source scheme·본문 크기를 제한한다. HTML UI는 제목과 source를 textContent로 표시한다. 메타데이터가 서버가 생성한 값인지 외부 문서에서 온 값인지 구분해 XSS와 로그 주입 경계를 지킨다.

## 실습과 평가

API query 요청에 tenant 필드를 추가하면 extra field로 거부되는지 확인한다. 다른 tenant에 같은 document_id를 넣어도 조회 범위가 섞이지 않아야 한다.

문서 권한만 바꾸어 청크 ID가 바뀌는 테스트를 확인한다. 인용이 이전 권한 snapshot을 계속 가리키지 않는지 살핀다.

## 확인 문제

본문 내용이 같다면 다른 tenant의 두 문서를 하나의 청크 객체로 공유해도 안전한가?

[해설](../appendices/answers.md#장-09)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html)
- [Security - FastAPI](https://fastapi.tiangolo.com/tutorial/security/)

---

[이전 장](../08-chunking/chapter.md) · [책 목차](../index.md) · [다음 장](../10-bm25/chapter.md)
