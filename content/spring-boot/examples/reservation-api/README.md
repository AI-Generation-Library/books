# 재고 예약 API

Java 21, Spring Boot 4.1.2, Maven 기반의 실행 예제입니다. MVC·JDBC·H2·Security·Actuator를 사용하며 생성자 DI, 서비스 트랜잭션, 롤백·전파·자기 호출, 조건부 재고 갱신, 멱등 키, Outbox 기록을 검증합니다.

## 준비와 실행

JDK 21과 Maven 3.6.3 이상이 필요합니다. 작성 환경의 실제 Maven은 3.9.11입니다. Maven Wrapper는 포함하지 않았습니다. 첫 실행은 Maven Central에 접근할 수 있어야 합니다.

```powershell
java -version
mvn -version
mvn verify
$env:APP_DEMO_PASSWORD = 'local-practice-change-me'
java -jar target/reservation-api-1.0.0.jar
```

개발 실행은 `mvn spring-boot:run`으로도 가능합니다. 비밀번호 환경변수가 없거나 비어 있으면 기동하지 않습니다. 예시 비밀번호는 로컬 실습용이며 외부 계정에 재사용하지 마세요.

서버는 `127.0.0.1:8080`에 바인딩합니다. 메모리 DB의 BOOK-1 초기 재고는 5개이고 프로세스를 종료하면 모든 예약·멱등 키·Outbox가 사라집니다. `schema.sql`과 `data.sql`은 폐기 가능한 실습 환경 전용입니다.

## PowerShell에서 요청하기

다른 터미널에서 다음을 실행합니다. 두 창의 비밀번호가 같아야 합니다. 직접 Authorization 헤더를 사용하므로 PowerShell 5.1에서도 같은 흐름을 사용할 수 있습니다.

```powershell
$demoPassword = 'local-practice-change-me'
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("buyer:$demoPassword"))
$headers = @{ Authorization = "Basic $basic" }
Invoke-RestMethod 'http://127.0.0.1:8080/actuator/health'
$csrf = Invoke-RestMethod 'http://127.0.0.1:8080/csrf' -Headers $headers -SessionVariable apiSession
$headers[$csrf.headerName] = $csrf.token
$body = @{ requestKey = 'demo-1'; sku = 'BOOK-1'; quantity = 2 } | ConvertTo-Json
$first = Invoke-RestMethod 'http://127.0.0.1:8080/api/reservations' -Method Post -Headers $headers -WebSession $apiSession -ContentType 'application/json' -Body $body
$first
$second = Invoke-RestMethod 'http://127.0.0.1:8080/api/reservations' -Method Post -Headers $headers -WebSession $apiSession -ContentType 'application/json' -Body $body
$first.id -eq $second.id
Invoke-RestMethod "http://127.0.0.1:8080/api/reservations/$($first.id)" -Headers $headers -WebSession $apiSession
```

health는 UP, 두 예약 응답은 200이며 동일한 id를 반환하고 마지막 비교는 True입니다. 최초 생성과 같은 키 재조회를 모두 200으로 정의한 명령 API입니다. JSON 객체의 필드 순서는 계약이 아닙니다.

실패 시 `Invoke-RestMethod`가 예외를 던지는 것은 정상입니다. 아래 시나리오의 HTTP 상태와 본문 code를 확인하세요.

| 요청 | 기대 결과 |
| --- | --- |
| 같은 키 demo-1, 수량 3 | 409 IDEMPOTENCY_CONFLICT |
| 새 키 demo-2, 수량 4 (현재 재고 3) | 409 OUT_OF_STOCK, 부분 예약 없음 |
| 새 키 demo-3, 수량 0 | 400 INVALID_REQUEST |
| 인증 없는 GET `/api/reservations/missing` | 401 |
| Basic 헤더만 있고 CSRF 토큰 없는 POST | 이 필터 구성에서는 401 |
| reader 계정으로 올바른 토큰을 받아 POST | 403 |
| reader 계정으로 buyer 예약 조회 | 404 NOT_FOUND |

reader는 같은 실습 비밀번호를 사용합니다. reader를 시험할 때는 인증 헤더와 `/csrf` 세션도 reader용으로 새로 만드세요. CSRF 검사가 Basic 인증보다 먼저 거절할 수 있으므로 “인증 헤더 전송”과 “인증 완료”를 구분합니다. Security 오류는 기본 응답이고 MVC 업무·검증 오류는 ProblemDetail 형식입니다.

## 테스트

```powershell
mvn test
mvn -Dtest=DiTests test
mvn -Dtest=TransactionTests test
mvn -Dtest=ReservationTests test
mvn -Dtest=HttpTests test
```

총 23개입니다. `DiTests` 2개는 순수 주입과 컨테이너 조립, `TransactionTests` 8개는 외부 호출·자기 호출·checked/unchecked 롤백·rollback-only·REQUIRES_NEW, `ReservationTests` 7개는 원자성·멱등성·소유권·도메인 검증·동시 주문, `HttpTests` 6개는 실제 임의 포트 서버와 인증·CSRF·역할·검증·예약을 확인합니다.

동시 주문 테스트는 재고 5에 12건을 요청해 성공 5·품절 7·예약 5·Outbox 5·재고 0을 검증합니다. 테스트 자체에 `@Transactional`을 붙이지 않아 실제 서비스 프록시와 commit/rollback 경계를 관찰합니다. H2 DB 이름을 테스트 클래스별로 구분하며 각 서비스 테스트는 필요한 테이블을 초기화합니다.

작성 시점의 실행 환경과 결과는 [검증 기록](../../appendices/verification.md)에 있습니다. 기능 검증을 운영 처리량 보장으로 해석하지 않습니다.

## 구현 범위

사용자+요청 키가 같고 SKU·수량도 같으면 이전 예약을 돌려줍니다. 동일 키에 다른 본문은 충돌입니다. 동시 요청이 사전 조회를 함께 통과하면 DB UNIQUE가 최종적으로 막으며 중복 예외는 트랜잭션 밖에서 409로 변환합니다. 클라이언트는 같은 키와 본문으로 제한적으로 다시 확인할 수 있습니다.

Outbox는 예약과 같은 DB 트랜잭션에 사건을 기록하는 단계까지 제공합니다. 메시지 브로커·발행기·다중 작업자·중복 소비·CDC는 구현하지 않았습니다. JPA·Redis·외부 결제·JWT·Docker·클라우드도 별도 확장 과제입니다. 목표 DB로 바꾸면 해당 DB의 제약·잠금·격리·마이그레이션 테스트를 추가해야 합니다.

Basic 자격 증명은 암호화가 아니므로 실제 원격 사용에는 TLS가 필요합니다. 현재 메모리 계정 두 개·공통 데모 비밀번호·H2 데이터로 공개 서비스를 운영하지 않습니다. 서비스 계층은 소유자 조건과 핵심 입력을 검증하지만 HTTP 외 진입점을 추가하면 그 진입점의 인증·역할 정책도 연결해야 합니다.

[책 목차](../../index.md) · [통합 프로젝트 장](../../25-capstone/chapter.md)
