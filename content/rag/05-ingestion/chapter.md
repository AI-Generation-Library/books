---
title: "05장. 문서 수집과 데이터 출처 관리"
description: "수집 권한과 자료의 사용 범위를 기록한다. 원본부터 색인까지 추적할 식별 체계를 만든다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 5
part: 2
enableToc: true
---

# 05장. 문서 수집과 데이터 출처 관리

## 학습 목표

- 수집 권한과 자료의 사용 범위를 기록한다.
- 원본부터 색인까지 추적할 식별 체계를 만든다.

## 수집 범위가 품질과 보안을 결정한다

많은 문서를 모으는 것보다 어떤 질문에 어떤 자료를 근거로 답할지 정하는 것이 먼저다. 정책·매뉴얼·FAQ·티켓·코드 문서는 작성 주체와 유효 기간이 다르다. 초안·폐기된 문서·개인 메모를 섞으면 검색된 근거끼리 충돌할 수 있다.

읽을 수 있다는 사실과 다시 저장·공개·모델 입력에 사용할 수 있다는 권한은 같지 않다. 수집 목적·저장 위치·제삼자 전송·보관 기간·삭제 요구를 확인한다. 이 책은 실제 기업 자료 대신 저자가 만든 가상 문서를 사용해 실행 데이터를 공개할 수 있게 했다.

## 수집 manifest

| 항목 | 기록 이유 |
| --- | --- |
| tenant·document_id | 조직과 업무 문서 경계 |
| source·원본 식별자 | 인용·감사·재수집 |
| version·내용 해시 | 수정 여부와 재현 |
| 수집 시각·유효 시각 | 최신성과 적용 시점 구분 |
| 권한·공개 범위 | 검색 전 접근 통제 |
| 파서·전처리 버전 | 추출 오류와 재색인 추적 |

웹 URL이 같아도 내용은 바뀔 수 있고, 파일명이 달라도 같은 내용일 수 있다. 원본 식별자·내용 해시·업무 버전을 분리한다. 예제는 source와 명시적 version을 저장하고 청크 내용·메타데이터를 ID에 반영한다.

## 커넥터와 반복 실행

파일·API·웹 커넥터는 인증·페이지네이션·호출 제한·변경 이력을 처리한다. 실패한 수집을 재시작할 때 같은 문서를 중복 추가하지 않게 안정적인 ID와 upsert 정책을 사용한다. 삭제된 원문을 계속 남기는 증분 수집은 보관 정책을 위반할 수 있다.

수집과 질의를 분리하면 외부 API가 잠깐 느려도 이미 색인된 문서를 검색할 수 있다. 반대로 최신성이 중요한 자료는 원본 조회를 혼합할 수 있다. 어떤 값이 snapshot이고 어떤 값이 실시간인지 응답 정책에 반영한다.

## 외부 URL의 경계

서비스가 사용자가 보낸 URL을 대신 다운로드하면 SSRF·무제한 다운로드·악성 파일의 경계가 열린다. 허용 대상·네트워크 출구·리다이렉트·크기·기한을 검토한다. 이 예제의 source 문자열은 출처 메타데이터이며 서버가 그 주소를 자동으로 가져오지 않는다.

가상 fixture:// 출처는 실제 공개 링크가 아니다. UI도 이를 텍스트로 보여 주며 임의 HTML이나 URL을 실행하지 않는다. 실제 서비스에는 원본 시스템의 접근 권한을 유지한 인용 링크를 연결한다.

## 실습과 평가

data/documents.json에서 공개 reader·admin 전용·다른 tenant 문서를 분류한다. CLI index를 두 번 실행해 같은 문서가 무한히 쌓이지 않는지 확인한다.

실제 자료를 추가한다면 먼저 별도의 manifest에 사용 권한과 원본 버전을 기록한다. 비밀 문서를 책 PR이나 검증 출력에 붙이지 않고 공개 가능한 테스트 문서로 재현한다.

## 확인 문제

같은 URL의 내용을 매일 수집한다. URL만 저장하면 답변을 나중에 완전히 재현할 수 있는가?

[해설](../appendices/answers.md#장-05)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [Server Side Request Forgery Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

---

[이전 장](../04-baseline/chapter.md) · [책 목차](../index.md) · [다음 장](../06-parsing/chapter.md)
