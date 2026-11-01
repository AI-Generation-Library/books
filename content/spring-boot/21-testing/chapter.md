---
title: "21장. 단위·통합·트랜잭션 테스트"
description: "단위·슬라이스·실제 HTTP·DB 통합 테스트를 구분하고 테스트 트랜잭션의 가림 효과·flush·commit·동시성 검증을 설계한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 21
part: 5
enableToc: true
---

> PART 5. 검증과 운영

## 도입: 테스트는 초록인데 운영에서는 롤백되지 않는다

테스트 클래스에 `@Transactional`이 있어 항상 바깥 트랜잭션이 열린 상태였다. 서비스는 직접 생성한 객체인데도 Repository가 그 트랜잭션에 참여해 테스트가 통과했다. 운영에서는 서비스 프록시가 빠져 부분 저장이 발생했다. 테스트 도구가 실제 결함을 가릴 수 있다.

## 21.1 검증할 계약에 맞춰 범위를 선택한다

| 종류 | 확인하는 것 | 의도적으로 놓는 것 |
| --- | --- | --- |
| 순수 단위 테스트 | 규칙, 상태 전이, 경계값 | Spring 구성·SQL |
| 슬라이스 테스트 | MVC 매핑·검증 또는 저장 계층 | 전체 앱의 조립 |
| 컨텍스트 통합 | 실제 빈·프록시·트랜잭션 | 실제 네트워크일 필요는 없음 |
| HTTP 통합 | 내장 서버·필터·직렬화·상태 코드 | 외부 운영 인프라 |
| 목표 DB 통합 | 실제 SQL·제약·잠금·마이그레이션 | 실트래픽 용량 보장 |

`@SpringBootTest`의 기본 사용만으로 실제 포트 서버가 항상 뜨는 것은 아니다. RANDOM_PORT 등 webEnvironment를 명시한다. MockMvc는 Servlet 요청 처리를 테스트하지만 실제 TCP 네트워크를 통과하는 실험과는 범위가 다르다.

## 21.2 통합 예제의 네 테스트 클래스

DiTests는 생성자 주입과 singleton 조립을, ReservationTests는 업무·DB 상태를, TransactionTests는 롤백·전파·프록시를, HttpTests는 실제 내장 서버를 검증한다. JDBC 테스트에는 H2 DB 이름을 나눠 컨텍스트 간 데이터가 섞이지 않게 했다.

```powershell
mvn test
mvn -Dtest=TransactionTests test
mvn -Dtest=ReservationTests test
mvn verify
```

검증 기록의 실행 결과와 현재 독자의 결과를 구분한다. dependency cache가 없는 첫 실행은 네트워크가 필요하다. 테스트가 성공해도 운영 DB·브로커·배포 설정까지 검증된 것은 아니다.

## 21.3 테스트의 자동 rollback을 구분한다

Spring TestContext의 테스트 트랜잭션은 기본적으로 테스트 후 rollback될 수 있다. 저장소 테스트의 격리에는 편리하지만 서비스의 실제 commit 동작, AFTER_COMMIT 리스너, 제약 오류 시점을 보려면 다른 구조가 필요하다.

테스트 메서드에 트랜잭션을 두지 않고 서비스를 프록시로 호출한 뒤 DB를 다시 조회하거나, TestTransaction 등으로 테스트 트랜잭션 종료를 명시할 수 있다. RANDOM_PORT 서버는 다른 스레드에서 처리하므로 테스트 메서드의 자동 rollback이 서버에서 commit한 데이터를 자동 되돌려주지 않는다. 데이터 정리 전략을 별도로 둔다.

## 21.4 flush와 commit을 실제로 통과시킨다

JPA에서 잘못된 엔티티 상태가 1차 캐시에만 남아 있으면 테스트가 통과하고 실제 flush에서 제약 오류가 날 수 있다. DB 검증이 목적이라면 flush로 SQL을 보내고 필요하면 clear 후 다시 읽는다. 하지만 flush만으로 commit 후 관측까지 확인한 것은 아니다.

테스트에서 읽은 객체가 같은 영속성 컨텍스트의 기존 객체인지, DB에서 다시 조회한 값인지 구분한다. “assertEquals가 성공했다”가 곧 “DB에 확정됐다”는 뜻은 아니다. 통합 JDBC 예제는 서비스 종료 뒤 SQL로 최종 상태를 확인한다.

## 21.5 동시성 테스트의 실패를 숨기지 않는다

CountDownLatch로 시작 구간을 모으고 Future 결과를 모두 회수한다. 작업 스레드의 예외를 버리면 성공 횟수가 줄었는데도 테스트가 통과할 수 있다. 단순 `Thread.sleep` 하나로 순서를 추측하는 테스트는 환경에 따라 흔들린다.

동시성 테스트는 최종 재고뿐 아니라 예약 수·Outbox 수·성공 응답 수를 함께 검증한다. 재고가 0이어도 성공 예약이 12개면 실패다. 테스트 반복이 경쟁 버그를 완전히 증명해 제거하는 것은 아니므로 SQL의 원자성·제약·격리 모델 설명도 필요하다.

## 21.6 목표 DB와 테스트 대역

Testcontainers는 실제 DB 제품을 테스트 수명에 맞춰 띄우는 데 유용하다. Docker 엔진과 이미지 다운로드가 필요하며 H2와 같은 환경은 아니다. 실제 운영과 같은 주요 버전·스키마 마이그레이션을 사용하고 unique·FK·격리·락 재시도를 검증한다.

Mock은 협력 객체 호출·결과를 통제하지만 DB 동시성이나 프록시를 대체하지 않는다. 예제는 트랜잭션 핵심을 Mock Repository로 검증하지 않고 실제 JdbcTemplate과 H2를 사용한다. 반대로 모든 도메인 계산에 앱 전체를 띄우면 테스트 속도와 원인 파악이 나빠진다.

## 실습: 결함을 넣으면 테스트가 실패하는가

별도 복사본에서 reserve의 `@Transactional`을 제거하고 품절 테스트를 실행한다. 예약 INSERT가 남으면 테스트가 실패해야 한다. 조건부 UPDATE를 조회→무조건 갱신으로 바꾼 실험에서는 경쟁 조건을 관찰한다. 이 연습은 테스트가 보장을 겨냥하는지 확인하는 방법이며 원본 코드에는 결함을 남기지 않는다.

## 확인 문제와 해설

**Q1. 모든 테스트에 Transactional을 붙이면 더 현실적인가?** 실제 서비스 경계를 가릴 수 있으므로 목적에 따라 선택한다.

**Q2. H2가 PostgreSQL 호환 모드이면 PostgreSQL 테스트를 대체하는가?** 문법 호환 일부와 제품의 동시성·쿼리 계획은 다르다.

**Q3. 성공 경로만 있으면 무엇이 빠지는가?** 품절·중복·부분 저장·인증 거절·commit 실패·재시도 등 가장 중요한 보장이 빠질 수 있다.

## 참고자료

- [Boot 애플리케이션 테스트](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html)
- [테스트 트랜잭션](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/tx.html)
- [Testcontainers Java](https://java.testcontainers.org/)

---

[전체 목차](../index.md) · [← 이전 장](../20-cache/chapter.md) · [다음 장 →](../22-observability/chapter.md)
