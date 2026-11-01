---
title: "15장. 격리 수준·락·재시도"
description: "dirty read·non-repeatable read·phantom·lost update·write skew, MVCC·낙관/비관 락·조건부 UPDATE·교착 재시도를 구분한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 15
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: 마지막 재고를 두 사람이 동시에 예약한다

T1과 T2가 재고 1을 읽었다. 둘 다 1 이상이라고 판단하고 예약을 저장한 다음 재고를 0으로 바꾼다. 최종 숫자가 음수가 아니어도 예약은 두 개다. 원자성만으로 이 경쟁 조건을 막을 수는 없다.

## 15.1 동시에 읽을 때 생기는 현상

**Dirty read**는 다른 트랜잭션이 아직 commit하지 않은 값을 읽는 것이다. **Non-repeatable read**는 같은 행을 다시 읽을 때 값이 달라지는 것이다. **Phantom read**는 같은 조건을 다시 조회했을 때 조건에 맞는 행 집합이 달라지는 것이다.

**Lost update**는 두 요청이 읽은 값으로 각각 갱신하면서 한 변경을 덮어쓰는 상황이다. **Write skew**는 각 트랜잭션이 서로 다른 행을 바꾸지만 합쳐 보면 규칙이 깨지는 상황이다. 예를 들어 당직 의사 두 명이 각각 “다른 한 명이 남아 있다”고 읽고 자기 상태만 퇴근으로 바꾸면 아무도 남지 않을 수 있다.

## 15.2 격리 수준은 DB 구현과 함께 읽는다

| 수준 | 핵심 관점 | 주의점 |
| --- | --- | --- |
| READ_UNCOMMITTED | 표준상 dirty read를 허용할 수 있음 | PostgreSQL은 READ_COMMITTED로 취급 |
| READ_COMMITTED | commit된 데이터 기준 읽기 | 문장마다 관찰 값이 달라질 수 있음 |
| REPEATABLE_READ | 반복 읽기의 안정성 강화 | DB별 스냅샷·팬텀·충돌 동작 차이 |
| SERIALIZABLE | 성공한 실행을 직렬 순서와 동등하게 | 충돌 시 실패·재시도 비용 가능 |

