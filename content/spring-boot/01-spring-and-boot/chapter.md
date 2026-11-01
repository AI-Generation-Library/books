---
title: "01장. Spring과 Spring Boot, 네 가지 핵심 개념"
description: "POJO·IoC/DI·AOP·PSA를 구분하고 Spring Framework와 Spring Boot가 각각 해결하는 문제를 예약 서비스로 설명한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 1
part: 1
enableToc: true
---

> PART 1. Spring의 핵심 원리

## 도입: 어노테이션을 외웠는데 장애는 설명할 수 없다

예약 API에 `@Service`와 `@Transactional`을 붙였다. 정상 주문은 성공하지만 품절 상황에서 이미 저장한 예약이 남는다. “Spring이 알아서 롤백한다”는 설명으로는 원인을 찾을 수 없다. 객체를 누가 만들었는지, 호출이 프록시를 통과했는지, 어떤 예외가 밖으로 나갔는지, SQL이 어떤 연결에서 실행됐는지를 추적해야 한다.

이 책은 **재고 5개에 예약 12건이 동시에 들어오는 서비스**를 공통 사례로 사용한다. 성공한 예약 수와 남은 재고가 맞아야 하고, 응답을 못 받은 고객이 재시도해도 재고가 다시 줄면 안 된다. DI부터 관측성까지의 개념은 이 요구를 구현하기 위한 도구다.

## 1.1 Spring과 Boot는 어떤 관계인가

Spring Framework는 Java 애플리케이션의 객체 조립, 공통 처리, 데이터 접근, 웹 요청 처리를 지원하는 기반이다. Spring Boot는 그 위에서 의존성 조합, 조건에 따른 구성, 서버 실행, 운영용 기능을 일관된 출발점으로 제공한다. Boot 없이 Spring을 사용할 수 있고, Boot를 사용해도 Spring의 객체 수명과 트랜잭션 규칙을 이해해야 한다.

Java는 언어이고 JVM은 바이트코드를 실행하는 런타임이다. Tomcat은 HTTP 요청을 Servlet 규약으로 넘기는 서버·컨테이너이고, Spring MVC는 그 요청을 컨트롤러와 연결한다. Hibernate는 ORM 구현체이고 JPA는 객체와 관계형 데이터의 매핑·영속성 API 규약이다. 이 이름들을 모두 “Spring 서버”로 합치면 문제의 담당 계층을 놓친다.

| 이름 | 담당하는 책임 | 예약 서비스에서 보이는 지점 |
| --- | --- | --- |
| Java / JVM | 프로그램 표현 / 실행 | 클래스, 스레드, GC |
| Spring Framework | 객체와 애플리케이션 기반 | DI, AOP, MVC, 트랜잭션 추상화 |
| Spring Boot | 애플리케이션 구성·실행 관례 | Starter, 자동 설정, 실행 JAR |
| Tomcat | HTTP·Servlet 실행 | 소켓에서 요청 객체로 변환 |
| JDBC 드라이버 | Java와 DB 통신 | SQL 전달, 결과 수신 |
| DBMS | 데이터·제약·동시 접근 제어 | UNIQUE, 행 잠금, commit |

## 1.2 흔히 말하는 네 가지 핵심 개념

POJO·IoC/DI·AOP·PSA는 Spring을 설명할 때 널리 쓰는 학습용 묶음이다. 공식적으로 모든 기능을 정확히 네 개로 분류해야 한다는 뜻은 아니다.

**POJO — Plain Old Java Object.** 특정 프레임워크의 거대한 기반 클래스를 상속하지 않아도 도메인 규칙을 Java 객체로 표현할 수 있다는 관점이다. `Stock.reserve(3)`은 서버가 없어도 테스트할 수 있어야 한다. 어노테이션을 하나 붙였다고 POJO 여부를 기계적으로 판정하기보다 비즈니스 규칙이 실행 환경에 얼마나 얽혔는지 살펴본다.

**IoC — Inversion of Control, 제어의 역전.** 객체가 협력자를 직접 찾고 생성하는 대신 조립 책임을 바깥으로 옮긴다. **DI — Dependency Injection, 의존성 주입**은 이 관점을 구현하는 방법이다. 서비스 생성자에 저장소를 전달하면 서비스는 저장소가 운영 DB인지 테스트용 대역인지 몰라도 된다. DI는 Spring 전용 문법이 아니다.

**AOP — Aspect-Oriented Programming, 관점 지향 프로그래밍.** 트랜잭션·권한 검사·관측 같은 여러 메서드에 걸친 관심사를 실행 경계에 적용한다. Spring AOP에서는 보통 원본 객체 앞에 프록시를 둔다. 호출 경로를 바꾸는 것이지 어노테이션이 Java 메서드 자체를 마법처럼 변경하는 것은 아니다.

