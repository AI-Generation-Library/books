---
title: "07장. Tomcat·Servlet·DispatcherServlet"
description: "HTTP 바이트가 Java 메서드 호출과 JSON 응답이 되는 경로를 추적하고 Filter·Interceptor·AOP와 ASGI를 비교한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 7
part: 2
enableToc: true
---

> PART 2. HTTP API와 데이터 접근

## 도입: 컨트롤러 로그도 없이 403이 반환된다

컨트롤러 첫 줄에 로그를 넣었는데 요청은 403으로 끝나고 로그가 없다. 컨트롤러 내부의 예외 처리만 확인해서는 답을 찾을 수 없다. 요청이 그 앞의 Security Filter에서 거절됐을 수 있기 때문이다. 이 장의 목표는 요청이 어디까지 도달했는지를 계층별로 확인하는 것이다.

## 7.1 Servlet은 서버와 애플리케이션 사이의 계약이다

Servlet은 Java 웹 요청·응답 처리 규약이다. Tomcat 같은 Servlet 컨테이너가 네트워크 연결과 HTTP 파싱을 담당하고 `HttpServletRequest`, `HttpServletResponse`를 제공한다. **DispatcherServlet**은 Spring MVC의 중앙 진입점, 즉 Front Controller다. 경로마다 Servlet을 하나씩 만드는 대신 여기서 적절한 핸들러를 찾는다.

```text
TCP 연결 / HTTP 요청
 → Tomcat
 → Servlet Filter 체인 (Spring Security 포함)
 → DispatcherServlet
 → HandlerMapping: 어느 핸들러인가?
 → HandlerAdapter: 그 핸들러를 어떻게 호출하는가?
 → ArgumentResolver / HttpMessageConverter / 입력 검증
 → Controller → Service → Repository
 → 반환값 처리 / HttpMessageConverter
 → 응답 상태·헤더·본문 전송
```

HandlerMapping과 HandlerAdapter를 구분하는 이유는 “경로 선택”과 “실제 호출 방법”이 다른 책임이기 때문이다. 어노테이션 컨트롤러의 JSON 요청 본문은 메시지 변환기가 Java 객체로 만들고, 검증 조건을 통과한 뒤 메서드에 들어간다. 출력 객체도 메시지 변환기를 거쳐 직렬화된다. 반환값이 자동으로 DB 행이나 HTTP 본문과 동일한 것은 아니다.

## 7.2 @RestController와 HTTP 계약

`@RestController`는 컨트롤러의 반환값을 응답 본문으로 처리하는 관례를 제공한다. 반환할 Java 객체를 선정한 뒤 상태 코드·헤더·본문을 별도로 설계한다. 생성된 리소스를 알리는 POST라면 보통 201과 Location을 고려하고, 이미 정한 명령 결과를 반환하는 API라면 200을 계약으로 선택할 수도 있다.

통합 예제는 예약 명령의 최초 실행과 같은 키 재조회를 모두 200으로 정의한다. “POST는 항상 201”이나 “POST는 멱등하게 만들 수 없다” 같은 암기는 피한다. HTTP 메서드의 표준 의미와 애플리케이션이 추가한 멱등성 계약을 함께 문서화한다.

## 7.3 Filter·Interceptor·AOP의 범위

| 도구 | 보는 경계 | 적합한 사례 | 놓치기 쉬운 점 |
| --- | --- | --- | --- |
| Filter | Servlet 요청·응답 | 보안 체인, 요청 래핑 | MVC 이전에 종료 가능 |
| Interceptor | 선택된 MVC 핸들러 | 핸들러별 메타데이터 관측 | 모든 보안 정책의 대체 수단 아님 |
| AOP | Spring 빈 메서드 | 트랜잭션, 서비스 관측 | 프록시를 지나야 함 |

