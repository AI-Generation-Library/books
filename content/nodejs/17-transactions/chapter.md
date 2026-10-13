---
title: "17장. 트랜잭션과 데이터 동시성"
description: "한 트랜잭션에서 같은 DB 연결을 사용한다. 원자성·격리·외부 큐 전달의 경계를 구분한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 17
part: 4
enableToc: true
---

# 17장. 트랜잭션과 데이터 동시성

## 학습 목표

- 한 트랜잭션에서 같은 DB 연결을 사용한다.
- 원자성·격리·외부 큐 전달의 경계를 구분한다.

## 하나의 업무 변경을 묶기

파일 업로드가 끝나면 작업을 queued로 바꾸고 큐에 전달할 의도를 기록해야 한다. 둘 중 하나만 저장되면 처리되지 않는 작업이 생기거나 존재하지 않는 작업 메시지가 생길 수 있다. 종합 프로젝트는 PostgreSQL 트랜잭션으로 작업 상태와 outbox 행을 함께 커밋한다.

```js
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query("UPDATE jobs SET state='queued' WHERE id=$1", [id]);
  await client.query('INSERT INTO outbox(job_id) VALUES($1)', [id]);
  await client.query('COMMIT');
} catch (error) {
  await client.query('ROLLBACK');
  throw error;
} finally {
  client.release();
}
```

`pool.query('BEGIN')`와 다른 `pool.query`를 섞으면 서로 다른 연결로 실행될 수 있다. 트랜잭션을 시작한 client를 끝까지 사용한다. 실패해도 연결을 반환하고, 커넥션을 잡은 채 느린 외부 HTTP 호출을 기다리지 않는다.

## 격리 수준과 경쟁 상태

트랜잭션이 있다고 모든 경쟁이 사라지지는 않는다. 같은 잔액을 두 요청이 읽고 각자 계산해 덮어쓰면 갱신을 잃을 수 있다. 원자적 UPDATE, 행 잠금, 버전 컬럼을 이용한 낙관적 충돌 검사 등 업무 규칙에 맞는 방법을 선택한다.

격리 수준은 동시에 실행되는 트랜잭션이 무엇을 볼 수 있는지에 관한 규칙이다. 더 강한 수준은 충돌로 실패할 수 있으므로 재시도 정책까지 필요하다. 재시도는 개별 SQL 한 줄이 아니라 업무 단위 전체의 안전성을 기준으로 설계한다. 데드락과 직렬화 실패를 무한 반복하지 않는다.

## 연결 풀은 무한한 처리량을 만들지 않는다

풀은 연결 생성 비용을 줄이고 DB 연결 수를 제한한다. 애플리케이션 인스턴스 10개가 각각 최대 20개를 사용하면 최대 200개를 요구할 수 있다. HTTP 요청 동시성·쿼리 시간·DB 한도를 함께 본다. 풀 대기 시간은 SQL 실행 시간과 구분해 측정한다.

연결 획득 기한과 쿼리 기한을 두고, DB 오류가 발생했을 때 사용자 응답과 내부 로그를 구분한다. 예제의 풀 크기 5는 학습 기본값이며 운영에 적합한 보편적 숫자는 아니다.

## DB와 큐 사이의 원자성

DB 커밋과 Redis 큐 추가는 서로 다른 시스템이다. DB 트랜잭션 안에서 Redis를 호출해도 두 자원이 함께 원자적으로 커밋되는 것은 아니다. outbox는 DB에 전달 의도를 남기고 별도 dispatcher가 큐로 옮긴다. 큐 추가 후 outbox 삭제 전에 종료되면 재전송될 수 있으므로 소비자도 중복을 허용해야 한다.

파일 시스템까지 같은 트랜잭션에 들어가지는 않는다. 업로드 직후 프로세스가 죽으면 `uploading` 행과 고아 파일이 남을 수 있다. 예제는 이 한계를 문서화하며 운영에는 업로드 기한과 정합성 점검·정리 작업을 추가해야 한다.

## 실습과 관찰

`PostgresRepository.enqueueJob()`에서 BEGIN부터 release까지 따라간다. 메모리 모드의 outbox 전송 실패 테스트는 의도 보존을 검사하지만 실제 DB 격리까지 검증하지는 않는다.

전용 DB에서 통합 테스트를 실행할 수 있다면 queued 상태와 outbox가 함께 존재하는지, Redis 전송 실패 동안 outbox가 남는지 관찰한다. 장애 주입 실험은 테스트 전용 데이터를 사용한다.

## 확인 문제

트랜잭션 내부에서 Redis에 메시지를 보냈다. 나중에 DB가 롤백되면 Redis 메시지도 사라지는가?

[해설 보기](../appendices/answers.md#장-17)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [GitHub](https://node-postgres.com/features/transactions)
- [GitHub](https://node-postgres.com/features/pooling)
- [PostgreSQL: Documentation: 17: 13.2. Transaction Isolation](https://www.postgresql.org/docs/17/transaction-iso.html)

---

[이전 장](../16-postgresql/chapter.md) · [책 목차](../index.md) · [다음 장](../18-authentication/chapter.md)
