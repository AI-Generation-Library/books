---
title: "16장. N+1·페이징·인덱스·OSIV"
description: "N+1을 쿼리 수와 데이터 크기로 측정하고 fetch join·EntityGraph·DTO·페이지·인덱스·OSIV의 대가를 비교한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 16
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: 목록 20건을 읽는데 SQL은 21번 실행된다

예약 목록을 한 번 조회한 다음 각 예약의 상품명을 접근하면서 상품 조회 20번이 추가됐다. 화면에는 한 요청만 보이지만 DB에는 여러 왕복이 발생한다. 이것이 대표적인 **N+1**이다. LAZY를 EAGER로 바꾸는 것만으로 모든 조회 경로의 N+1이 사라진다는 보장은 없다.

## 16.1 먼저 무엇을 읽을지 정한다

목록 화면이 id·상품명·수량만 필요하다면 전체 엔티티 그래프보다 DTO projection이 적합할 수 있다. 상세 화면, 수정 유스케이스, 목록은 필요한 데이터와 변경 추적 여부가 다르다. 한 저장소 메서드를 모든 화면에 재사용하기보다 읽기 목적을 명확히 한다.

진단은 응답 한 건당 SQL 수, 총 반환 행 수, 전송 데이터 크기, DB 실행 시간, 앱의 객체 생성량을 함께 본다. 쿼리 하나가 수십만 행을 가져오면 쿼리 수가 적어도 느릴 수 있다.

## 16.2 fetch join과 EntityGraph

fetch join은 조회 시 연관 데이터를 함께 가져오도록 표현한다. EntityGraph도 특정 조회의 로딩 계획을 지정하는 수단이다. 둘 다 모든 관계를 무제한으로 미리 가져오라는 뜻은 아니다. 여러 to-many 관계를 한 번에 조인하면 결과 행이 곱으로 늘 수 있다.

JPA 확장 설계 예시:

```java
@Query("select r from ReservationEntity r join fetch r.product where r.owner = :owner")
List<ReservationEntity> findWithProduct(String owner);
```

이 코드는 별도 JPA 모듈용 부분 코드다. 통합 JDBC 예제의 Reservation record와는 다른 엔티티 이름을 사용했다. 실제 테이블·인덱스·쿼리 계획은 매핑을 완성한 환경에서 검증한다.

## 16.3 컬렉션 fetch join과 페이지 문제

부모 20개를 원하는데 SQL JOIN 결과는 자식 수에 따라 수백 행이 된다. 그 결과 행에 LIMIT을 걸면 부모 수와 기대가 어긋날 수 있어 ORM이 메모리에서 페이지를 처리하거나 경고·예외를 낼 수 있다. 설정과 버전에 따라 결과가 달라지므로 로그를 확인한다.

대안은 부모 ID만 안정적인 순서로 페이지 조회한 뒤 필요한 상세 데이터를 두 번째 쿼리로 가져오는 방법, batch fetching, 읽기 전용 DTO 쿼리다. 두 쿼리 사이 데이터 변경의 허용 범위도 문서화한다. “쿼리는 무조건 한 번”을 목표로 삼지 않는다.

## 16.4 offset과 keyset

offset 방식은 이해하기 쉽지만 깊은 페이지에서 앞의 많은 행을 건너뛰는 비용이 커질 수 있다. keyset은 마지막으로 본 정렬 키를 기준으로 다음 구간을 조회한다.

```sql
SELECT id, created_at, quantity
FROM reservation_history
WHERE owner_name = :owner
  AND (created_at, id) < (:last_created_at, :last_id)
ORDER BY created_at DESC, id DESC
LIMIT :page_size;
```

이는 PostgreSQL 확장 예시이며 통합 예제에 reservation_history 테이블은 없다. 동률을 깨는 고유 id와 정렬에 맞는 인덱스가 필요하다. 임의 페이지로 점프해야 하는 화면에는 keyset이 불편할 수 있다. 페이지 크기는 서버에서 제한하고 커서 값을 검증한다.

## 16.5 인덱스와 실행 계획

복합 인덱스는 WHERE 조건과 ORDER BY, 데이터 분포를 함께 보고 설계한다. `(owner_name, created_at, id)` 후보가 있어도 실제 필터 선택도·정렬 방향·DB 최적화에 따라 계획을 확인해야 한다. 인덱스는 저장 공간과 쓰기 비용을 늘린다.

`EXPLAIN ANALYZE`는 쿼리를 실제 실행한다. 변경 SQL에 사용하면 데이터가 바뀔 수 있으며, 큰 조회도 운영 부하를 만들 수 있다. 복제된 실험 데이터나 통제된 환경에서 예상 행 수와 실제 행 수, 반복 루프, 정렬·버퍼 사용을 읽는다.

## 16.6 OSIV의 편의와 비용

**OSIV — Open Session/EntityManager in View**는 웹 요청 처리 동안 영속성 문맥을 열어 두어 응답 생성 중 지연 로딩을 가능하게 하는 구성이다. 서비스 트랜잭션이 끝났어도 직렬화 단계에서 SQL이 실행될 수 있다. 모든 쿼리가 같은 서비스 트랜잭션의 일관된 스냅샷이라는 기대가 깨질 수 있다.

JPA 서비스에서 `spring.jpa.open-in-view=false`를 선택하면 서비스 안에서 필요한 데이터를 DTO로 준비하는 경계를 만들기 쉽다. 대신 기존 응답 경로의 지연 로딩 의존을 찾아 수정해야 한다. 통합 예제는 JDBC이므로 이 속성을 넣어도 해당 문제를 테스트한 것이 아니다.

## 실습: 쿼리 예산을 정의한다

별도 JPA 목록 실습에서 1건·20건·100건 데이터를 만들고 SQL 수가 어떻게 늘어나는지 기록한다. 정상 목표를 “무조건 1회” 대신 “페이지당 최대 쿼리 수와 반환 행 수가 예측 가능함”으로 정한다. OSIV를 끈 뒤 서비스 반환 후 직렬화까지 수행해 숨은 조회를 찾는다.

## 확인 문제와 해설

**Q1. LAZY면 성능이 항상 좋은가?** 접근 패턴에 따라 왕복이 늘 수 있다. 필요한 시점과 조회 수를 측정한다.

**Q2. Page와 Slice가 같은 비용인가?** Page는 전체 개수를 위한 count가 필요할 수 있고 Slice는 다음 구간 여부 중심으로 설계할 수 있다.

**Q3. 인덱스를 모든 컬럼에 만들면 빨라지는가?** 쓰기·메모리·저장 비용이 커지고 원하는 복합 접근을 보장하지 않는다.

## 참고자료

- [Spring Data 쿼리 메서드](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)
- [Hibernate fetching](https://docs.hibernate.org/orm/current/userguide/html_single/Hibernate_User_Guide.html#fetching)
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html)

---

[전체 목차](../index.md) · [← 이전 장](../15-isolation-locking/chapter.md) · [다음 장 →](../17-security/chapter.md)
