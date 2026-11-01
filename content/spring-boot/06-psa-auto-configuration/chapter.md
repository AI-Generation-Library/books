---
title: "06장. PSA·Starter·자동 설정의 연결"
description: "PSA의 보장 범위를 정리하고 Starter·BOM·조건부 자동 설정·사용자 빈의 우선 적용을 원인 분석 절차로 연결한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 6
part: 1
enableToc: true
---

> PART 1. Spring의 핵심 원리

## 도입: DB 라이브러리를 넣었더니 서버가 켜지지 않는다

JDBC Starter를 추가한 뒤 DataSource 설정 오류가 난다. 어제까지는 DB가 필요 없는 앱이었는데 의존성 하나가 기동 조건을 바꿨다. 자동 설정은 클래스패스와 환경에 반응하므로 의존성 변경은 실행 구조의 변경이기도 하다.

## 6.1 PSA의 핵심은 호출 계약이다

트랜잭션 매니저는 시작·commit·rollback 경계를 공통 형태로 제공한다. JDBC를 쓰면 해당 연결을 관리하는 매니저를, JPA를 쓰면 EntityManager와 연계하는 매니저를 사용할 수 있다. 호출자는 `@Transactional` 또는 `TransactionTemplate`을 통해 업무 경계를 표현한다.

공통 API가 있어도 모든 기술의 기능은 동일하지 않다. JDBC savepoint를 쓰는 중첩 트랜잭션과 JPA의 영속성 컨텍스트는 별도 문제이며, 반응형 트랜잭션은 스레드 로컬 기반 모델과 문맥 전달 방식이 다르다. PSA는 의미를 감추는 장치가 아니라 기술 종속 부분을 적절한 위치에 모으는 장치다.

## 6.2 Starter·BOM·자동 설정은 서로 다른 단계다

```text
pom.xml의 Starter
  → Maven이 필요한 JAR과 버전을 해석
  → 애플리케이션 클래스패스 형성
  → 자동 설정 후보와 조건 평가
  → 조건에 맞는 빈 정의 등록
  → 실제 빈 생성과 의존성 연결
```

BOM이 버전을 관리한다고 라이브러리가 모두 내려오는 것은 아니다. Starter가 클래스를 가져온다고 해당 기능이 반드시 켜지는 것도 아니다. 사용자가 이미 빈을 제공했거나 필요한 설정이 없거나 다른 조건이 불일치하면 자동 설정이 달라진다.

예제에서 H2 드라이버, JDBC Starter, datasource URL이 준비되면 DataSource·JdbcTemplate·트랜잭션 인프라를 구성할 수 있다. 서비스의 `@Transactional`은 이 인프라와 연결돼 동작한다. 예제는 한 DataSource를 사용하며, 여러 데이터소스에 같은 어노테이션을 붙이는 것만으로 분산 원자성이 생기지는 않는다.

## 6.3 조건을 읽는 법

**`@ConditionalOnClass`**는 특정 클래스가 존재하는지, **`@ConditionalOnMissingBean`**은 사용자가 이미 해당 역할의 빈을 제공했는지, **`@ConditionalOnProperty`**는 특정 설정이 만족되는지 판단하는 대표적인 도구다. 실제 조건은 구성마다 다르므로 이름만 보고 한 빈의 생성 원인을 단정하지 않는다.

진단은 다음 순서가 유용하다.

1. `mvn dependency:tree`로 어떤 모듈이 들어왔는지 확인한다.
2. `--debug`를 사용해 conditions report의 해당 자동 설정을 찾는다.
3. positive/negative match의 이유를 읽는다.
4. 사용자 정의 빈과 설정 값이 의도한 것인지 확인한다.
5. 필요한 설정만 바꾸고 기동·동작 테스트를 다시 실행한다.

Actuator의 conditions는 운영 정보를 드러낼 수 있으므로 인터넷에 무제한 노출하지 않는다. 문제 해결을 위해 잠깐 켰다면 접근 제어와 종료 후 원복도 함께 관리한다.

## 6.4 사용자 빈으로 교체할 때의 경계

일부 자동 설정은 사용자가 같은 역할의 빈을 정의하면 물러난다. 이를 **back-off**라고 부른다. 예를 들어 DataSource를 직접 제공하면 그 생성 책임과 설정 책임도 사용자가 가져온다. “Boot의 좋은 기본값에 내가 만든 설정이 조금만 더해진다”고 가정하면 풀 크기·계측·라이프사이클 설정을 놓칠 수 있다.

`spring.main.allow-bean-definition-overriding=true`로 이름 충돌을 무조건 허용하는 것은 조건부 구성을 이해한 것과 다르다. 무엇이 선택됐는지 불분명해지므로 명시적인 빈 이름·조건·프로파일부터 정리한다.

## 6.5 구성 속성과 자동 설정의 테스트

자체 라이브러리를 여러 서비스에 배포한다면 자동 설정의 활성·비활성 조건을 테스트한다. 클래스가 없을 때, 사용자가 빈을 제공했을 때, 속성이 꺼졌을 때의 결과가 문서와 일치해야 한다. 사용자 코드를 강제로 덮어쓰는 설정은 확장을 어렵게 만든다.

이 책은 커스텀 Starter 배포를 통합 예제에 포함하지 않는다. 작은 서비스에서는 명시적 `@Configuration`이 충분할 수 있다. 공유할 실제 사용처가 생겼을 때 모듈화 비용과 버전 호환성 책임을 평가한다.

## 실습: 설정 결과에서 출발한다

실습 비밀번호를 환경변수로 지정한 뒤 예제에서 `mvn spring-boot:run -Dspring-boot.run.arguments=--debug`를 실행한다. DataSource 관련 조건을 찾고 H2·JdbcTemplate·트랜잭션 매니저가 존재하는 경로를 설명한다. 로그를 공유할 때 민감한 설정 값은 제거한다.

다음 변형은 별도 복사본에서 한다. H2 의존성을 빼고 외부 DB 설정도 제공하지 않으면 DataSource 생성이 실패할 수 있다. 이때 서비스를 지우거나 트랜잭션 어노테이션을 제거하기보다 드라이버·URL·자동 설정 조건이라는 원인을 확인한다.

## 확인 문제와 해설

**Q1. PSA를 사용하면 DB 교체 테스트가 필요 없는가?** SQL 문법, 데이터 타입, 격리, 잠금, 실행 계획이 다르므로 여전히 필요하다.

**Q2. Starter를 제거했는데 컴파일이 되는 이유는?** 다른 의존성에서 전이적으로 같은 클래스가 들어왔을 수 있다. 실제 트리를 본다.

**Q3. 자동 설정 실패를 해결하는 첫 행동은?** 조건과 가장 깊은 원인 예외를 읽어 실패한 책임을 찾는다. 무관한 설정을 대량으로 추가하지 않는다.

## 참고자료

- [트랜잭션 전략](https://docs.spring.io/spring-framework/reference/data-access/transaction/strategies.html)
- [자체 자동 설정 작성](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html)
- [자동 설정](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)

---

[전체 목차](../index.md) · [← 이전 장](../05-aop-proxy/chapter.md) · [다음 장 →](../07-servlet-mvc/chapter.md)
