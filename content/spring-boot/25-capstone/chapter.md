---
title: "25장. 실전 프로젝트: 재고 예약 API"
description: "재고 예약 API의 요구·스키마·실행·실패 경로·멱등성·테스트를 하나로 연결하고 운영 확장 범위를 명시한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 25
part: 6
enableToc: true
---

> PART 6. 통합 실습과 설계

## 도입: 개념을 하나의 성공 조건으로 묶는다

이 프로젝트의 성공 조건은 서버가 켜지는 것보다 구체적이다. 재고 5개를 동시에 예약할 때 성공한 수량만 차감되고, 실패한 예약·이벤트는 남지 않아야 한다. 같은 업무 요청을 반복해도 추가 차감하지 않아야 하며, 인증과 역할·소유권도 검사해야 한다.

## 25.1 제공되는 구현과 확장 과제

실제 제공되는 것은 Java 21 / Boot 4.1.2 / MVC / JDBC / H2 / Spring Security / Actuator 애플리케이션이다. 생성자 DI, 서비스 트랜잭션, 조건부 재고 UPDATE, 멱등 키 UNIQUE, Outbox 기록, Bean Validation, ProblemDetail, Basic·CSRF를 연결했다.

JPA·Redis·실제 결제·브로커 전달·Docker·클라우드는 본문의 별도 설계·확장 과제다. 첨부 앱에는 실제 Outbox 발행기가 없고 H2 데이터는 재시작 시 사라진다. 데모 계정과 메모리 DB를 그대로 운영 배포하지 않는다.

## 25.2 파일 책임 지도

| 파일 | 읽으면서 확인할 질문 |
| --- | --- |
| ReservationApplication | 스캔 기준 패키지는 어디인가? |
| ReserveRequest | 클라이언트가 입력할 수 있는 필드는 무엇인가? |
| ReservationController | 인증 사용자와 요청 DTO를 어떻게 전달하는가? |
| ReservationService | 어떤 변경이 한 트랜잭션인가? |
| ReservationRepository | SQL의 조건·반환 행 수·바인딩은 무엇인가? |
| ApiErrors | 업무·형식·중복 오류를 어떻게 공개하는가? |
| SecurityConfig | 공개 경로·역할·CSRF의 경계는 어디인가? |
| schema.sql / data.sql | 무결성 제약과 실습 초기 데이터는 무엇인가? |

전체 폴더는 [실습 코드 안내](../examples/reservation-api/README.md)에서 시작한다. 이 표는 파일 이름을 외우기 위한 것이 아니라 변경 이유를 구분하기 위한 지도다.

## 25.3 요청 처리의 실제 순서

```text
POST /api/reservations
 → CSRF 토큰·Basic 인증·BUYER 권한 확인
 → JSON 변환·DTO 검증
 → 서비스 프록시: 트랜잭션
 → 사용자 + 요청 키로 기존 결과 검사
 → SKU 존재 검사
 → 예약 INSERT (사용자 + 키 UNIQUE)
 → 재고 조건부 UPDATE
 → Outbox INSERT
 → commit
 → JSON 응답 200
```

같은 키·본문이면 기존 결과를 반환하고 추가 감소·이벤트를 만들지 않는다. 같은 키의 다른 수량은 IDEMPOTENCY_CONFLICT다. 동시 사전 조회 경쟁은 DB UNIQUE로 막고, 실패한 트랜잭션 바깥에서 DUPLICATE_REQUEST 409로 변환한다.

재고 부족에서 예약 INSERT가 먼저 수행됐다는 사실이 중요하다. 그 뒤 예외가 나도 트랜잭션 덕분에 예약이 남지 않아야 한다. “실패 전에 아무것도 안 했으니 rollback이 됐다”는 약한 실험을 피했다.

## 25.4 실행 명령과 기대 결과

예제 폴더에서 실행한다.

```powershell
mvn verify
$env:APP_DEMO_PASSWORD = 'local-practice-change-me'
java -jar target/reservation-api-1.0.0.jar
```

다른 PowerShell 창에서 같은 비밀번호를 사용해 인증 헤더를 만들고 `/csrf`를 요청한다. 그때 받은 쿠키 세션과 토큰을 함께 POST로 보낸다. 복사 가능한 전체 명령은 [README](../examples/reservation-api/README.md)에 있다.

