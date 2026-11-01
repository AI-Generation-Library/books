---
title: "10장. JDBC·커넥션 풀·스키마 변경"
description: "JDBC·DataSource·Connection·JdbcTemplate의 역할, 풀 고갈, SQL 파라미터 바인딩과 스키마 변경 전략을 설명한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 10
part: 2
enableToc: true
---

> PART 2. HTTP API와 데이터 접근

## 도입: CPU는 한가한데 API가 3초씩 멈춘다

DB 커넥션 풀은 8개인데 요청 스레드는 수십 개다. 일부 요청이 연결을 오래 점유하면 나머지는 연결을 빌리려고 기다린다. CPU 사용률이 낮아도 사용자는 타임아웃을 경험한다. 풀의 대기 시간과 SQL 실행 시간을 나눠 측정해야 원인을 알 수 있다.

## 10.1 JDBC의 네 객체

**JDBC — Java Database Connectivity**는 Java에서 DB를 사용하기 위한 API다. DataSource는 연결 공급, Connection은 작업에 사용할 연결과 트랜잭션 상태, PreparedStatement는 매개변수를 바인딩한 SQL, ResultSet은 조회 결과를 나타낸다. 드라이버가 DB 프로토콜과의 연결을 담당한다.

JdbcTemplate은 반복되는 연결·문장·결과 처리와 예외 변환을 줄인다. Spring 트랜잭션에 참여할 때는 그 문맥에 연결된 자원을 사용한다. 템플릿을 사용한다는 이유로 SQL 최적화와 트랜잭션 경계가 자동 해결되는 것은 아니다.

```java
int changed = jdbc.update(
    "UPDATE inventory SET available=available-? WHERE sku=? AND available>=?",
    quantity, sku, quantity
);
if (changed != 1) throw new BusinessException("OUT_OF_STOCK");
```

물음표에는 값이 바인딩된다. 사용자 입력을 문자열로 이어 붙여 SQL을 만들지 않는다. 테이블·컬럼 이름이나 정렬 방향은 일반 값 파라미터로 대체할 수 없으므로 허용 목록에서 선택한다. 예제 테스트의 테이블 이름 연결은 테스트 내부의 고정 상수 호출만 사용하며 사용자 입력 경로가 아니다.

## 10.2 커넥션 풀은 비용이 큰 자원을 제한한다

HikariCP 같은 풀은 연결을 재사용한다. `maximum-pool-size`는 동시에 빌릴 수 있는 연결 한도, `connection-timeout`은 연결을 얻기 위해 기다리는 한도다. 이 값은 SQL 실행 타임아웃과 다르다. 이미 얻은 연결에서 실행 중인 쿼리를 반드시 그 시간 안에 중단한다는 뜻이 아니다.

애플리케이션 복제본 10개가 각각 풀 20개를 가지면 최대 200개의 연결이 필요하다. DB의 전체 연결 한도에서 관리·마이그레이션·다른 서비스 몫을 빼야 한다. 풀 크기를 늘리는 대신 느린 쿼리와 긴 트랜잭션을 줄여야 해결되는 문제가 많다.

## 10.3 트랜잭션이 연결 수명을 바꾼다

서비스 트랜잭션 안의 여러 JdbcTemplate 호출은 같은 트랜잭션 자원에 참여하도록 연결된다. 메서드가 끝날 때까지 외부 HTTP 응답을 기다리면 DB 작업은 끝났어도 연결과 잠금이 오래 유지될 수 있다. 타임라인에 “연결 획득 → SQL → 외부 대기 → commit → 반환”을 그려 본다.

다른 스레드에서 직접 DataSource로 연결을 가져오거나 Spring 관리 밖에서 별도 연결을 생성하면 같은 메서드 안에 있어도 같은 트랜잭션이라고 보장할 수 없다. DB URL이 같다는 사실과 트랜잭션 자원이 같다는 사실은 다르다.

## 10.4 스키마가 마지막 방어선이다

예제의 reservations는 `(owner_name, request_key)` UNIQUE로 사용자별 중복 키를 제한한다. inventory는 `available >= 0`, quantity는 1~100 CHECK로 범위를 제한한다. FK는 존재하지 않는 SKU와 예약을 참조하지 못하게 한다. 이름만 있는 제약보다 어떤 불변식을 지키는지 적는다.

Schema 변경은 Flyway·Liquibase 같은 버전 관리 도구를 활용할 수 있다. 운영에서 Hibernate `ddl-auto=update`에 모든 변경을 맡기는 대신 변경 이력, 잠금 영향, 데이터 이행, 재실행 가능성, 배포 순서를 검토한다. 통합 예제의 schema.sql/data.sql은 폐기 가능한 H2 실습용 초기화다.

## 10.5 호환 가능한 변경 순서

컬럼 이름을 즉시 바꾸면 롤링 배포 중 이전 앱이 깨질 수 있다. 새 컬럼 추가 → 양쪽 버전이 호환되는 읽기·쓰기 → 기존 데이터 이행 → 새 컬럼으로 전환 → 이전 버전 제거 후 구 컬럼 삭제처럼 **expand–contract** 단계를 고려한다. 대규모 backfill은 작은 배치와 진행 기록을 두고 장시간 잠금을 피한다.

DDL도 DB마다 트랜잭션·잠금·온라인 변경 지원이 다르다. 작은 H2 스키마 성공으로 운영 PostgreSQL 변경 시간을 예측하지 않는다.

## 실습: 풀 대기와 업무 실패를 나눈다

동시 주문 테스트를 실행하고 성공 5건, 실패 7건, 최종 재고 0을 확인한다. 여기서 품절은 정상적인 업무 거절이다. 풀 획득 타임아웃이 나왔다면 테스트의 원래 예상 결과와 다른 인프라 실패이므로 품절로 집계하면 안 된다.

확장 실습에서는 테스트 전용 별도 DB를 사용하고 풀을 1로 줄인 뒤 트랜잭션 안에 대기를 삽입한다. 다른 요청이 연결을 얻기까지 걸리는 시간을 측정한다. 이 변형을 제품 코드에 남기지 않는다.

## 확인 문제와 해설

**Q1. 풀 8개면 요청도 8개까지만 받아야 하는가?** 요청 처리에는 DB를 쓰지 않는 구간도 있으므로 동일 수는 아니지만 DB 대기열과 지연 목표를 함께 제한해야 한다.

**Q2. connection-timeout을 올리면 DB가 빨라지는가?** 더 오래 기다릴 뿐 처리량이 늘지 않을 수 있다.

**Q3. 서비스의 중복 조회 검사와 UNIQUE를 함께 쓰는 이유는?** 전자는 친절한 제어 흐름, 후자는 동시 실행에서도 지켜지는 최종 제약이다.

## 참고자료

- [JdbcTemplate](https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html)
- [HikariCP 설정](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)
- [DB 초기화](https://docs.spring.io/spring-boot/how-to/data-initialization.html)

---

[전체 목차](../index.md) · [← 이전 장](../09-configuration-architecture/chapter.md) · [다음 장 →](../11-jpa-persistence/chapter.md)
