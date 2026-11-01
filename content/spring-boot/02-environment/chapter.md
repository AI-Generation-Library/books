---
title: "02장. Java·Maven·첫 애플리케이션"
description: "Java 21과 Boot 4.1.2로 버전을 고정하고 Maven 생명주기·의존성 관리·실행 JAR을 구분하며 예제를 시작한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 2
part: 1
enableToc: true
---

> PART 1. Spring의 핵심 원리

## 도입: IDE에서는 되는데 서버에서는 안 된다

팀원은 실행 버튼을 누르면 성공하고 CI는 `UnsupportedClassVersionError`를 낸다. IDE가 쓰는 JDK와 터미널의 JDK가 다르거나, 컴파일 타깃보다 실행 JVM이 오래됐을 가능성이 있다. “Java 설치 완료”보다 **어떤 실행 파일이 어떤 버전으로 컴파일하고 실행했는가**가 중요하다.

## 2.1 책의 실행 기준

이 책의 통합 예제는 Java 21, Spring Boot 4.1.2, Maven을 사용한다. 작성 환경에서 Maven 3.9.11을 사용했으며 실제 실행 결과는 [검증 기록](../appendices/verification.md)에 별도로 적는다. 이 버전은 재현 기준이며 모든 시점의 최신 버전이라는 뜻이 아니다. 2026-11-01에 확인한 [시스템 요구사항](https://docs.spring.io/spring-boot/system-requirements.html)은 Boot 4.1.2의 최소 Java 17과 Maven 3.6.3 이상을 명시한다. 책은 Java 21의 기능과 일관된 환경을 위해 21로 고정한다.

Boot 3 예제를 복사할 때 `spring-boot-starter-web`과 Boot 4의 `spring-boot-starter-webmvc`, 테스트 모듈과 패키지 이름 차이를 확인한다. `javax.servlet`과 `jakarta.servlet`을 섞지 않는다. 애플리케이션 코드를 고치기 전에 의존성 트리부터 맞춰야 한다.

```powershell
java -version
javac -version
mvn -version
```

`mvn -version`에 출력된 Java home도 읽는다. JRE만 있거나 PATH가 다른 JDK를 가리키면 빌드가 달라진다. 이 책은 Maven Wrapper 파일이 포함돼 있다고 가정하지 않는다. Maven을 설치해 `mvn` 명령을 사용한다.

## 2.2 pom.xml의 네 책임

`pom.xml`은 프로젝트 좌표, 의존성, 플러그인, 빌드 속성을 선언한다. 예제의 핵심은 다음과 같다. 전체 파일은 [pom.xml](../examples/reservation-api/pom.xml)에 있다.

```xml
<parent>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-parent</artifactId>
  <version>4.1.2</version>
  <relativePath/>
</parent>
<properties><java.version>21</java.version></properties>
```

Parent는 Boot와 맞는 라이브러리·플러그인 구성을 제공한다. 모든 의존성에 개별 버전을 붙이면 이 정합성을 쉽게 깨뜨린다. **BOM — Bill of Materials**는 의존성 버전의 조합을 관리하는 목록이다. BOM을 가져오는 것과 특정 라이브러리를 실제 dependencies에 넣는 것은 다른 일이다.

Starter JDBC에는 DB와 통신할 기반이 포함되지만 어떤 DB를 쓸지는 드라이버와 설정으로 정한다. 예제는 H2를 runtime scope로 사용한다. H2 테스트 성공을 PostgreSQL의 격리 수준이나 실행 계획 검증으로 확대하지 않는다.

## 2.3 Maven의 단계

| 명령 | 수행 범위 | 오해하기 쉬운 점 |
| --- | --- | --- |
| `mvn test` | 컴파일과 단위 테스트 단계 | 실행 JAR 제작까지 보장하지 않음 |
| `mvn package` | 테스트를 거쳐 패키징 | 배포 서버에 설치하는 명령 아님 |
| `mvn verify` | 패키징 후 검증 단계까지 | 통합 테스트는 플러그인 연결이 필요 |
| `mvn dependency:tree` | 해석된 의존성 확인 | 소스 import와 별개로 실제 충돌 진단 |
| `mvn spring-boot:run` | 개발 실행 | 운영 프로세스 관리 도구를 대신하지 않음 |

`-DskipTests`는 테스트를 생략하는 선택이다. 빌드 시간을 줄였다는 사실과 코드가 검증됐다는 사실을 혼동하지 않는다. 예제의 `*Tests`들은 기본 테스트 단계에서 실행되도록 구성했다.

## 2.4 main에서 서버 준비까지

```java
@SpringBootApplication
public class ReservationApplication {
    public static void main(String[] args) {
        SpringApplication.run(ReservationApplication.class, args);
    }
}
```

`@SpringBootApplication`은 구성 클래스, 컴포넌트 스캔, 자동 설정 활성화의 출발점이다. 예제는 `com.example.reservation` 아래에 구성과 서비스를 두므로 스캔 범위가 명확하다. 애플리케이션 클래스를 지나치게 깊은 패키지에 두면 형제 패키지의 서비스가 누락될 수 있다.

실행 과정은 대략 설정 준비 → 컨텍스트 준비 → 빈 정의 등록 → 필요한 빈 생성·후처리 → 웹 서버 시작 → 준비 완료 흐름이다. 세부 이벤트 순서를 외우기보다 초기화 시점의 객체가 아직 프록시나 모든 자원을 사용할 수 있는지 확인한다.

## 실습: API를 실행하고 재시작한다

```powershell
cd examples/reservation-api
mvn test
$env:APP_DEMO_PASSWORD = 'local-practice-change-me'
mvn spring-boot:run
```

다른 터미널에서 `Invoke-RestMethod http://127.0.0.1:8080/actuator/health`를 실행한다. 정상 기동했다면 status가 UP이다. `/api/reservations/missing`을 인증 없이 요청하면 401이다. 주문 호출은 CSRF 토큰과 쿠키가 필요하며 [예제 안내](../examples/reservation-api/README.md)의 명령을 따른다.

예제는 루프백 주소에만 바인딩하고 H2 메모리 DB를 사용한다. 재시작하면 재고가 5개로 초기화된다. 이는 학습을 위한 초기화 정책이지 운영 데이터 보존 방식이 아니다. 운영 DB에서 `data.sql`을 계속 실행하는 구성으로 옮기면 안 된다.

패키징은 `mvn package`, 실행은 `java -jar target/reservation-api-1.0.0.jar`다. JAR 안에 의존성이 들어가는 Boot 패키징과 일반 라이브러리 JAR의 차이를 확인한다. 환경변수는 실행 프로세스에도 전달해야 한다.

## 실패를 분류하기

의존성 다운로드 실패는 DNS·프록시·저장소 연결을 먼저 본다. `BeanCreationException`은 가장 아래쪽 원인 예외와 누락 설정을 읽는다. 포트 충돌은 `--server.port=8081`처럼 실행 포트를 바꿔 확인한다. 데이터베이스 접속 실패와 SQL 문법 오류는 같은 원인이 아니므로 함께 “DB 오류”로 처리하지 않는다.

## 확인 문제와 해설

**Q1. Parent 버전과 각 Spring 모듈 버전을 모두 독립적으로 최신으로 올려도 되는가?** 모듈 간 호환성이 깨질 수 있다. Boot가 관리하는 조합에서 시작하고 의도한 변경만 검증한다.

**Q2. `package`가 성공했는데 API가 실패할 수 있는가?** 있다. 빌드 환경에서 없는 운영 설정·네트워크·권한·데이터를 실행 시 요구할 수 있다.

**Q3. H2 데이터가 사라진 이유는?** 예제 URL이 메모리 DB이기 때문이다. `DB_CLOSE_DELAY=-1`은 JVM 안에서 마지막 연결 종료 후 유지하는 설정이지 프로세스 재시작 후 디스크 복원을 뜻하지 않는다.

## 참고자료

- [Maven 생명주기](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html)
- [Boot Maven Plugin](https://docs.spring.io/spring-boot/maven-plugin/index.html)
- [H2 기능](https://h2database.com/html/features.html)

---

[전체 목차](../index.md) · [← 이전 장](../01-spring-and-boot/chapter.md) · [다음 장 →](../03-dependency-injection/chapter.md)