초기 BOOK-1 재고는 5다. 수량 2, 키 `demo-1`로 요청하면 200과 예약 ID가 나온다. 같은 요청을 다시 보내면 같은 ID이고 재고는 3이다. 같은 키로 수량 3을 보내면 409다. 새 키로 수량 4를 요청해도 409이며 기존 예약·재고는 바뀌지 않아야 한다.

새 키와 수량 3으로 성공한 다음 다른 새 키로 1을 요청하면 품절이어야 한다. GET `/api/reservations/{id}`는 소유자 buyer에게 결과를, reader에게 404를 반환한다. reader의 POST는 올바른 CSRF 토큰이 있어도 403이다.

## 25.5 테스트가 증명하는 범위

DiTests 2개, ReservationTests 7개, TransactionTests 8개, HttpTests 6개로 총 23개 테스트를 제공한다. 작성 시점의 실제 결과와 환경은 [검증 기록](../appendices/verification.md)에 있다.

이는 H2에서의 제약·원자적 갱신과 해당 Spring 구성의 프록시·트랜잭션·HTTP 동작을 확인한다. PostgreSQL lock timeout, 실제 네트워크 단절 중 commit, Redis 장애, 브로커 재전달, 운영 부하와 백업 복원을 증명하지 않는다.

## 25.6 운영으로 확장하는 순서

먼저 H2를 지속 DB로 바꾸고 schema/data 초기화를 버전 마이그레이션으로 옮긴다. 프로세스 재시작 뒤에도 예약·멱등 키·Outbox가 남는지 확인한다. 다음으로 실제 계정과 테넌트 정책·TLS·비밀 관리·rate limit을 도입한다.

Outbox 전달기를 추가할 때는 선점·lease·재시도·중복 소비를 테스트한다. 가격과 결제를 붙이면 PENDING·CONFIRMED·CANCELLED 등의 상태 전이와 보상을 설계한다. 예약 취소가 재고를 한 번만 복원하도록 취소 자체에도 멱등성을 둔다.

마지막으로 목표 DB에서 동시성·실행 계획·부하를 측정하고, readiness·종료·복구를 검증한다. 이 순서는 도구 목록이 아니라 아직 충족되지 않은 보장을 하나씩 추가하는 과정이다.

## 종합 과제와 평가 기준

**과제 A: 취소 API.** 소유자의 예약만 취소하고 같은 취소 요청이 반복돼도 재고를 한 번만 복원한다. 상태 변경과 재고 복원이 원자적이어야 하며 동시 취소 테스트가 필요하다.

**과제 B: 상품 두 개 예약.** 두 SKU의 재고를 함께 차감한다. 한쪽이 부족하면 모두 취소되고, 서로 반대 순서의 예약 요청에서 교착 위험을 줄이도록 잠금·갱신 순서를 일관되게 한다.

**과제 C: 프로세스 재기동.** 지속 DB를 연결해 예약 후 서버를 재시작하고 같은 키 요청이 기존 결과를 반환하는지 검증한다. 새 JVM이므로 singleton의 메모리만으로 해결할 수 없다.

## 확인 문제와 해설

**Q1. 이 예제를 왜 JDBC로 만들었는가?** SQL 실행·행 수·트랜잭션 경계를 직접 관찰하기 위해서다. JPA를 사용해도 같은 업무 보장은 설계해야 한다.

**Q2. 예약 ID와 requestKey는 왜 다른가?** 하나는 생성된 리소스 식별자, 다른 하나는 클라이언트 업무 시도의 중복 방지 식별자다.

**Q3. Outbox에 행이 있으면 알림이 전송됐는가?** 전달할 사건이 지속 DB 트랜잭션에 기록된 단계일 뿐이다. 예제에서는 메모리 DB 기록이며 외부 전달은 구현하지 않았다.

## 참고자료

- [예제 README](../examples/reservation-api/README.md)
- [검증 기록](../appendices/verification.md)
- [실무 점검 워크북](../appendices/workbook.md)

---

[전체 목차](../index.md) · [← 이전 장](../24-deployment/chapter.md) · [다음 장 →](../26-architecture-interview/chapter.md)
