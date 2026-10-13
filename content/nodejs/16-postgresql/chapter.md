---
title: "16장. PostgreSQL과 데이터 모델링"
description: "관계·제약·인덱스를 데이터 불변식과 연결한다. 매개변수 쿼리와 마이그레이션으로 데이터를 관리한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 16
part: 4
enableToc: true
---

# 16장. PostgreSQL과 데이터 모델링

## 학습 목표

- 관계·제약·인덱스를 데이터 불변식과 연결한다.
- 매개변수 쿼리와 마이그레이션으로 데이터를 관리한다.

## 데이터 모델은 규칙의 저장 장소

사용자는 여러 작업을 소유하고 세션은 한 사용자를 가리킨다. 작업 ID와 사용자 ID는 기본 키, 이메일은 유니크 제약, 세션과 작업의 소유자는 외래 키로 표현한다. 애플리케이션에서 중복을 미리 조회해도 동시에 요청이 들어오면 둘 다 통과할 수 있다. 최종 불변식은 DB 제약으로 지킨다.

```sql
CREATE TABLE users (
  id uuid PRIMARY KEY,
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL
);
CREATE TABLE jobs (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id),
  state text NOT NULL,
  result jsonb
);
```

실제 마이그레이션은 상태 CHECK·조회 인덱스·세션·outbox를 추가한다. JSONB는 분석 결과처럼 형태가 작고 변화할 수 있는 값에 썼다. 검색·관계·제약이 중요한 필드를 전부 JSON에 넣으면 쿼리와 데이터 규칙이 불명확해질 수 있다.

## 문자열 조합 대신 매개변수

```js
const { rows } = await pool.query(
  'SELECT id, email FROM users WHERE email=$1', [email]
);
```

값을 SQL 문자열에 붙이지 않는다. 매개변수는 값에 쓰이며 테이블·컬럼 이름을 임의로 치환하는 기능은 아니다. 정렬 컬럼을 입력받는다면 허용 목록에서 SQL 조각을 선택한다. ORM을 써도 raw SQL과 동적 식별자 처리에는 같은 주의가 필요하다.

## 인덱스와 접근 패턴

`WHERE owner_id=$1 ORDER BY id` 같은 조회가 많으면 해당 조건과 정렬에 맞는 인덱스를 검토한다. 인덱스는 쓰기와 저장 공간 비용도 갖는다. 모든 컬럼에 만드는 대신 실제 데이터 분포와 실행 계획을 본다. 작은 개발 DB에서 빠르다는 이유만으로 운영 크기에서도 같다고 결론 내리지 않는다.

조회 때 필요한 컬럼만 선택하면 전송량을 줄이고 민감정보를 실수로 노출할 가능성도 줄인다. 비밀번호 해시는 로그인 검증 경로 외에는 응답 객체에 포함하지 않는다. API용 객체와 DB 행 전체를 구분한다.

## 마이그레이션과 ORM의 역할

예제의 `001-initial.sql`은 새 전용 DB를 초기화하는 파일이다. `IF NOT EXISTS`를 사용하지만 기존 테이블의 스키마를 최신으로 바꾸는 일반 마이그레이션 시스템은 아니다. 다음 변경부터는 번호·적용 기록·롤포워드·호환 전략을 가진 별도 변경을 추가해야 한다.

ORM은 객체 매핑과 쿼리 구성을 돕지만 SQL·트랜잭션·인덱스 이해를 없애지는 않는다. 이 책은 원리를 드러내기 위해 `pg`로 작성했다. ORM을 도입한다면 생성 SQL, N+1 조회, 트랜잭션 범위와 커넥션 점유를 관찰한다.

## 실습과 관찰

`examples/migrations/001-initial.sql`과 `src/postgres-repository.mjs`를 함께 읽는다. 메서드 하나가 어떤 제약을 기대하는지 표시한다. 중복 이메일의 DB 오류 `23505`를 HTTP 409로 바꾸는 경로를 찾는다.

실행 환경이 준비되면 `npm run migrate`로 전용 DB를 초기화한다. 운영 DB에 실습용 접속 정보를 사용하지 않는다. 이번 환경에서는 PostgreSQL 직접 실행 여부를 검증 안내와 구분한다.

## 확인 문제

이메일 중복을 SELECT로 검사한 뒤 INSERT했다. UNIQUE 제약이 없어도 안전한가?

[해설 보기](../appendices/answers.md#장-16)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [GitHub](https://node-postgres.com/features/queries)
- [PostgreSQL: Documentation: 17: 5.5. Constraints](https://www.postgresql.org/docs/17/ddl-constraints.html)
- [PostgreSQL: Documentation: 17: Chapter 11. Indexes](https://www.postgresql.org/docs/17/indexes.html)

---

[이전 장](../15-testing/chapter.md) · [책 목차](../index.md) · [다음 장](../17-transactions/chapter.md)