Filter에서 거절된 예외는 컨트롤러의 `@ExceptionHandler`에 도달하지 않을 수 있다. Security의 401·403 응답 형식을 통일하려면 `AuthenticationEntryPoint`와 `AccessDeniedHandler` 같은 해당 경계의 확장점을 사용한다. 통합 예제는 Security의 기본 오류 응답과 MVC의 ProblemDetail을 구분한다.

## 7.4 스레드·연결·요청은 다른 수명이다

동기 MVC 요청은 일반적으로 처리 중인 스레드가 컨트롤러와 JDBC 호출을 이어 수행한다. JDBC가 응답을 기다리는 동안 그 실행 흐름도 대기한다. HTTP keep-alive 연결 하나가 여러 요청을 전달할 수 있으므로 연결 수와 요청 수를 같게 보면 안 된다.

Servlet 비동기 처리도 존재한다. 따라서 Servlet은 언제나 요청 하나가 시작부터 끝까지 동일한 플랫폼 스레드에 고정된다고 단정하지 않는다. 비동기 디스패치에서는 필터 재실행 정책, 요청 문맥, 로깅 MDC 정리가 중요해진다. 긴 스트리밍의 자원 수명은 일반 JSON 반환과도 다르다.

## 7.5 FastAPI의 ASGI와 비교

FastAPI 책에서 다룬 정확한 약어는 **ASGI — Asynchronous Server Gateway Interface**다. ASGI는 `scope`, `receive`, `send`로 서버와 앱의 메시지를 연결한다. Servlet은 Java 요청·응답 객체와 컨테이너의 실행 규약을 제공한다. 둘은 웹 서버와 애플리케이션 경계를 이해하는 비교 지점이지만 동일한 인터페이스는 아니다.

Uvicorn을 Tomcat, FastAPI 라우팅을 MVC 핸들러 선택에 대략 대응시킬 수 있지만 동시성·취소·스트리밍 의미까지 같아지지는 않는다. 특히 FastAPI의 `async def` 경험만으로 Java 서비스의 JDBC 호출이 비차단이라고 가정하지 않는다.

## 실습: 401·403·400·200을 구분한다

`mvn -Dtest=HttpTests test`는 실제 임의 포트의 내장 서버에 JDK HTTP 클라이언트로 요청한다. 인증 없는 GET은 401, reader 역할의 정상 토큰 POST는 403, buyer의 올바른 인증·토큰에 잘못된 수량을 보낸 POST는 400, 정상 요청은 200을 기대한다. 이 구성에서 토큰 없이 Basic 헤더만 보낸 POST는 CSRF 필터가 Basic 인증보다 먼저 거절하므로 401이다. 자격 증명을 보냈다는 사실과 인증이 완료됐다는 사실은 다르다.

각 테스트에 대해 “어디에서 종료되는가”를 적는다. 첫 두 경우는 보안 경계, 입력 검증 오류는 MVC 호출 준비 단계, 성공은 서비스와 DB를 통과한다. 모든 상태 코드를 컨트롤러가 직접 만든다고 설명하면 이 차이를 놓친다.

## 확인 문제와 해설

**Q1. ControllerAdvice로 모든 403을 바꿀 수 있는가?** 보안 필터에서 끝난 요청은 별도 오류 처리 경계가 필요하다.

**Q2. 컨트롤러가 DTO를 반환하면 응답 전송까지 끝난 것인가?** 직렬화와 실제 전송이 남아 있을 수 있다. 스트리밍에서는 차이가 더 크다.

**Q3. 연결 100개면 동시에 SQL 100개인가?** 요청·스레드·DB 커넥션은 별도 자원이며 풀과 대기 상태에 따라 다르다.

## 참고자료

- [DispatcherServlet](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-servlet.html)
- [MVC Interceptor](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-config/interceptors.html)
- [Jakarta Servlet](https://jakarta.ee/specifications/servlet/6.1/)

---

[전체 목차](../index.md) · [← 이전 장](../06-psa-auto-configuration/chapter.md) · [다음 장 →](../08-validation-errors/chapter.md)
