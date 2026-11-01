---
title: "14장. 트랜잭션 전파와 자원 점유"
description: "논리·물리 트랜잭션, REQUIRED·REQUIRES_NEW·NESTED와 나머지 전파 모드를 비교하고 풀 고갈·중첩 롤백을 분석한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 14
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: 감사 로그만 남기려다 연결 풀이 멈췄다

실패한 주문도 감사 기록은 남겨야 해서 감사 서비스에 REQUIRES_NEW를 붙였다. 요청 수가 늘자 DB가 한가해도 풀이 고갈됐다. 바깥 트랜잭션이 연결을 잡은 채 안쪽 독립 트랜잭션이 추가 연결을 기다리는 상황이다. 전파는 예외 처리 선택이면서 자원 점유 정책이다.

## 14.1 논리 경계와 물리 트랜잭션

메서드 A와 B에 각각 `@Transactional`이 있어도 반드시 DB 트랜잭션이 두 개 생기지는 않는다. 각 메서드 선언은 **논리 경계**이고, 실제 Connection의 commit 단위가 **물리 트랜잭션**이다. 전파 설정은 기존 트랜잭션이 있을 때 둘을 어떻게 연결할지 정한다.

## 14.2 REQUIRED: 같은 업무를 함께 확정

기존 트랜잭션이 없으면 새로 시작하고, 있으면 참여한다. 예약 서비스가 저장소 여러 개를 호출할 때 한 업무로 묶기 적합하다. 안쪽의 실패가 rollback-only를 표시하면 바깥도 확정할 수 없다.

안쪽 메서드에 더 높은 isolation이나 readOnly를 적어도 이미 존재하는 물리 트랜잭션을 새로 만드는 것은 아니다. 기본 참여 동작에서는 바깥 특성을 따르는 경우가 있으며, 불일치를 거절하도록 매니저의 검증 옵션을 설정할 수도 있다. 안쪽 어노테이션만 보고 실제 격리 수준이 바뀌었다고 판단하지 않는다.

## 14.3 REQUIRES_NEW: 독립적인 성공과 실패

기존 트랜잭션을 일시 중단하고 새 물리 트랜잭션을 시작한다. 안쪽이 commit되면 이후 바깥이 rollback돼도 안쪽 결과는 남는다. 감사 기록 같은 경우에 유용할 수 있지만 주문 실패 후 “예약 완료” 이벤트만 남기는 데 사용하면 잘못된 사실을 전파한다.

```text
Connection A: 주문 시작 ───────────── 주문 실패 → rollback
                         잠시 중단
Connection B:          감사 기록 → commit → 반환
```

바깥이 잡은 연결·잠금은 중단했다고 사라지지 않는다. 독립 트랜잭션이 바깥에서 아직 commit하지 않은 행을 읽거나 수정하려 하면 보이지 않거나 잠금 대기·교착 문제가 생길 수 있다. 같은 스레드라는 이유로 DB 잠금이 자동 공유되지는 않는다.

## 14.4 풀 크기만으로 해결되지 않는 문제

요청 N개가 각각 바깥 연결 하나를 점유하고 안쪽 연결을 기다리는데 풀이 N개면 전부 기다릴 수 있다. 여분 연결을 두는 것은 필요 조건이 될 수 있지만 재귀적 중첩·다른 사용자·DB 한도까지 고려해야 한다. 무조건 `2 × 요청 수`로 고정하는 공식도 적절하지 않다.

가능하면 업무 경계를 짧게 만들고 REQUIRES_NEW가 정말 필요한지 검토한다. 실패 감사는 요청 데이터만 별도 기록하고 아직 확정되지 않은 주문 행에 FK를 걸지 않는 등의 데이터 설계도 중요하다. [공식 전파 문서](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)는 독립 트랜잭션과 추가 연결 위험을 구분한다.

## 14.5 NESTED: savepoint가 독립 commit은 아니다

