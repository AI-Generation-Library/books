---
title: "13장. 벡터 저장소 구성과 검색 조건"
description: "저장소의 거리·차원·필터·갱신 계약을 확인한다. 로컬 구현과 외부 DB의 실제 검증을 구분한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 13
part: 3
enableToc: true
---

# 13장. 벡터 저장소 구성과 검색 조건

## 학습 목표

- 저장소의 거리·차원·필터·갱신 계약을 확인한다.
- 로컬 구현과 외부 DB의 실제 검증을 구분한다.

## 저장소가 맡는 책임

벡터 저장소는 벡터만 담는 배열보다 많은 책임을 가진다. 식별자·메타데이터·필터·갱신·삭제·지속성·동시 질의·인덱스 관리가 필요하다. 임베딩 모델을 자동으로 골라 주거나 답변 정확성을 보장하는 장치는 아니다.

이 프로젝트는 SQLite에 문서·청크·벡터 JSON을 저장하고 Python에서 허용 후보를 정확 검색한다. 소규모 학습과 재현이 목적이다. 대규모 벡터 DB의 성능·트랜잭션·복제 기능을 흉내 냈다고 주장하지 않는다.

## pgvector로 확장하는 예

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE passages (
  id text PRIMARY KEY,
  tenant_id text NOT NULL,
  document_id text NOT NULL,
  version text NOT NULL,
  body text NOT NULL,
  embedding vector(384) NOT NULL
);
CREATE INDEX ON passages USING hnsw (embedding vector_cosine_ops);
```

이 SQL은 구조를 설명하는 예시이며 이번 환경에서 실행하지 않았다. 실제 서비스에는 문서 권한·행 수준 보안·접속 역할·업무 제약·갱신 관리가 추가된다. WHERE tenant_id가 있다는 사실만으로 전체 인증과 인가 설계가 완료되는 것은 아니다.

## 거리 함수와 연산자

내적·코사인 거리·L2는 의미와 정렬 방향이 다르다. 정규화 여부에 따라 순위 관계가 달라질 수 있다. pgvector의 연산자와 인덱스 opclass를 같은 거리 계약에 맞춘다. 벡터 문자열을 SQL에 붙이지 말고 드라이버의 매개변수·지원 타입을 사용한다.

모델·차원·정규화가 달라지면 새 인덱스를 만든다. 같은 컬렉션 이름에 기존 벡터와 새 벡터를 섞지 않는다. 임베딩 signature를 메타데이터로 검사하고 색인과 질의 설정이 다르면 빠르게 실패하게 한다.

## 필터된 ANN의 두 문제

첫째는 권한이 없는 내용이 반환되지 않도록 하는 보안 문제다. 둘째는 필터 후 후보가 부족해지는 검색 품질 문제다. DB 내부의 ANN 탐색과 필터 순서를 확인하고 oversampling·iterative scan·분리 인덱스 등을 요구에 맞게 검토한다. 반환 후에만 인가를 검사해 외부 리랭커에 비인가 후보를 보내지 않는다.

연결 풀의 tenant 문맥이 다음 사용자 요청에 남지 않도록 트랜잭션 지역 설정과 정리를 설계한다. 사용자 입력을 그대로 DB 세션 권한으로 바꾸지 않는다. 저장소의 빠른 검색만으로 서비스 경계가 안전해지는 것은 아니다.

## 실습과 평가

Store의 metadata embedding·dimension 필드를 확인한다. 다른 signature나 차원의 벡터로 기존 인덱스를 열거나 갱신하면 거부되고 이전 문서가 보존되는지 테스트한다.

pgvector를 도입하는 확장에서는 같은 qrels·문서 snapshot으로 정확 검색과 ANN을 비교하고 DB 버전·확장 버전·인덱스 파라미터를 함께 기록한다.

## 확인 문제

벡터 DB가 tenant 필터를 지원하므로 비인가 문서를 외부 리랭커에 먼저 보낸 뒤 최종 결과만 필터해도 되는가?

[해설](../appendices/answers.md#장-13)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [GitHub - pgvector/pgvector: Open-source vector similarity search for Postgres · GitHub](https://github.com/pgvector/pgvector)
- [PostgreSQL: Documentation: 18: 5.9. Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Transaction](https://www.sqlite.org/lang_transaction.html)

---

[이전 장](../12-ann-index/chapter.md) · [책 목차](../index.md) · [다음 장](../14-hybrid-rrf/chapter.md)
