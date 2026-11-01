---
title: "08장. DTO·검증·HTTP 오류 계약"
description: "DTO와 엔티티를 분리하고 Bean Validation·도메인 제약·DB 제약을 배치하며 ProblemDetail과 상태 코드를 설계한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 8
part: 2
enableToc: true
---

> PART 2. HTTP API와 데이터 접근

## 도입: 수량 -3을 보내니 재고가 늘었다

`available = available - quantity`에서 quantity가 음수라면 재고는 늘어난다. JSON을 Java 객체로 변환할 수 있다는 사실은 입력이 유효하다는 뜻이 아니다. 형식 검증, 업무 규칙, DB 무결성을 나눠 배치해야 한다.

## 8.1 DTO의 역할

**DTO — Data Transfer Object**는 경계를 넘는 데이터를 표현한다. HTTP DTO와 JPA 엔티티를 같은 클래스로 사용하면 DB 관계·내부 필드·지연 로딩이 API 계약에 노출되기 쉽다. 요청 DTO는 클라이언트가 바꿀 수 있는 값만, 응답 DTO는 공개할 값만 갖도록 설계한다.

예약 요청에서 owner는 본문에 받지 않는다. 인증된 Principal에서 가져온다. 클라이언트가 `owner=admin`을 보낼 수 있는 구조라면 타입 검증이 성공해도 권한 문제가 남는다. 가격·할인율·확정 상태도 어떤 값이 서버의 권한인지 구분한다.

## 8.2 Bean Validation을 정확히 읽기

```java
public record ReserveRequest(
    @NotBlank @Size(max = 80)
    @Pattern(regexp = "[A-Za-z0-9-]+") String requestKey,
    @NotBlank @Size(max = 40) String sku,
    @Min(1) @Max(100) int quantity
) {}
```

전체 코드는 [ReserveRequest.java](../examples/reservation-api/src/main/java/com/example/reservation/ReserveRequest.java)에 있다. `@NotNull`은 null만, `@NotBlank`는 문자열의 공백 여부까지 검사한다. Size와 범위 조건은 목적이 다르다. 중첩 객체의 제약은 `@Valid`를 통해 탐색하도록 연결해야 한다.

컨트롤러 인자에 `@Valid @RequestBody`를 붙이면 변환된 요청 객체를 검증한다. 서비스 메서드 인자에 어노테이션만 적는다고 모든 직접 Java 호출에 자동 적용되는 것은 아니다. 메서드 검증 인프라와 프록시가 필요할 수 있다. 통합 예제는 HTTP 외 호출에도 중요한 규칙을 보장하도록 서비스에 수량·키 검사를 둔다.

## 8.3 검증을 세 층으로 나누기

| 위치 | 예 | 실패 시 의미 |
| --- | --- | --- |
| HTTP 경계 | 문자열 길이, JSON 문법, 수량 범위 | 요청 형식이 잘못됨 |
| 도메인/서비스 | 품절, 동일 키의 본문 변경, 상태 전이 | 현재 업무 상태와 충돌 |
| DB | UNIQUE, FK, CHECK | 동시 요청 포함 최종 무결성 위반 |

“먼저 조회해서 없으면 insert”는 동시에 두 요청이 들어오면 둘 다 없다고 읽을 수 있다. 따라서 중복 방지는 서비스 조회만으로 완성되지 않고 DB UNIQUE 제약이 필요하다. 입력 검증은 DB 제약을 대체하지 않는다.

## 8.4 ProblemDetail로 오류 계약 만들기

**Problem Details**는 HTTP 오류의 공통 표현이다. Spring의 `ProblemDetail`에는 status·title·detail 등과 추가 속성을 담을 수 있다. 내부 오류 클래스 이름과 SQL 메시지를 그대로 반환하기보다 안정적인 업무 코드와 사용자 행동을 제공한다.

```json
{
  "title": "Conflict",
  "status": 409,
  "detail": "요청 조건을 확인하세요.",
  "code": "OUT_OF_STOCK"
}
```

이는 핵심 필드 예시이며 실제 응답에는 instance 등 필드가 추가될 수 있다. 클라이언트는 변경 가능한 한국어 detail을 파싱하지 않고 `code`를 사용한다. 서버 로그에는 원인과 추적 정보를 남기되 인증 헤더·비밀번호·전체 개인정보 본문을 기록하지 않는다.

통합 예제의 `ApiErrors`는 잘못된 JSON과 DTO 검증을 400, 조회 불가를 404, 품절·멱등성 충돌을 409로 변환한다. 예상치 못한 인프라 장애를 무조건 409로 숨기지 않는다. 알려진 `DuplicateKeyException`만 특정 중복 처리로 매핑하며, 외래키 오류까지 모두 “중복”이라고 해석하지 않는다.

## 8.5 오류 응답은 트랜잭션 종료 뒤에

Service에서 예외가 밖으로 나가면 프록시가 롤백을 결정한 뒤 ControllerAdvice가 HTTP 응답을 만든다. 서비스 안에서 예외를 삼키고 “실패 DTO”를 반환하면 트랜잭션 입장에서는 정상 반환일 수 있다. 업무 결과를 값으로 반환하는 설계를 택한다면 롤백 여부를 별도로 명확히 정의한다.

메서드 검증에는 `MethodArgumentNotValidException` 외에도 호출 형태에 따라 다른 예외가 발생할 수 있다. 통합 예제는 자신의 DTO 요청 경로를 처리하며 모든 MVC 검증 형태를 포괄하는 범용 라이브러리라고 주장하지 않는다. [MVC 검증](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)의 분류를 확인한다.

## 실습: DB가 바뀌지 않았는지 확인한다

HTTP 테스트의 수량 0 요청은 400이어야 한다. 서비스 테스트는 HTTP를 거치지 않고 음수를 전달하며 재고가 5로 남는지 확인한다. 품절 요청은 형식상 유효하므로 400이 아니라 업무 충돌이고, 이미 insert한 예약까지 롤백되는지 확인한다.

추가 연습으로 키 길이 81, 공백 SKU, 깨진 JSON을 보내고 상태 코드와 공개 오류 필드를 비교한다. 응답에 스택 트레이스나 실제 SQL이 포함되지 않아야 한다. Security 경계의 401·403 형식은 이 장의 Advice와 별도임을 기억한다.

## 확인 문제와 해설

**Q1. Bean Validation이 통과하면 품절이 아니라고 보장할 수 있는가?** 현재 재고와 동시성은 업무·DB 경계에서 판단한다.

**Q2. 404로 소유권 부족을 숨겨도 권한 검사를 생략할 수 있는가?** 아니다. 조회 조건에 owner와 id를 함께 적용한 결과를 공개하지 않는 선택일 뿐이다.

**Q3. 모든 예외에 200과 `success=false`를 쓰면 무엇을 잃는가?** HTTP 클라이언트·캐시·모니터링이 표준 실패 신호를 활용하기 어렵고 재시도 정책도 불명확해진다.

## 참고자료

- [Spring 오류 응답](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)
- [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html)

---

[전체 목차](../index.md) · [← 이전 장](../07-servlet-mvc/chapter.md) · [다음 장 →](../09-configuration-architecture/chapter.md)
