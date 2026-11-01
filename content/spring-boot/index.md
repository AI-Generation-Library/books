---
title: "Spring Boot 완전 정복"
description: "DI와 트랜잭션을 실행 원리와 실패 사례로 이해하는 6부 26장 실무형 기술서"
tags: ["Spring Boot", "Java", "DI", "트랜잭션", "한국어"]
enableToc: true
---

# Spring Boot 완전 정복

어노테이션을 외우는 데서 멈추지 않고 **객체가 어떻게 조립되고, 요청이 어디를 통과하며, 실패한 변경이 언제 되돌아가는지** 설명하는 책이다. 재고 예약 서비스 한 가지 사례를 DI·AOP·SQL·트랜잭션·보안·동시성·운영까지 연결한다.

Java의 클래스·인터페이스·예외와 HTTP·SQL의 기초를 접한 독자를 대상으로 한다. 약어는 풀어 쓰고 역할과 보장 범위를 구분한다. 기존 FastAPI 책의 ASGI 설명처럼 Spring에서는 Servlet·DispatcherServlet·컨테이너·프록시의 안쪽 흐름을 살펴본다.

## 이 책에서 깊게 다루는 것

- **네 핵심 개념:** POJO, IoC/DI, AOP, PSA. Boot의 Starter·자동 설정·내장 서버·운영 지원과 구분한다.
- **DI:** 생성자 주입, 후보 선택, Qualifier·Primary, 순환 의존성, 빈 스코프·생명주기, 테스트 대역.
- **트랜잭션:** ACID, 서비스 경계, checked/unchecked 롤백, 자기 호출, rollback-only, REQUIRED·REQUIRES_NEW·NESTED, 격리·락·재시도.
- **실무:** DTO·오류·보안·JPA·N+1·OSIV·멱등성·Outbox·캐시·테스트·관측·배포·장애 복구.

## 읽는 순서와 실행 기준

처음 읽는다면 1~10장을 순서대로 읽는다. DI와 트랜잭션을 집중 학습하려면 **3~6장 → 10장 → 12~15장 → 21장 → 25장**을 연결한다. FastAPI 경험자는 7장의 실행 스택 비교와 23장의 스레드·WebFlux 비교를 함께 본다.

실행 기준은 **Java 21 / Spring Boot 4.1.2 / Maven**이며 작성 환경에서는 Maven 3.9.11을 사용했다. 통합 예제는 MVC·JDBC·H2이며 테스트 23개와 별도 실행 JAR HTTP 시나리오 10건을 확인했다. 전체 사람 검수, JPA·Redis·브로커·운영 배포는 별도 범위다. 상세한 확인·미확인 경계는 [검증 기록](appendices/verification.md)에 있다.

각 장의 코드는 **첨부 프로젝트의 실행 코드**, **구조를 설명하는 부분 코드**, **독자가 수행할 확장 과제**를 구분한다. 코드 블록 하나를 모두 독립 실행 파일로 간주하지 않는다.

## 목차

### PART 1. Spring의 핵심 원리

- [01장. Spring과 Spring Boot, 네 가지 핵심 개념](01-spring-and-boot/chapter.md)
- [02장. Java·Maven·첫 애플리케이션](02-environment/chapter.md)
- [03장. IoC와 DI: 객체의 조립을 설계한다](03-dependency-injection/chapter.md)
- [04장. 빈 컨테이너·스코프·생명주기](04-container-lifecycle/chapter.md)
- [05장. AOP와 프록시의 실제 호출 경로](05-aop-proxy/chapter.md)
- [06장. PSA·Starter·자동 설정의 연결](06-psa-auto-configuration/chapter.md)

### PART 2. HTTP API와 데이터 접근

- [07장. Tomcat·Servlet·DispatcherServlet](07-servlet-mvc/chapter.md)
- [08장. DTO·검증·HTTP 오류 계약](08-validation-errors/chapter.md)
- [09장. 설정·프로파일·계층과 모듈 경계](09-configuration-architecture/chapter.md)
- [10장. JDBC·커넥션 풀·스키마 변경](10-jdbc-pool-schema/chapter.md)

### PART 3. 영속성과 트랜잭션

- [11장. JPA·Hibernate·영속성 컨텍스트](11-jpa-persistence/chapter.md)
- [12장. ACID와 서비스 트랜잭션 경계](12-transaction-acid/chapter.md)
- [13장. 롤백 규칙과 프록시 함정](13-transaction-rollback/chapter.md)
- [14장. 트랜잭션 전파와 자원 점유](14-transaction-propagation/chapter.md)
- [15장. 격리 수준·락·재시도](15-isolation-locking/chapter.md)
- [16장. N+1·페이징·인덱스·OSIV](16-query-performance/chapter.md)

### PART 4. 보안과 외부 시스템

- [17장. Spring Security·인증·인가](17-security/chapter.md)
- [18장. 외부 API·타임아웃·멱등성](18-http-resilience/chapter.md)
- [19장. 비동기·이벤트·Outbox](19-async-outbox/chapter.md)
- [20장. 캐시 일관성과 Redis 설계](20-cache/chapter.md)

### PART 5. 검증과 운영

- [21장. 단위·통합·트랜잭션 테스트](21-testing/chapter.md)
- [22장. Actuator·로그·메트릭·트레이스](22-observability/chapter.md)
- [23장. 성능 측정·스레드·WebFlux](23-performance-concurrency/chapter.md)
- [24장. 배포·종료·장애 복구와 버전 전환](24-deployment/chapter.md)

### PART 6. 통합 실습과 설계

- [25장. 실전 프로젝트: 재고 예약 API](25-capstone/chapter.md)
- [26장. 설계 판단과 기술 면접](26-architecture-interview/chapter.md)

## 부록과 다운로드

- [핵심 용어 사전](appendices/glossary.md)
- [실무 점검 워크북](appendices/workbook.md)
- [공식 참고자료](appendices/references.md)
- [검증 결과와 제한](appendices/verification.md)
- [재고 예약 API 실행 안내](examples/reservation-api/README.md)
- [원고와 실습 전체 ZIP](downloads/spring-boot-book.zip)
- [재고 예약 API 코드 ZIP](downloads/reservation-api.zip)

Codex가 사용자 요청과 공식 자료를 바탕으로 직접 집필한 AI 생성 원고다. 확인되지 않은 모델 ID는 기록하지 않았으며, 상세 입력·판단은 [생성 기록](generation-input.json)에 있다. 저장소의 CC0 라이선스를 따른다. 공식 자료의 예제를 길게 복제하지 않고 자체 설명과 실습을 작성했다.
