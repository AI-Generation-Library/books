---
title: "09장. 설정·프로파일·계층과 모듈 경계"
description: "외부 설정의 우선순위와 타입 검증, 프로파일의 경계, 기능별 패키지와 서비스 책임을 구체화한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 9
part: 2
enableToc: true
---

> PART 2. HTTP API와 데이터 접근

## 도입: 운영에서만 테스트 결제 서버를 호출한다

코드의 URL은 올바른데 실제 요청은 다른 곳으로 간다. 컨테이너의 환경변수가 파일 값을 덮어쓰고 있을 수 있다. 설정은 단순 텍스트가 아니라 배포 환경과 애플리케이션 사이의 입력 계약이다.

## 9.1 설정 값의 출처를 추적한다

Boot는 파일, 환경변수, 명령행 인자 등 여러 PropertySource를 합친다. 일반 실행에서 명령행 인자는 환경변수와 application 파일보다 높은 우선순위를 가질 수 있다. 테스트 속성처럼 추가 우선순위도 있으므로 세 가지 예만을 전체 규칙으로 외우지 않는다. [외부 설정 문서](https://docs.spring.io/spring-boot/reference/features/external-config.html)의 실제 순서를 확인한다.

비밀번호는 소스의 기본값으로 두지 않는다. 예제는 `app.demo-password=${APP_DEMO_PASSWORD}`로 필요한 입력을 명시한다. 누락되면 기동 실패로 드러난다. 이것은 두 학습용 계정의 설정이며 운영 계정 저장소 설계는 별도다.

## 9.2 타입 있는 설정

설정이 많으면 여러 `@Value` 문자열보다 `@ConfigurationProperties`로 관련 값을 묶는다. 다음은 확장 설계용 코드다. 통합 예제에 자동 등록된 구성은 아니다.

```java
@Validated
@ConfigurationProperties(prefix = "payment")
public record PaymentProperties(
    @NotNull URI baseUrl,
    @NotNull Duration readTimeout
) {}
```

등록은 `@EnableConfigurationProperties(PaymentProperties.class)` 또는 속성 스캔으로 연결한다. null 검사만으로 음수·0초·허용되지 않는 프로토콜까지 검증되지는 않는다. Duration에 대한 별도 제약과 HTTPS·허용 호스트 정책은 요구에 맞게 추가한다. 단위를 문자열에 명시하면 밀리초와 초의 혼동을 줄일 수 있다.

## 9.3 프로파일의 역할과 한계

`application-local.properties`와 `application-prod.properties`는 환경별 구성 차이를 표현한다. 프로파일은 보안 경계가 아니다. `prod`라는 이름이 붙었다고 TLS·권한·백업이 자동 보장되는 것은 아니다. 비밀 값도 프로파일 파일에 커밋하지 않는다.

프로파일이 조합될수록 활성 빈과 최종 값의 경우의 수가 늘어난다. “local이면 메모리 DB, prod이면 외부 DB” 같은 필요한 차이부터 작게 시작하고, 중요한 조합의 기동 테스트를 마련한다. 배포된 애플리케이션이 어떤 프로파일과 버전으로 실행 중인지 민감 값 없이 확인할 수 있어야 한다.

## 9.4 계층은 파일 이름보다 의존 방향이다

Controller는 HTTP 해석과 응답, Service는 유스케이스의 순서와 트랜잭션, Repository는 저장 접근을 맡는다. 도메인 규칙은 HTTP 객체나 SQL 예외에 과도하게 기대지 않도록 둔다. 서비스가 `HttpServletRequest`와 ResponseEntity를 깊이 사용하면 배치·메시지 소비에서 재사용하기 어렵다.

기능이 늘면 `controller/`, `service/`, `repository/`라는 전역 폴더보다 `reservation/`, `payment/`, `catalog/` 내부에 필요한 계층을 두는 구성이 변경 범위를 읽기 쉽다. 작은 예제에서는 한 패키지로 출발하되 실제 책임이 생길 때 분리한다.

```text
reservation
  api          HTTP DTO·Controller
  application  예약 유스케이스·트랜잭션
  domain       상태 전이·규칙
  persistence  SQL/JPA 어댑터
```

인터페이스가 필요하다면 업무 관점의 계약을 application/domain 쪽에 두고 인프라가 구현하도록 할 수 있다. 모든 프로젝트에 네 폴더와 인터페이스를 강제하기보다 테스트 독립성과 변경 이유를 확인한다.

## 실습: 설정과 규칙을 분리한다

예제의 재고 초기값 5와 풀 크기 8을 찾는다. 전자는 학습 데이터, 후자는 실행 자원 설정이다. 둘을 같은 “환경 설정”으로 취급하면 재고처럼 지속돼야 할 업무 상태가 배포마다 초기화될 수 있다.

`--server.port=8081`로 실행해 파일 기본값을 덮어쓰는지 확인한다. 실습 비밀번호 환경변수를 제거한 별도 터미널에서는 기동 실패 원인을 읽는다. 실패를 감추기 위해 빈 비밀번호를 기본값으로 넣지 않는다.

## 확인 문제와 해설

**Q1. 환경변수면 안전한 비밀 관리인가?** 전달 경로일 뿐이다. 런타임 권한·진단 출력·회전·주입 시스템까지 관리해야 한다.

**Q2. Service가 SQL을 전혀 알아서는 안 되는가?** 구현 문자열과 저장 세부를 분리하되 트랜잭션·잠금·조회 비용 같은 보장은 유스케이스 설계에서 이해해야 한다.

**Q3. 모듈을 나누면 순환 의존이 자동 해소되는가?** 파일 위치만 바뀌어서는 안 된다. 호출 방향과 계약을 바꿔야 한다.

## 참고자료

- [Boot 프로파일](https://docs.spring.io/spring-boot/reference/features/profiles.html)
- [타입 안전한 구성 속성](https://docs.spring.io/spring-boot/reference/features/external-config.html)

---

[전체 목차](../index.md) · [← 이전 장](../08-validation-errors/chapter.md) · [다음 장 →](../10-jdbc-pool-schema/chapter.md)
