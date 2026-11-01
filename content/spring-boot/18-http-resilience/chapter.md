---
title: "18장. 외부 API·타임아웃·멱등성"
description: "RestClient·WebClient와 타임아웃 예산, 재시도·회로 차단·격벽, 결제 결과 불명과 멱등 키를 설계한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 18
part: 4
enableToc: true
---

> PART 4. 보안과 외부 시스템

## 도입: 결제 응답을 못 받았는데 다시 결제해도 되는가

결제 서버는 승인했지만 응답이 네트워크에서 사라질 수 있다. 우리 서버의 timeout은 결제 실패의 증거가 아니다. 예외를 보고 무조건 재시도하면 이중 결제가 된다. 외부 호출은 성공·실패뿐 아니라 **결과 불명** 상태를 다뤄야 한다.

## 18.1 클라이언트 선택

RestClient는 동기식 HTTP 호출 API이며 MVC·JDBC 기반 서비스에서 자연스러운 선택이 될 수 있다. WebClient는 반응형·비차단 흐름을 구성할 수 있지만 `.block()`을 호출하면 그 지점은 기다린다. 클라이언트의 이름보다 실제 실행 스레드와 사용하는 드라이버를 확인한다.

아래는 외부 호출을 확장할 때 사용할 구성 예시다. 통합 예제는 실제 결제 API를 호출하지 않는다.

```java
var jdkClient = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(1))
    .build();
var factory = new JdkClientHttpRequestFactory(jdkClient);
factory.setReadTimeout(Duration.ofSeconds(2));
var client = RestClient.builder()
    .requestFactory(factory)
    .baseUrl("https://payment.example.invalid")
    .build();
```

이는 `java.net.http.HttpClient`, `Duration`, Spring의 request factory·RestClient를 사용하는 부분 코드다. 주소는 의도적으로 실제 서비스가 아닌 예시다. 운영에서는 Boot가 구성한 builder의 관측·추적 사용자화를 보존할지 검토하고 TLS 검증을 끄지 않는다.

## 18.2 시간 예산을 나눈다

전체 API deadline이 3초라면 connect 2초 + read 2초를 세 번 재시도하는 설정은 맞지 않는다. DNS, 연결·TLS, 풀 획득, 응답 헤더·본문, 백오프, 우리 서버의 처리 시간을 합쳐 예산을 정한다. 클라이언트 구현마다 timeout의 정확한 범위가 다르므로 이름만으로 전체 요청 상한이라고 해석하지 않는다.

취소 요청을 보냈다고 상대 서버가 이미 수행한 부수효과가 취소되는 것도 아니다. 결제·예약 같은 변경 요청에는 외부 시스템과 공유하는 멱등 키와 상태 조회 경로가 필요하다.

## 18.3 재시도·회로 차단·격벽

**Retry**는 일시 실패에 다시 시도하는 것이다. 무작위 지터를 포함한 백오프, 최대 횟수, 전체 시간 예산을 둔다. 400 입력 오류나 권한 부족을 반복 호출해도 해결되지 않는다. 429는 서버의 Retry-After 계약을 고려하고, 변경 요청은 중복 실행 방어를 먼저 확인한다.

**Circuit Breaker**는 실패가 누적된 의존성 호출을 일정 조건에서 빠르게 차단하는 상태 기계다. 타임아웃을 대신하지 않고 원격 시스템을 수리하지도 않는다. half-open에서 제한된 탐색 호출로 회복을 판단한다.

**Bulkhead, 격벽**는 특정 외부 시스템이 전체 스레드·연결을 독점하지 못하게 동시 실행 자원을 나누는 방식이다. 큐가 무한이면 실패를 지연시킬 뿐이므로 큐 길이와 거절 정책도 필요하다.

## 18.4 DB 트랜잭션과 외부 결제를 한 줄로 묶지 않는다

DB 트랜잭션 안에서 결제 요청을 보낸다고 결제 서버와 DB가 하나의 ACID 트랜잭션이 되지는 않는다. 결제 성공 후 DB commit 실패, DB 성공 후 응답 유실, 취소 요청 실패를 각각 설계한다.

실무 흐름의 한 예는 짧은 트랜잭션으로 PENDING 예약·외부 요청 키 저장 → 트랜잭션 밖에서 결제 요청 → 짧은 트랜잭션으로 결과와 상태 전이 기록이다. 중간에 죽은 요청은 상태 조회·재처리로 복구한다. 예약 기한과 재고 해제는 별도 업무 규칙이다. 이를 여러 서비스에 걸친 보상 흐름으로 확장하면 Saga 관점을 적용할 수 있다.

## 18.5 통합 예제의 멱등성 계약

예제는 `(owner, requestKey)`를 중복 판단 범위로 한다. 같은 키·같은 SKU·수량이면 기존 예약을 반환하고, 같은 키에 본문이 달라지면 409다. 첫 요청과 재시도 모두 결과 200을 사용한다. 다른 사용자에게 같은 키가 있다고 충돌시키지 않는다.

두 요청이 완전히 동시에 들어오면 둘 다 사전 조회에서 없음으로 볼 수 있다. DB UNIQUE가 최종 경쟁을 막으며, 패배한 요청은 프록시 밖에서 409로 변환된다. 클라이언트는 같은 키·본문으로 제한적으로 다시 조회한다. 실패한 트랜잭션 안에서 예외를 잡고 곧바로 재조회하지 않는다.

키는 클라이언트의 한 업무 시도에서 고정해야 한다. 네트워크 retry마다 새 UUID를 만들면 중복 방지 의미가 사라진다. 예제는 키를 메모리 DB에만 저장하므로 프로세스 재시작 후에도 유지되는 운영 멱등성 보장은 제공하지 않는다.

## 실습: 같은 키의 의미를 검증한다

`sameKeyReplaysWithoutSecondDecrease`와 `sameKeyDifferentPayloadIsRejected`를 실행한다. 첫 테스트는 두 번 호출해도 재고가 한 번만 감소하고 Outbox가 한 행인지 본다. 두 번째는 같은 키로 수량을 바꿔 보냈을 때 원래 결과를 잘못 재사용하지 않고 거절하는지 본다.

외부 결제를 붙이는 확장 실습에서는 가짜 서버가 “처리는 성공했지만 응답을 끊음”을 재현하게 한다. 우리 앱이 중복 결제 없이 상태 조회로 복구하는지 확인한다. 단순 500 반환 테스트만으로 결과 불명을 검증했다고 하지 않는다.

## 확인 문제와 해설

**Q1. GET이면 무한 재시도해도 되는가?** 자원 고갈과 deadline을 고려해 횟수를 제한한다.

**Q2. 회로 차단기를 달면 타임아웃이 없어도 되는가?** 개별 호출이 언제 종료되는지 별도 제한이 필요하다.

**Q3. 멱등 키를 전역 키만으로 잡으면 어떤 문제가 있는가?** 사용자·테넌트 경계가 섞이거나 다른 사용자의 결과를 노출할 수 있다.

## 참고자료

- [Spring REST Clients](https://docs.spring.io/spring-framework/reference/integration/rest-clients.html)
- [HTTP 멱등 메서드 의미](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods)

---

[전체 목차](../index.md) · [← 이전 장](../17-security/chapter.md) · [다음 장 →](../19-async-outbox/chapter.md)
