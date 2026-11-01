---
title: "24장. 배포·종료·장애 복구와 버전 전환"
description: "실행 JAR·컨테이너·자원 한도·readiness·graceful shutdown·스키마 호환·복구 훈련과 Boot 3→4 전환을 정리한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 24
part: 5
enableToc: true
---

> PART 5. 검증과 운영

## 도입: 새 버전 배포 중 처리하던 주문이 끊겼다

앱 프로세스를 강제 종료하자 응답 전송 중이던 요청이 끊겼다. 새 버전은 스키마 컬럼을 이미 삭제해 이전 버전으로 돌아갈 수도 없다. 배포는 JAR을 복사하는 작업뿐 아니라 트래픽·프로세스·스키마·복구 순서를 조율하는 일이다.

## 24.1 한 번 만든 산출물을 이동한다

테스트한 코드에서 `mvn verify`로 실행 JAR을 만들고 버전·commit·의존성 정보를 연결한다. 환경마다 다시 컴파일하기보다 같은 산출물에 외부 설정을 주입하면 차이를 줄일 수 있다. 비밀 키나 실제 `.env`를 JAR·이미지에 넣지 않는다.

다음 Dockerfile은 구조 설명용이며 이미지 빌드·실행은 이 책의 검증 범위 밖이다.

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/reservation-api-1.0.0.jar app.jar
USER 10001:10001
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

실제 배포에서는 검증한 패치 이미지와 digest를 고정하고 취약점·라이선스를 검사한다. 예제 앱의 `server.address=127.0.0.1`은 컨테이너 외부 접근을 막으므로 배포 환경에서는 의도적으로 바인딩을 조정해야 한다. H2 메모리 데이터·데모 계정을 운영 데이터 저장소·인증 체계로 교체하는 작업도 필요하다. Dockerfile 한 장을 추가했다고 운영 준비가 완료되는 것은 아니다.

## 24.2 JVM 메모리와 컨테이너 한도

Java heap 외에도 metaspace·스레드 스택·direct buffer·코드 캐시·네이티브 메모리를 쓴다. 컨테이너 메모리 전체를 Xmx로 채우면 다른 영역 때문에 강제 종료될 수 있다. JVM이 컨테이너 한도를 어떻게 인식하는지 확인하고 실제 부하에서 총 RSS와 GC를 관찰한다.

CPU limit은 GC·요청 실행·JIT에도 영향을 준다. 개발 노트북에서의 결과를 작은 컨테이너에 그대로 적용하지 않는다. OOM의 원인이 Java heap 부족인지 운영체제의 프로세스 종료인지 구분해 로그와 종료 코드를 본다.

## 24.3 graceful shutdown의 전체 순서

먼저 readiness를 내려 신규 트래픽을 빼고, 라우터 전파 시간을 고려한 뒤 기존 요청을 완료할 시간을 준다. 애플리케이션은 정상 종료 신호를 받아 컨텍스트를 닫으며 자원을 정리한다. 플랫폼의 종료 유예 시간이 앱의 처리·정리 시간보다 짧으면 강제 종료될 수 있다.

예제는 `server.shutdown=graceful`, `spring.lifecycle.timeout-per-shutdown-phase=20s`를 명시한다. 이 시간은 모든 외부 작업의 무조건 완료 보장이 아니다. 스레드 풀·메시지 처리·긴 스트림의 종료 정책도 정해야 한다. Windows IDE의 Stop과 Linux SIGTERM이 같은 동작인지 별도 확인한다.

## 24.4 롤백 가능한 배포와 데이터 복구는 다르다

이전 앱 버전으로 돌아가는 것과 DB를 이전 상태로 복원하는 것은 다른 작업이다. 이미 생성된 예약과 결제를 단순히 이전 스냅샷으로 덮으면 데이터가 사라질 수 있다. 호환 가능한 스키마 변경과 상태 전이를 먼저 설계한다.

**RPO — Recovery Point Objective**는 허용 가능한 데이터 손실 시점 범위, **RTO — Recovery Time Objective**는 복구까지의 목표 시간이다. 백업 파일 존재만 확인하지 말고 복원·무결성·서비스 재개를 실제로 연습한다. 예제의 메모리 DB는 이런 지속성 보장을 제공하지 않는다.

## 24.5 Boot 3에서 4로 이동할 때

단순 버전 문자열 변경으로 끝내지 않는다. Framework·Security·Jackson·Servlet·테스트 모듈의 호환성을 확인한다. Boot 4의 모듈 분리 때문에 이전 Starter나 테스트 import를 그대로 복사하면 컴파일이 깨질 수 있다. 이 책은 `spring-boot-starter-webmvc`와 JDK HttpClient 기반 실제 HTTP 테스트를 사용한다.

1. 현재 버전의 테스트와 의존성 트리를 확보한다.
2. 대상 Boot 릴리스의 공식 migration guide와 요구 JDK·빌드 도구를 확인한다.
3. deprecated API와 Jackson 설정·직렬화 계약, Security matcher와 예외 응답을 검사한다.
4. 실제 DB 마이그레이션·쿼리·트랜잭션·HTTP 계약 테스트를 실행한다.
5. 카나리나 단계적 배포에서 지연·실패·직렬화 차이를 관찰한다.

이 책의 버전은 재현 기준이므로 이후 보안 패치가 나오면 변경 내용을 확인해 업데이트한다. 아직 실행하지 않은 버전을 검증된 것으로 표시하지 않는다.

## 실습: 배포 전 실패 시나리오 세 개

비밀번호 설정 누락, DB 연결 실패, 종료 중 요청의 세 경우에 대해 기동 여부·readiness·응답·로그·재시도 정책을 기록한다. 배포 환경이 없다면 표를 먼저 작성하되 실제 성공으로 기록하지 않는다. 운영 전에는 H2를 목표 DB로 바꾸고 백업 복원과 재기동 후 멱등 키 보존을 확인한다.

## 확인 문제와 해설

**Q1. graceful shutdown이면 commit 후 끊긴 응답이 자동 복구되는가?** 응답 유실은 여전히 가능하다. 멱등 키와 상태 조회가 필요하다.

**Q2. 앱 롤백으로 삭제한 컬럼이 복원되는가?** 코드 버전과 DB 스키마는 독립적으로 관리해야 한다.

**Q3. 이미지 태그 21이면 항상 같은 JDK인가?** 태그가 가리키는 패치가 바뀔 수 있으므로 재현에는 digest와 버전 기록이 필요하다.

## 참고자료

- [Boot Dockerfiles](https://docs.spring.io/spring-boot/reference/packaging/container-images/dockerfiles.html)
- [Graceful shutdown](https://docs.spring.io/spring-boot/reference/web/graceful-shutdown.html)
- [Spring Boot 4.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)

---

[전체 목차](../index.md) · [← 이전 장](../23-performance-concurrency/chapter.md) · [다음 장 →](../25-capstone/chapter.md)
