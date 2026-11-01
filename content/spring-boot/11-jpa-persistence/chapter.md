---
title: "11장. JPA·Hibernate·영속성 컨텍스트"
description: "JPA 규약·Hibernate 구현·Spring Data 저장소를 구분하고 영속성 상태·dirty checking·flush와 commit·연관관계 소유권을 이해한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 11
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: save를 호출하지 않았는데 UPDATE가 실행된다

트랜잭션 안에서 조회한 엔티티의 값을 바꿨더니 종료할 때 UPDATE가 발생했다. 반대로 DTO의 값을 바꾸거나 트랜잭션 밖의 분리된 객체를 바꾸면 같은 결과가 나오지 않는다. JPA를 단순한 “자동 SQL 생성기”로만 보면 이 차이를 설명하기 어렵다.

이 장의 JPA 코드는 개념을 설명하는 확장 예제다. **통합 프로젝트는 트랜잭션의 SQL 경계를 명확히 보여주기 위해 JDBC를 사용한다.** JPA 예제를 실행하려면 별도 모듈에 JPA Starter·엔티티·저장소·DB 설정을 구성해야 하며 첨부 JDBC 테스트의 통과를 JPA 검증으로 해석하지 않는다.

## 11.1 세 이름을 분리한다

**JPA — Jakarta Persistence**는 Java 객체의 영속성을 다루는 규약이다. **Hibernate ORM**은 그 구현체 중 하나다. **Spring Data JPA**는 JPA 위에서 저장소 인터페이스 구현, 쿼리 메서드, 페이지 처리 등의 반복 코드를 줄인다. JPA를 쓴다고 Spring Data가 반드시 필요한 것은 아니다.

**ORM — Object-Relational Mapping**은 객체와 관계형 테이블 사이의 매핑이다. 객체의 참조와 상속이 DB의 FK·JOIN과 완전히 같지는 않다. 어느 객체 그래프를 언제 로딩하고 어떤 변경을 언제 SQL로 반영할지 이해해야 한다.

## 11.2 영속성 컨텍스트와 상태

영속성 컨텍스트는 EntityManager가 관리하는 엔티티의 작업 문맥이다. 같은 식별자의 관리 엔티티를 일관되게 다루고 변경을 추적한다. Spring의 일반적인 트랜잭션 구성에서는 작업 트랜잭션과 연계되지만 OSIV처럼 문맥의 수명을 더 길게 하는 구성도 있다.

| 상태 | 의미 | 필드 변경의 효과 |
| --- | --- | --- |
| new/transient | 아직 관리되지 않는 새 객체 | 그것만으로 SQL 실행 안 됨 |
| managed | 현재 컨텍스트에서 관리 | 변경 감지 대상이 될 수 있음 |
| detached | 과거 관리됐으나 분리됨 | 직접 변경만으로 자동 반영 안 됨 |
| removed | 삭제가 예약된 관리 객체 | flush 시 삭제 SQL 대상 |

1차 캐시는 해당 영속성 문맥의 식별자별 객체 관리이지 모든 서버에 공유되는 Redis 같은 캐시가 아니다. 다른 트랜잭션이 바꾼 DB 값과 이미 관리 중인 객체의 상태가 언제 일치하는지도 별도 문제다.

## 11.3 dirty checking과 flush

```java
@Transactional
public void rename(long id, String newName) {
    Product product = entityManager.find(Product.class, id);
    if (product == null) throw new IllegalArgumentException("missing");
    product.rename(newName);
}
```

이는 EntityManager와 Product가 구성돼 있다는 전제의 부분 코드다. 관리 엔티티의 변경을 감지해 flush 시 SQL로 동기화할 수 있다. **flush는 DB로 변경 SQL을 보내는 과정이고 commit은 트랜잭션을 확정하는 과정**이다. flush 후에도 rollback할 수 있다.

SQL은 꼭 commit 직전에만 나가지 않는다. ID 생성 전략, 명시적 flush, 쿼리와 flush mode 등에 따라 더 일찍 나갈 수 있다. `save()`를 호출한 줄과 실제 INSERT가 실행된 줄이 같다고 가정하지 않는다.

## 11.4 persist와 merge

persist는 새 엔티티를 관리 대상으로 만드는 동작이다. merge는 전달된 객체 상태를 관리 인스턴스에 복사하는 의미이며 **반환된 관리 객체**와 전달한 객체를 구분해야 한다. Spring Data의 save는 새 엔티티 판정 등에 따라 이 경로를 선택한다.

요청 JSON을 엔티티로 그대로 바인딩한 뒤 save하면 클라이언트가 보내지 않은 필드가 null로 덮이거나 내부 상태가 변경될 수 있다. 필요한 엔티티를 트랜잭션 안에서 조회하고 허용된 도메인 메서드로 수정하는 방식이 의도를 드러낸다.

## 11.5 연관관계의 주인과 cascade

양방향 관계에서는 DB FK를 실제로 변경하는 매핑의 주인을 구분한다. `mappedBy`가 있는 쪽에서 컬렉션만 변경했다고 FK까지 기대대로 바뀌는 것은 아니다. 양쪽 객체 관계를 맞추는 편의 메서드를 두고 실제 SQL을 확인한다.

cascade는 영속성 작업의 전파이고 DB FK의 ON DELETE 정책과 동일하지 않다. `CascadeType.ALL`과 orphanRemoval을 모든 관계에 붙이면 공유 엔티티를 의도치 않게 삭제할 수 있다. “부모가 자식의 생명주기를 정말 소유하는가”를 먼저 판단한다.

## 실습: SQL 시점 예상표 만들기

별도 JPA 실습 모듈에서 조회 → 이름 변경 → flush → 예외 발생을 수행한다. 예상은 UPDATE가 로그에 보이더라도 최종 DB 값은 롤백돼 원래 값이라는 것이다. 테스트 자체의 자동 롤백을 쓰지 말고 서비스 호출이 끝난 후 새 트랜잭션으로 확인한다.

두 번째 연습은 조회한 엔티티를 detach한 뒤 수정하는 것이다. 변경을 다시 연결하지 않았다면 DB가 바뀌지 않아야 한다. 예상과 다르면 OSIV·트랜잭션 경계·테스트 컨텍스트를 먼저 확인한다.

## 확인 문제와 해설

**Q1. flush 성공이면 다른 요청도 확정된 값을 보는가?** commit과 격리 조건을 함께 봐야 한다. flush 성공만으로 확정되지 않는다.

**Q2. 엔티티를 JSON으로 반환하면 어떤 비용이 숨어 있는가?** 직렬화가 연관관계를 접근하며 추가 SQL이나 지연 로딩 예외를 만들 수 있다.

**Q3. save를 여러 번 호출하면 SQL도 그 수만큼인가?** 상태·식별자 전략·flush·배치 설정에 따라 달라지므로 로그와 통계로 확인한다.

## 참고자료

- [Jakarta Persistence 규약](https://jakarta.ee/specifications/persistence/)
- [Hibernate ORM User Guide](https://docs.hibernate.org/orm/current/userguide/html_single/Hibernate_User_Guide.html)
- [Spring Data JPA 트랜잭션](https://docs.spring.io/spring-data/jpa/reference/jpa/transactions.html)

---

[전체 목차](../index.md) · [← 이전 장](../10-jdbc-pool-schema/chapter.md) · [다음 장 →](../12-transaction-acid/chapter.md)