**PSA — Portable Service Abstraction, 일관된 서비스 추상화.** 구현 기술이 달라도 호출자가 공통 인터페이스로 작업할 수 있게 한다. 예를 들어 `PlatformTransactionManager`는 서로 다른 데이터 접근 기술의 트랜잭션 경계를 공통 방식으로 다룬다. 추상화가 모든 DB의 잠금과 SQL 문법까지 같게 만들지는 않는다.

## 1.3 Boot의 특징도 별도로 구분한다

Boot의 실용적인 출발점을 네 가지로 정리하면 **Starter, 자동 설정, 내장 서버, 운영 지원**이다. Starter는 의존성 묶음이고, 자동 설정은 클래스·설정·기존 빈 등 조건을 보고 구성을 제공한다. 내장 서버 덕분에 웹 앱을 `java -jar`로 실행할 수 있으며, Actuator는 상태와 관측 정보를 제공한다.

Starter를 추가하는 행위와 빈을 생성하는 행위는 같지 않다. 전자는 빌드 도구가 JAR을 가져오는 단계이고, 후자는 실행 중 컨테이너가 객체를 구성하는 단계다. 또한 Actuator를 추가했다고 수집 서버와 알림 정책까지 자동 완성되는 것은 아니다. [Boot 빌드 시스템](https://docs.spring.io/spring-boot/reference/using/build-systems.html)과 [자동 설정 문서](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)의 구분을 기준으로 읽는다.

## 1.4 네 개념을 하나의 요청에 연결하기

```text
HTTP 요청
  → Controller
  → ReservationService의 프록시: 트랜잭션 시작
  → 실제 ReservationService: 예약 규칙 실행
  → Repository → JdbcTemplate → Connection → DB
  ← 결과 반환
  ← 프록시: commit 성공 후 호출자에게 결과 전달
```

서비스가 저장소를 생성자로 받는 것이 DI다. 서비스의 순수한 입력 검증은 POJO 관점으로 읽을 수 있다. 서비스 앞에서 시작·종료를 처리하는 것은 AOP다. 데이터 접근 기술에 맞는 트랜잭션 매니저를 연결하는 것은 PSA다. Boot는 필요한 라이브러리와 조건이 맞을 때 이 구성을 준비하는 일을 돕는다.

서비스 메서드가 반환해도 commit이 실패할 수 있다. 따라서 “return 문에 도달했다”와 “고객에게 성공을 확정했다”는 다르다. 이것이 뒤에서 프록시 밖으로 나가는 시점을 반복해서 확인하는 이유다.

## 실습: 책임 지도를 먼저 그린다

[통합 예제](../examples/reservation-api/README.md)의 `ReservationController`, `ReservationService`, `ReservationRepository`, `SecurityConfig`를 열고 다음 질문에 답한다.

1. HTTP 요청 본문의 형식을 검사하는 위치는 어디인가?
2. 재고와 예약을 함께 확정하는 경계는 어디인가?
3. SQL 문자열을 실행하는 객체와 실제 데이터 무결성을 지키는 시스템은 무엇인가?

답은 각각 Controller의 검증 경계, Service의 트랜잭션 경계, JdbcTemplate과 DB 제약·원자적 갱신이다. Repository의 메서드마다 따로 성공해도 서비스 전체가 원자적이라는 보장은 생기지 않는다.

## 실무에서 피할 오해

DI가 있으면 좋은 설계가 자동으로 만들어진다는 생각부터 버린다. 생성자 인자가 열다섯 개라면 주입 방식보다 서비스 책임이 너무 큰지 검토한다. 모든 클래스에 인터페이스를 만드는 것도 목표가 아니다. 변경 축과 테스트 경계에 맞춰 추상화를 둔다.

Boot가 DB 장애, 잠금 대기, 인증 정책까지 대신 결정하지는 않는다. 설정 파일에서 숫자 하나를 바꾸기 전에 그 숫자가 어떤 자원을 제한하는지 설명할 수 있어야 한다.

## 확인 문제와 해설

**Q1. 생성자로 `new FakeRepository()`를 넘기면 DI인가?** 그렇다. 객체 조립을 바깥에서 했으므로 DI다. 컨테이너는 조립 자동화와 생명주기 관리를 추가한다.

**Q2. `@Transactional`은 DB 기능인가, Spring 기능인가?** 선언과 인터셉트는 Spring의 기능이고 실제 원자적 commit·rollback과 격리는 DB·드라이버·트랜잭션 자원이 구현한다.

**Q3. POJO·DI·AOP·PSA와 Starter·자동 설정은 같은 분류인가?** 전자는 설계와 실행 기반의 개념이고 후자는 Boot가 제공하는 편의와 구성 방식이다.

## 참고자료

- [Spring Framework 개요](https://docs.spring.io/spring-framework/reference/overview.html)
- [DI](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
- [트랜잭션 추상화](https://docs.spring.io/spring-framework/reference/data-access/transaction/strategies.html)

---

[전체 목차](../index.md) · [다음 장 →](../02-environment/chapter.md)