NESTED는 일반적으로 하나의 물리 트랜잭션 안에 savepoint를 만들고 일부 변경을 되돌리는 방식이다. 안쪽 범위를 rollback하고 바깥 작업을 계속할 수 있지만, 바깥이 최종 rollback하면 안쪽에서 유지한 변경도 함께 취소된다. REQUIRES_NEW처럼 독립 확정되는 것이 아니다.

지원 여부는 트랜잭션 매니저와 드라이버에 달려 있다. JDBC savepoint 지원이 있다고 JPA의 1차 캐시와 엔티티 상태까지 부분 rollback에 맞춰 자동 복원된다고 가정하면 안 된다. JPA 환경에서 NESTED를 사용하기 전 실제 매니저 지원과 컨텍스트 상태를 검증한다.

## 14.6 나머지 전파 모드

| 모드 | 기존 트랜잭션 있음 | 없음 | 읽을 때의 질문 |
| --- | --- | --- | --- |
| SUPPORTS | 참여 | 트랜잭션 없이 실행 가능 | 둘 다 안전한 작업인가? |
| MANDATORY | 참여 | 예외 | 반드시 상위 유스케이스 안에서만 호출하는가? |
| NOT_SUPPORTED | 중단 후 비트랜잭션 실행 | 비트랜잭션 실행 | 중단 중에도 바깥 자원이 남는가? |
| NEVER | 예외 | 비트랜잭션 실행 | 트랜잭션 안의 호출을 금지할 이유가 있는가? |

“비트랜잭션” 메서드가 호출한 저장소가 자체적으로 새 트랜잭션을 열 수도 있다. 모드 이름만이 아니라 하위 호출과 매니저 동작까지 읽는다. 이 표는 트랜잭션 문맥의 기본 정책이며 모든 자원 동기화 세부를 생략한 것이다.

## 실습: 독립 감사 기록의 의미

`requiresNewCommitSurvivesOuterRollback` 테스트는 바깥에서 `outer` 행을 넣고 다른 빈의 `independent()`를 호출해 `independent` 행을 commit한 뒤 바깥을 실패시킨다. 최종 audit_log에는 independent 한 행만 남아야 한다.

이는 감사 DB가 반드시 별도 시스템이어야 한다는 뜻이 아니다. 같은 DB에서도 별도 Connection과 물리 트랜잭션을 사용한다. 반대로 다른 DB 두 개를 사용하면 같은 REQUIRED 이름만으로 원자성이 생기지 않는다. XA/JTA 등의 분산 트랜잭션 또는 업무 보상·Outbox 설계가 별도 필요하다.

NESTED는 첨부 자동 테스트의 범위에 포함하지 않는다. 독자 실습에서는 JDBC 매니저와 savepoint 지원을 명확히 선택한 뒤 안쪽 rollback 후 바깥 commit, 안쪽 성공 후 바깥 rollback 두 경우를 각각 관찰한다.

## 확인 문제와 해설

**Q1. REQUIRED가 붙은 메서드 세 개면 commit 세 번인가?** 같은 트랜잭션에 참여했다면 물리 commit은 바깥 종료 때 한 번일 수 있다.

**Q2. REQUIRES_NEW 메서드를 같은 클래스에서 호출하면 독립 트랜잭션인가?** 프록시 자기 호출이면 설정이 적용되지 않을 수 있다.

**Q3. NESTED 성공 후 바깥 실패에서 안쪽만 남는가?** 같은 물리 트랜잭션이므로 남지 않는다. 독립 commit과 savepoint를 구분한다.

## 참고자료

- [Propagation API](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/transaction/annotation/Propagation.html)
- [JdbcTransactionManager](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/jdbc/support/JdbcTransactionManager.html)
- [JpaTransactionManager](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/orm/jpa/JpaTransactionManager.html)

---

[전체 목차](../index.md) · [← 이전 장](../13-transaction-rollback/chapter.md) · [다음 장 →](../15-isolation-locking/chapter.md)
