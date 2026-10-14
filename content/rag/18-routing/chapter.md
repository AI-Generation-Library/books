---
title: "18장. 질의 라우팅과 여러 데이터 소스 연결"
description: "문서·SQL·전용 API의 역할을 요구에 맞게 나눈다. 라우팅이 권한을 바꾸지 않도록 제한한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 18
part: 4
enableToc: true
---

# 18장. 질의 라우팅과 여러 데이터 소스 연결

## 학습 목표

- 문서·SQL·전용 API의 역할을 요구에 맞게 나눈다.
- 라우팅이 권한을 바꾸지 않도록 제한한다.

## 모든 질문을 문서 벡터로 풀 필요는 없다

정책 설명은 문서 검색, 현재 주문 상태는 업무 API, 기간별 합계는 구조화 질의가 더 적합할 수 있다. 숫자가 매일 바뀌는데 어제 만든 문서 임베딩으로 답하면 최신성 문제가 생긴다. 자료 유형과 사실의 원본을 먼저 정한다.

라우터는 질문을 보고 적절한 검색기를 고른다. 처음에는 명시적인 규칙과 확인 질문으로 시작할 수 있다. LLM 라우팅은 모호한 질문을 처리할 수 있지만 잘못된 선택·추가 호출·출력 검증이 필요하다. 선택 이유와 실패 시 되돌아갈 경로를 기록한다.

## 메타데이터 필터

질문에서 제품명·기간·문서 종류를 추출해 허용된 필터로 바꿀 수 있다. 모델이 만든 임의 SQL 조각이나 검색 표현식을 바로 실행하지 않는다. 허용 필드·연산자·값 타입과 조회 범위를 검증하고, 추출하지 못한 조건은 사용자에게 확인하거나 필터 없는 허용 범위 검색으로 돌아간다.

tenant·사용자 권한은 라우터가 추측하는 필터가 아니다. 인증 계층이 제공한 강제 경계다. 프롬프트로 다른 tenant를 검색하라는 지시가 들어와도 도구의 서버 측 범위를 넓히지 않는다.

## SQL과 업무 API

자연어→SQL은 문법이 맞는지 외에도 권한·비용·결과 크기·업무 의미를 검증해야 한다. 읽기 전용 DB 역할, 허용 테이블·열, 행 수·실행 시간 제한, 매개변수와 승인된 질의 템플릿을 검토한다. 단순히 SELECT로 시작하는지 확인하는 것은 충분한 방어가 아니다.

민감한 업무 API는 사용자의 실제 권한과 감사 기록을 유지한다. 답변 모델에 전체 원장이나 필요 없는 개인 정보를 보내지 않는다. 집계와 마스킹이 필요한 경우 도구 계층에서 처리한다.

## 여러 검색 결과 결합

서로 다른 인덱스의 점수·문서 ID·시간 기준을 통일해야 한다. 검색 시점이 다른 자료를 조합하면 모순될 수 있다. 출처별 원본 시각과 근거를 유지하고 충돌을 숨기지 않는다. 다중 검색 호출의 타임아웃·부분 실패·최대 비용도 계약이다.

예제 서비스는 하나의 허용 문서 저장소를 사용한다. 본 장의 SQL·다중 인덱스 라우팅은 확장 설계 범위다. 구현되지 않은 외부 업무 시스템 연결을 실행 검증했다고 표시하지 않는다.

## 실습과 평가

가상 질문을 정책 설명·현재 수치·문서 비교로 나누고 어느 데이터 원본이 맞는지 표를 만든다. 잘못된 라우팅의 실패 비용과 확인 질문 정책도 적는다.

향후 도구를 추가할 때는 반환 형식·최대 결과·권한·기한·오류를 인터페이스로 고정한다. 질문 본문이 서버의 Principal을 덮어쓰지 않는 테스트를 유지한다.

## 확인 문제

모델이 SQL 검색을 선택했으니 관리자 DB 계정으로 실행해도 되는가?

[해설](../appendices/answers.md#장-18)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [PostgreSQL: Documentation: 18: 5.9. Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [SQL Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

---

[이전 장](../17-context-retrieval/chapter.md) · [책 목차](../index.md) · [다음 장](../19-multi-hop/chapter.md)
