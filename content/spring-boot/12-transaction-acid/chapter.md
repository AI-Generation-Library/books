---
title: "12장. ACID와 서비스 트랜잭션 경계"
description: "ACID 각각의 보장과 한계를 구분하고 예약·재고·Outbox를 하나의 서비스 트랜잭션으로 묶는 이유를 설명한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 12
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: 예약은 있는데 재고가 줄지 않았다

예약 INSERT는 성공했지만 재고 UPDATE가 실패했다. 둘이 서로 다른 트랜잭션이면 예약만 남는다. 반대로 재고를 먼저 줄인 뒤 예약 저장이 실패하면 고객은 주문을 찾지 못하는데 상품은 판매 불가능해진다. 이 두 변경을 어떤 성공 단위로 묶을지가 트랜잭션 설계다.

## 12.1 ACID를 예약 서비스의 문장으로 번역한다

**Atomicity, 원자성:** 한 트랜잭션에 참여한 변경은 함께 확정되거나 함께 취소된다. 예약·재고·Outbox가 같은 DB 트랜잭션에 들어갔다면 하나만 확정되는 상태를 막을 수 있다. 이미 보낸 이메일이나 다른 HTTP 서버의 결제는 이 범위에 자동 포함되지 않는다.

**Consistency, 일관성:** 트랜잭션 전후에 정의된 데이터 규칙을 만족해야 한다. DB는 CHECK·UNIQUE·FK를 강제할 수 있지만 “유효한 쿠폰만 사용한다” 같은 규칙을 스스로 알아내지는 못한다. 애플리케이션과 제약 설계가 규칙을 표현해야 한다. 분산 복제의 일관성 모델과 같은 단어를 쓰지만 논의 범위가 다르다.

**Isolation, 격리성:** 동시에 실행되는 트랜잭션이 서로의 중간 상태와 결과를 어떤 규칙으로 관찰하는지 정한다. 모든 격리 수준이 완전 직렬 실행과 같지는 않다. 격리 수준과 잠금·조건부 갱신을 조합한다.

**Durability, 지속성:** 성공적으로 commit된 변경을 장애 뒤에도 유지하도록 DB가 보장하는 성질이다. 실제 보장 범위는 로그 동기화·복제·스토리지 설정과 장애 모델에 의존한다. 메모리 H2 예제는 프로세스 재시작 후 데이터 보존 실험이 아니다.

## 12.2 서비스가 업무 경계를 가진다

```java
@Transactional
public Reservation reserve(String owner, ReserveRequest request) {
    // 입력·멱등 키 검사 생략: 실제 코드는 전체 파일 참조
    Reservation value = /* 예약 객체 생성 */;
    repository.insert(value);
    if (!repository.decrease(value.sku(), value.quantity())) {
        throw new BusinessException("OUT_OF_STOCK");
    }
    repository.appendEvent(value.id());
    return value;
}
```

위는 흐름을 드러낸 의사 코드다. 복사해 실행할 전체 코드는 [ReservationService](../examples/reservation-api/src/main/java/com/example/reservation/ReservationService.java)에 있다. INSERT·UPDATE·Outbox INSERT의 순서가 같아도 각각 독립 commit이면 원자성이 없다. 저장소 메서드 세 개에 각각 어노테이션을 붙이는 것보다 바깥 유스케이스 경계가 중요하다.

## 12.3 선언형 트랜잭션의 실행 순서

1. 호출자가 Spring에서 받은 서비스 프록시를 호출한다.
2. 인터셉터가 전파·격리·롤백 메타데이터를 읽는다.
3. 트랜잭션 매니저가 새 트랜잭션을 만들거나 기존 것에 참여한다.
4. Repository의 JDBC 작업이 관리된 자원을 사용한다.
5. 메서드 반환 또는 전파된 예외를 기준으로 종료를 결정한다.
6. commit 또는 rollback을 마친 뒤 호출자에게 결과가 전달된다.

Connection을 직접 만들거나 다른 매니저의 데이터소스를 쓰면 4번의 전제가 깨질 수 있다. 메서드 몸체의 중괄호 안에 있다는 이유만으로 모든 작업이 한 트랜잭션에 포함되는 것은 아니다.

