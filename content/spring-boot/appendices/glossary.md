---
title: "핵심 용어 사전"
enableToc: true
---

처음 읽을 때는 정의와 관련 장을 함께 본다. 비슷한 이름이 같은 보장 범위를 뜻하지 않는다.

| 용어 | 풀어 쓴 이름·의미 | 관련 장 |
| --- | --- | --- |
| POJO | Plain Old Java Object. 실행 프레임워크에 과도하게 얽히지 않은 일반 Java 객체 설계 관점 | 1, 3 |
| IoC | Inversion of Control. 객체 생성·조립 등 제어 책임을 바깥으로 옮기는 관점 | 3 |
| DI | Dependency Injection. 필요한 협력 객체를 생성자 등으로 전달하는 방법 | 3 |
| Bean | Spring 컨테이너가 관리하는 객체. 모든 데이터 객체가 빈일 필요는 없다 | 4 |
| BeanDefinition | 객체 자체가 아닌 생성·주입·스코프의 명세 | 4 |
| ApplicationContext | 빈 관리와 환경·이벤트 등의 애플리케이션 기능을 제공하는 컨테이너 | 4 |
| Singleton scope | 컨테이너의 해당 빈 정의당 공유 인스턴스. 스레드 안전성을 자동 보장하지 않음 | 4 |
| Qualifier / Primary | 주입 후보를 좁히는 조건 / 기본 우선 후보 지정 | 3 |
| AOP | Aspect-Oriented Programming. 여러 실행 경계의 공통 관심사를 적용하는 방식 | 5 |
| Advice / Pointcut | 실행할 부가 동작 / 적용할 실행 지점을 고르는 조건 | 5 |
| Proxy / Target | 호출을 중개하는 객체 / 실제 업무 객체 | 5 |
| Self-invocation | 같은 대상 객체 내부 호출. 기본 프록시의 안쪽 설정이 적용되지 않을 수 있음 | 5, 13 |
| PSA | Portable Service Abstraction. 기술별 구현을 일관된 계약 뒤에 두는 추상화 | 6 |
| Starter | 기능별 관련 의존성을 묶은 시작점 | 2, 6 |
| BOM | Bill of Materials. 의존성 버전 조합을 관리하는 목록 | 2 |
| Auto-configuration | 클래스·빈·속성 조건을 평가해 기본 구성을 제공하는 방식 | 6 |
| Back-off | 사용자가 해당 역할의 구성을 제공하면 일부 자동 설정이 물러나는 동작 | 6 |
| Servlet | Java 서버와 웹 애플리케이션의 요청·응답 처리 규약 | 7 |
| DispatcherServlet | Spring MVC의 중앙 요청 진입점 | 7 |
| HandlerMapping / Adapter | 핸들러 선택 / 선택된 핸들러 호출 방법 연결 | 7 |
| HttpMessageConverter | HTTP 본문과 Java 값 사이의 변환 | 7 |
| Filter / Interceptor | Servlet 요청 경계 / MVC 핸들러 경계의 가로채기 도구 | 7 |
| ASGI | Asynchronous Server Gateway Interface. Python 서버·앱의 비동기 메시지 계약 | 7 |
| DTO | Data Transfer Object. 경계를 넘는 데이터 계약 | 8 |
| Bean Validation | 객체·메서드 등에 선언한 제약을 검증하는 규약·인프라 | 8 |
| ProblemDetail | HTTP 오류의 표준 필드와 확장 코드를 표현하는 Spring 타입 | 8 |
| JDBC | Java Database Connectivity. Java의 관계형 DB 접근 API | 10 |
| DataSource / Connection | 연결 공급자 / 실제 작업의 연결·트랜잭션 자원 | 10 |
| Connection pool | 연결 재사용과 동시 점유 한도 관리 | 10 |
| JPA | Jakarta Persistence. Java 객체 영속성 규약 | 11 |
| ORM | Object-Relational Mapping. 객체와 관계형 데이터 사이의 매핑 | 11 |
| Hibernate | JPA 구현과 ORM 기능을 제공하는 라이브러리 | 11 |
| Persistence context | EntityManager가 엔티티 식별자·상태·변경을 관리하는 문맥 | 11 |
| Dirty checking | 관리 엔티티의 변경을 감지해 SQL 동기화 대상으로 반영 | 11 |
| Flush / Commit | DB로 변경 SQL 동기화 / 트랜잭션 확정. 서로 다름 | 11, 12 |
| ACID | Atomicity·Consistency·Isolation·Durability. 트랜잭션의 원자성·일관성·격리성·지속성 | 12 |
| Rollback-only | 해당 트랜잭션을 성공 확정할 수 없도록 표시한 상태 | 13 |
| Propagation | 기존 트랜잭션과 새 논리 경계를 연결하는 정책 | 14 |
| REQUIRED | 없으면 시작, 있으면 참여 | 14 |
| REQUIRES_NEW | 기존 경계를 중단하고 독립 물리 트랜잭션 생성 | 14 |
| NESTED | 지원하는 환경에서 savepoint 기반 부분 rollback | 14 |
| MVCC | Multi-Version Concurrency Control. 여러 데이터 버전을 이용한 동시성 제어 | 15 |
| Dirty read | 다른 트랜잭션의 미확정 값을 읽음 | 15 |
| Non-repeatable read | 같은 행을 반복 읽었을 때 값이 바뀜 | 15 |
| Phantom read | 같은 조건에 해당하는 행 집합이 반복 조회 중 바뀜 | 15 |
| Lost update / Write skew | 변경 덮어쓰기 / 서로 다른 행 수정이 합쳐져 규칙을 위반 | 15 |
| Optimistic lock | 버전 조건으로 변경 충돌을 감지 | 15 |
| Pessimistic lock | 필요한 대상의 경쟁 접근을 잠금으로 먼저 제한 | 15 |
| Deadlock | 서로의 자원을 기다리는 순환 대기 | 15 |
| N+1 | 기본 조회 뒤 각 결과의 연관 데이터 조회가 추가로 발생하는 패턴 | 16 |
| OSIV | Open Session/EntityManager in View. 웹 요청 동안 영속성 문맥을 유지하는 구성 | 16 |
| Keyset pagination | 마지막 정렬 키 이후의 구간을 조회하는 방식 | 16 |
| Authentication / Authorization | 누구인지 확인 / 해당 동작·객체에 대한 권한 확인 | 17 |
| CSRF | Cross-Site Request Forgery. 자동 전송 자격 증명 등을 악용한 요청 위조 | 17 |
| CORS | Cross-Origin Resource Sharing. 브라우저의 다른 출처 접근 정책 | 17 |
| JWT | JSON Web Token. payload 해석과 서명·발급자·대상·시각 검증은 다름 | 17 |
| Idempotency | 같은 업무 시도 반복에도 부수효과가 중복되지 않게 하는 계약 | 18 |
| Circuit Breaker | 실패 상태에 따라 외부 호출을 제한하고 회복을 탐색하는 장치 | 18 |
| Bulkhead | 특정 의존성이 전체 실행 자원을 독점하지 못하게 분리 | 18 |
| Outbox | 업무 데이터와 전달할 사건을 같은 DB 트랜잭션에 기록 | 19 |
| At-least-once | 적어도 한 번 전달을 지향하며 중복 가능성을 수용 | 19 |
| DLQ | Dead Letter Queue. 계속 실패한 메시지의 격리·조사·재처리 공간 | 19 |
| Saga | 여러 로컬 업무와 보상 동작으로 긴 프로세스를 관리 | 19 |
| TTL | Time To Live. 캐시·기록의 보관 시간 | 20 |
| Cache stampede | 같은 키의 동시 miss가 원본 조회 폭증을 유발 | 20 |
| Liveness / Readiness | 재시작 필요 판단 / 트래픽 수용 준비 판단 | 22 |
| Micrometer | 여러 관측 백엔드를 연결하는 계측 추상화 | 22 |
| Cardinality | 태그 값 조합으로 만들어지는 시계열 수의 규모 | 22 |
| MDC | Mapped Diagnostic Context. 로그에 연결하는 실행 문맥 | 22 |
| Trace / Span | 분산 작업 경로 / 경로 안의 개별 작업 구간 | 22 |
| SLI / SLO | Service Level Indicator / Objective. 관측 지표 / 그 목표 | 22 |
| Throughput / Latency | 완료 처리량 / 개별 작업의 지연 시간 | 23 |
| WebFlux | 반응형·비차단 흐름을 지원하는 Spring 웹 스택 | 23 |
| RPO / RTO | Recovery Point / Time Objective. 데이터 손실 시점 / 복구 시간 목표 | 24 |

[책 목차](../index.md)
