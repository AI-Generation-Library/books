---
title: "17장. Spring Security·인증·인가"
description: "SecurityFilterChain·인증·인가·PasswordEncoder·CSRF·CORS·JWT를 구분하고 역할 검사와 객체 소유권을 검증한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 17
part: 4
enableToc: true
---

> PART 4. 보안과 외부 시스템

## 도입: 로그인했지만 다른 사람의 주문을 읽을 수 있다

인증은 “누구인가”, 인가는 “이 동작을 할 수 있는가”를 판단한다. `/api/**`에 authenticated만 설정하면 로그인한 사용자가 다른 사용자의 예약 ID를 추측해 읽는 문제는 남는다. 경로 수준 권한과 객체 수준 권한을 함께 다룬다.

## 17.1 SecurityFilterChain의 위치

Servlet 요청은 Spring Security의 FilterChainProxy를 거쳐 일치하는 SecurityFilterChain의 필터들로 처리된다. 인증 정보 추출, 인증 수행, SecurityContext 관리, CSRF 검사, 인가 등이 이 경계에 있다. 여러 체인이 있다면 matcher와 순서에 따라 선택되는 체인을 확인한다.

**Authentication**은 인증 주체·자격 증명·권한 등을 나타내는 객체다. **GrantedAuthority**는 부여된 권한을 표현한다. **SecurityContext**는 현재 보안 문맥을 담는다. 일반 Servlet 실행에서 스레드와 연계되더라도 임의의 비동기 스레드나 큐 작업에 자동·영속적으로 전달된다고 가정하지 않는다.

## 17.2 예제의 인증 범위

통합 프로젝트는 학습을 위해 `buyer`, `reader` 두 메모리 계정을 제공한다. 비밀번호는 `APP_DEMO_PASSWORD`에서 받고 PasswordEncoder로 해시해 저장한다. HTTP Basic은 사용자명·비밀번호를 요청에 포함하는 방식이며 Base64는 암호화가 아니다. 예제는 루프백에서만 실행하고 실제 원격 서비스에서는 TLS와 계정 관리 체계를 갖춘다.

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/actuator/health").permitAll()
    .requestMatchers(HttpMethod.POST, "/api/reservations").hasRole("BUYER")
    .anyRequest().authenticated())
    .httpBasic(Customizer.withDefaults())
    .csrf(Customizer.withDefaults());
```

전체 구성은 [SecurityConfig.java](../examples/reservation-api/src/main/java/com/example/reservation/SecurityConfig.java)다. `hasRole("BUYER")`는 기본 role 접두사 정책에서 `ROLE_BUYER` 권한과 연결된다. 임의 scope 문자열과 역할 이름을 혼용하지 않는다.

## 17.3 객체 소유권은 쿼리와 서비스에서

예약 조회는 `WHERE owner_name=? AND id=?`로 현재 인증 사용자와 ID를 함께 사용한다. reader가 buyer의 예약 ID를 알아도 결과를 받지 못한다. 응답을 404로 정하면 객체의 존재를 감추는 데 도움이 될 수 있지만 실제 접근 조건을 생략할 수는 없다.

서비스 메서드 수준 인가는 `@EnableMethodSecurity`와 `@PreAuthorize` 등으로 확장할 수 있다. Security Starter만 추가했다고 메서드 인가가 자동 활성화된다고 보지 않는다. 또한 프록시 자기 호출 제약을 고려한다. 통합 예제는 HTTP 역할 검사와 서비스의 소유자 조건을 사용하며 메서드 어노테이션 기반 인가는 확장 과제다.

## 17.4 CSRF와 CORS는 서로 다른 문제다

**CSRF — Cross-Site Request Forgery**는 브라우저가 자동으로 보내는 자격 증명을 악용한 요청 위조 문제다. 세션 쿠키를 쓰거나 브라우저가 Basic 자격 증명을 자동 전송하는 환경에서는 위험을 검토해야 한다. REST라는 이름이나 세션 정책만으로 CSRF를 무조건 끄지 않는다.

예제는 GET `/csrf`로 받은 토큰과 같은 세션 쿠키를 POST에 보낸다. 토큰 문자열만 복사하고 JSESSIONID를 잃으면 검증에 실패할 수 있다. 이 구성에서 Basic 헤더만 있고 토큰이 없는 POST는 인증 필터 이전의 CSRF 거절로 401이 발생한다. reader가 올바른 토큰을 보내도 역할 인가에서 403이다. 필터 순서와 인증 완료 여부를 함께 본다.

**CORS — Cross-Origin Resource Sharing**는 브라우저의 다른 출처 요청·응답 접근 정책이다. CORS 허용은 사용자 인증이나 객체 권한이 아니다. 허용 Origin·메서드·헤더·credentials 조합을 제한하고, preflight가 인증 쿠키 없이 올 수 있다는 점을 고려한다. 서버 간 HTTP 클라이언트는 브라우저 CORS 제한을 동일하게 적용하지 않는다.

## 17.5 JWT를 사용할 때 검증할 것

**JWT — JSON Web Token**의 payload를 decode하는 것만으로 신뢰할 수 없다. Resource Server는 서명과 허용 알고리즘, 발급자 issuer, 만료·유효 시각, 서비스 목적에 맞는 audience 등을 검증하도록 구성해야 한다. `issuer-uri`만 넣었다고 모든 업무용 audience 정책이 자동 완성된다고 가정하지 않는다.

JWT의 서명은 암호화가 아니다. payload에 비밀번호나 민감한 개인정보를 넣지 않는다. 탈취 대응을 위해 짧은 수명, 키 회전, 필요한 취소·재인증 정책을 정한다. 인증 서버와 리소스 서버를 구분하고 직접 암호 프로토콜을 구현하기보다 검증된 지원 모듈을 쓴다. 이 책의 통합 예제는 JWT 서버를 포함하지 않는다.

## 실습: 허용과 거절을 함께 테스트한다

HTTP 테스트는 공개 health 200, 익명 조회 401, reader 예약 403, buyer 정상 예약 200을 확인한다. 서비스 테스트 `otherOwnerCannotReadReservation`은 객체 소유권을 별도로 확인한다. 역할 검사만 통과했다고 소유권 테스트를 생략하지 않는다.

추가 연습은 잘못된 비밀번호, 토큰과 다른 세션 쿠키, 존재하지 않는 예약, 타인의 예약을 각각 요청하는 것이다. 응답 차이가 불필요한 정보 유출이나 무한 재시도를 만들지 않는지 확인한다.

## 확인 문제와 해설

**Q1. JWT를 쓴다는 이유로 CSRF를 꺼도 되는가?** 토큰이 어디에 저장되고 어떻게 자동 전송되는지 확인해야 한다. 쿠키에 담긴 토큰은 같은 문제가 남을 수 있다.

**Q2. 관리자 역할이면 모든 테넌트 데이터를 조회해도 되는가?** 테넌트 범위와 업무 권한은 별도로 정의해야 한다.

**Q3. 비밀번호를 암호화해서 원문으로 복호화하는가?** 일반 로그인 검증은 적절한 단방향 비밀번호 해시와 비교를 사용한다.

## 참고자료

- [Security 구조](https://docs.spring.io/spring-security/reference/servlet/architecture.html)
- [CSRF](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html)
- [CORS](https://docs.spring.io/spring-security/reference/servlet/integrations/cors.html)
- [JWT Resource Server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)
- [메서드 보안](https://docs.spring.io/spring-security/reference/servlet/authorization/method-security.html)

---

[전체 목차](../index.md) · [← 이전 장](../16-query-performance/chapter.md) · [다음 장 →](../18-http-resilience/chapter.md)