## 12.4 프로그램 방식이 더 명확한 경우

외부 조회를 먼저 하고 짧은 DB 변경만 묶어야 한다면 `TransactionTemplate`을 사용할 수 있다. 다음은 구조 예시다.

```java
Quote quote = remoteClient.fetchQuote(command); // DB 트랜잭션 바깥
Reservation saved = transactionTemplate.execute(status -> {
    return persistReservation(command, quote);
});
```

외부에서 받은 가격이 이후 바뀌는 문제까지 해결되지는 않는다. 견적 ID·유효기간·버전 같은 검증 조건을 저장하고 실제 예약 시점의 정책을 정의해야 한다. 짧은 트랜잭션과 업무 일관성은 함께 설계한다.

## 12.5 readOnly·timeout을 과신하지 않는다

`readOnly=true`는 트랜잭션 인프라와 드라이버·ORM에 전달하는 최적화·의도 신호다. 모든 환경에서 쓰기를 강제로 차단하는 권한 장치가 아니다. 쓰기 금지가 필수라면 DB 권한·연결 분리·테스트를 함께 사용한다.

트랜잭션 timeout도 Java 코드의 모든 무한 루프나 외부 HTTP 호출을 정확히 그 시각에 멈추는 만능 타이머가 아니다. 드라이버·쿼리·클라이언트별 적용 범위를 확인한다. API 전체 deadline, 연결 획득, 쿼리, 외부 호출의 시간 예산을 따로 설계한다.

## 12.6 응답이 사라지면 commit도 취소되는가

DB commit이 끝난 직후 네트워크가 끊기면 서버는 성공했지만 클라이언트는 실패로 인식할 수 있다. 클라이언트의 타임아웃은 서버의 rollback 증거가 아니다. 예약 요청에 멱등 키를 두고 동일 키·동일 본문으로 결과를 재조회할 수 있어야 한다.

이는 ACID가 부족하다는 뜻이 아니라 DB 트랜잭션과 네트워크 응답이 다른 경계라는 뜻이다. 성공 확정과 성공 전달을 같은 사건으로 취급하지 않는다.

## 실습: 품절 직전에 이미 INSERT가 있었다

`shortageRollsBackInsertedReservation` 테스트는 재고 5에서 수량 6을 요청한다. 서비스는 예약 INSERT 뒤 재고 감소에 실패하고 RuntimeException 계열의 업무 예외를 던진다. 최종 기대값은 예약 0행, Outbox 0행, 재고 5다.

반면 `commitsReservationStockAndEvent`는 수량 2를 요청하며 예약 1행·Outbox 1행·재고 3을 확인한다. 테스트 메서드는 자동 롤백으로 결과를 감추지 않고 실제 서비스 경계가 끝난 후 DB를 읽는다.

## 확인 문제와 해설

**Q1. 이메일 발송 후 DB에서 예외가 나면 이메일도 취소되는가?** 로컬 DB 트랜잭션이 외부 발송을 되돌리지는 않는다. Outbox나 보상 절차를 설계한다.

**Q2. Repository 메서드가 모두 각각 원자적이면 예약 전체도 원자적인가?** 여러 독립 트랜잭션의 성공을 하나의 원자적 단위로 합칠 수 없다.

**Q3. 재고 5를 읽은 뒤 1을 빼면 격리가 충분한가?** 두 요청이 같은 값을 읽을 수 있으므로 조건부 갱신·락·버전 검사 등의 동시성 설계가 필요하다.

## 참고자료

- [트랜잭션 추상화](https://docs.spring.io/spring-framework/reference/data-access/transaction/strategies.html)
- [프로그램 방식 트랜잭션](https://docs.spring.io/spring-framework/reference/data-access/transaction/programmatic.html)
- [PostgreSQL 트랜잭션 입문](https://www.postgresql.org/docs/18/tutorial-transactions.html)

---

[전체 목차](../index.md) · [← 이전 장](../11-jpa-persistence/chapter.md) · [다음 장 →](../13-transaction-rollback/chapter.md)