SQL 표준의 최소 보장 표와 실제 DB 동작은 다르다. PostgreSQL의 REPEATABLE READ는 팬텀도 방지하지만 직렬화 이상 현상까지 모두 제거하지는 않는다. 이 책의 PostgreSQL 설명은 [격리 수준 문서](https://www.postgresql.org/docs/18/transaction-iso.html)를 기준으로 하며 MySQL InnoDB의 잠금 읽기에 그대로 대입하지 않는다.

**MVCC — Multi-Version Concurrency Control**는 데이터의 여러 버전을 활용해 읽기와 동시 수정을 제어하는 방식이다. MVCC를 사용한다고 잠금이 사라지는 것은 아니다. UPDATE·제약 검사·DDL 등은 여전히 잠금과 대기를 만들 수 있다.

## 15.3 조건부 UPDATE: 검사와 변경을 한 문장으로

통합 예제는 다음 SQL을 사용한다.

```sql
UPDATE inventory
SET available = available - :quantity
WHERE sku = :sku AND available >= :quantity;
```

위 named parameter는 설명 표기이며 실제 JdbcTemplate 코드는 `?`를 사용한다. 성공 여부는 영향받은 행 수 1인지로 판단한다. 조회 결과를 Java에서 감소시켜 다시 저장하는 두 단계보다 경쟁 구간을 줄인다. DB의 해당 UPDATE 동시성 규칙을 바탕으로 한 설계이므로 목표 DB에서 확인한다.

예제에는 `available >= 0` CHECK도 있다. CHECK는 음수를 막지만 예약 개수와 재고 감소가 함께 맞는지까지 스스로 검증하지 않으므로 서비스 원자성도 필요하다. 단일 행 조건으로 표현할 수 없는 여러 행 불변식에는 다른 전략을 검토한다.

## 15.4 낙관적 락

낙관적 락은 충돌을 드물다고 가정하고 버전 조건으로 변경 시점을 확인한다. JPA의 `@Version`이 대표적이다. 원리는 다음과 같은 갱신이다.

```sql
UPDATE product
SET available = :next, version = version + 1
WHERE id = :id AND version = :observed_version;
```

행 수가 0이면 읽은 뒤 다른 변경이 있었다고 판단한다. 재시도할 때는 이전 계산 결과를 그대로 쓰지 않고 새 트랜잭션에서 읽기·규칙 검사를 다시 수행한다. JPA 버전 충돌 예외와 HTTP 409 변환은 경계를 분리한다.

## 15.5 비관적 락과 교착

비관적 락은 `SELECT ... FOR UPDATE` 등으로 갱신 대상에 대한 경쟁을 먼저 제한한다. 락을 보유한 동안 외부 API를 기다리면 다른 요청도 길게 막힌다. 두 SKU를 잠그는 작업에서는 모든 코드 경로가 SKU 정렬 순서처럼 같은 순서로 잠그도록 설계하면 교착 가능성을 줄일 수 있다.

**Deadlock, 교착**은 T1이 A를 가진 채 B를 기다리고 T2가 B를 가진 채 A를 기다리는 순환 대기다. DB는 피해 트랜잭션을 중단할 수 있다. 단순 쿼리 지연과 구분하고 제한된 재시도·백오프·지터를 적용한다. 재시도는 전체 업무가 멱등하며 새 트랜잭션에서 가능할 때만 수행한다.

## 실습 A: 첨부된 동시 주문 테스트

`concurrentRequestsCannotOversell`은 12개 작업을 CountDownLatch로 함께 출발시키고 각자 다른 요청 키로 수량 1을 예약한다. 시작 재고는 5다. 기대 결과는 성공 5, 품절 7, 예약 5행, Outbox 5행, 재고 0이다. 업무 예외 외의 타임아웃·DB 오류는 테스트 실패로 드러내며 품절로 숨기지 않는다.

이 실험은 H2에서 코드의 경쟁 조건 방어를 확인한다. PostgreSQL 운영 락 시간·초당 처리량·공정성을 검증한 결과가 아니다.

## 실습 B: PostgreSQL 두 세션 실험

별도 폐기 가능한 DB에서 `inventory` 한 행을 준비한다. 세션 A가 BEGIN 후 해당 행을 `FOR UPDATE`로 읽고 commit하지 않는다. 세션 B가 같은 행을 UPDATE하면 대기하는지 관찰한다. A를 COMMIT한 뒤 B의 결과를 읽는다. 모든 열린 트랜잭션은 실습 종료 때 명시적으로 닫는다.

이 연습은 별도 실행 과제다. 운영 DB에 장시간 잠금을 잡아 실험하지 않는다. DB 버전·격리 수준·lock_timeout을 기록해야 재현할 수 있다.

## 확인 문제와 해설

**Q1. synchronized면 서버 세 대에서도 마지막 재고를 보호하는가?** 한 JVM의 잠금 범위이므로 다른 프로세스와 공유되지 않는다.

**Q2. SERIALIZABLE이면 재시도 코드가 필요 없는가?** 직렬화 충돌로 실패할 수 있으므로 실패 분류와 재시도 설계가 필요하다.

**Q3. 낙관적 락 충돌 후 같은 EntityManager에서 무조건 재호출해도 되는가?** 실패 상태와 오래된 객체가 남을 수 있다. 트랜잭션을 종료하고 새 경계에서 다시 읽는다.

## 참고자료

- [PostgreSQL 명시적 잠금](https://www.postgresql.org/docs/18/explicit-locking.html)
- [Spring Data JPA locking](https://docs.spring.io/spring-data/jpa/reference/jpa/locking.html)

---

[전체 목차](../index.md) · [← 이전 장](../14-transaction-propagation/chapter.md) · [다음 장 →](../16-query-performance/chapter.md)
