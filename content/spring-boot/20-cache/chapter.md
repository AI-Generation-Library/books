---
title: "20장. 캐시 일관성과 Redis 설계"
description: "Cacheable·CacheEvict·키·TTL·stampede·commit 이후 무효화·경쟁 재채움과 Redis 장애 정책을 설계한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 20
part: 4
enableToc: true
---

> PART 4. 보안과 외부 시스템

## 도입: 예약은 성공했는데 상품 화면에는 이전 재고가 보인다

DB 재고는 3인데 캐시에는 5가 남아 있다. 화면 표시의 짧은 지연을 허용할 수는 있지만 그 값으로 판매 가능 여부를 확정하면 초과 판매 위험이 있다. 캐시는 데이터를 빨리 읽는 방법이며 최종 업무 규칙의 원본인지 여부를 별도로 정해야 한다.

## 20.1 캐시의 세 가지 질문

무엇이 원본인가, 얼마나 오래된 값을 허용하는가, 캐시 장애 때 어떻게 동작하는가를 먼저 정한다. 상품 설명은 수분 지연을 허용할 수 있지만 재고 확정·계좌 잔액·권한 철회는 다른 요구를 갖는다. 모든 조회에 같은 TTL을 적용하지 않는다.

**Cache-aside**는 캐시 조회 → miss면 DB 조회 → 캐시 채움 흐름이다. **TTL — Time To Live**은 보관 시간이다. 만료는 stale 값을 언젠가 제거하는 수단이지 갱신 직후 일관성의 증거가 아니다.

## 20.2 Spring 캐시 추상화

`@Cacheable`은 결과 재사용을, `@CacheEvict`는 제거를 선언한다. CacheManager가 실제 저장 구현과 연결한다. 활성화·제공자·직렬화·TTL은 별도로 구성해야 하며 어노테이션만으로 Redis가 시작되는 것은 아니다.

```java
@Cacheable(cacheNames = "product-summary", key = "#tenant + ':' + #sku")
public ProductSummary getSummary(String tenant, String sku) {
    return querySummary(tenant, sku);
}
```

이 코드는 확장 설계용이다. 전체 타입·캐시 설정·등록은 생략돼 있고 통합 예제에는 캐시가 없다. 키에 결과를 결정하는 테넌트·언어·권한 범위 등이 빠지면 다른 사용자의 결과를 재사용할 수 있다. 문자열 조합의 충돌이 없도록 인코딩·구조·버전도 고려한다.

## 20.3 자기 호출과 null·오류 캐싱

캐시 어노테이션도 기본 프록시 방식의 자기 호출 문제를 가진다. 같은 클래스 내부 호출이 캐시를 지나지 않는 상황을 테스트한다. null 캐싱은 존재하지 않는 ID 조회 부하를 줄일 수 있지만 나중에 생성된 데이터를 보이지 않게 만들 수 있어 짧은 negative TTL이나 무효화가 필요하다.

DB 장애 결과를 “없음”으로 변환해 오래 캐시하면 장애가 회복돼도 잘못된 결과가 유지된다. 정상 미존재와 인프라 실패를 구분한다. 모든 예외를 빈 목록으로 바꾸는 편의 코드가 캐시와 결합하면 특히 위험하다.

## 20.4 commit 이후 무효화도 만능은 아니다

DB commit 전에 캐시를 지우면 다른 요청이 아직 이전 DB 값을 읽어 캐시를 다시 채울 수 있다. 그래서 commit 이후 무효화를 설계한다. 하지만 다음 경쟁도 남는다.

```text
R: 이전 DB 값을 읽음 ────────────────────── 이전 값을 캐시에 기록
W:                 DB commit → 캐시 삭제
```

오래된 읽기가 삭제보다 늦게 캐시를 채우는 경우다. 짧은 TTL, 값의 버전 비교, 순서를 보장하는 갱신 이벤트, 원본 재검증 등 요구에 맞는 방식을 조합한다. “DB 갱신 후 캐시 삭제 두 줄이면 항상 강한 일관성”이라고 설명하지 않는다.

`@Transactional`과 `@CacheEvict`를 같은 메서드에 붙였을 때 Advice 순서와 transaction-aware cache 설정도 확인한다. 캐시 갱신 시점이 DB commit 뒤인지 테스트한다. Redis와 관계형 DB가 별도 시스템이면 기본적으로 하나의 원자적 commit이 아니다.

## 20.5 stampede·hot key·장애

**Cache stampede**는 같은 인기 키가 만료될 때 많은 요청이 동시에 원본을 조회하는 현상이다. TTL 지터, 요청 병합, 제한된 동시 재계산, stale-while-revalidate 같은 방법을 검토한다. `sync=true`의 보장도 제공자와 실행 환경에 따라 확인해야 하며 모든 서버에 걸친 분산 잠금으로 일반화하지 않는다.

**Hot key**는 한 키에 요청이 집중되는 상태다. 캐시가 있어도 특정 노드·네트워크가 병목일 수 있다. 히트율만 보지 말고 응답 지연·eviction·메모리·원본 부하를 함께 본다. 캐시 장애 때 모든 요청이 DB로 한꺼번에 넘어가면 연쇄 장애가 날 수 있으므로 우회 동시성도 제한한다.

## 실습: 장애 타임라인 작성

별도 Redis 확장 실습에서 상품 설명만 캐시하고 재고 확정은 DB 조건부 UPDATE를 유지한다. 캐시 miss, 만료, Redis 중단, DB 갱신 직후 조회의 네 시나리오를 실행한다. 각 경우의 기대 HTTP 응답과 DB 호출 수를 먼저 적는다.

원고의 캐시 설계는 학습·확장 범위이며 Redis 실행 검증은 [검증 기록](../appendices/verification.md)의 미확인 항목이다. 캐시를 추가하지 않은 통합 예제가 느린 대신 올바른 것으로 증명됐다는 뜻도 아니며, 필요하면 별도 성능 측정으로 판단한다.

## 확인 문제와 해설

**Q1. 히트율 99%면 장애 때도 안전한가?** 남은 1%와 전체 miss 전환 시 원본 부하를 봐야 한다.

**Q2. 캐시 삭제 실패면 DB 트랜잭션을 항상 되돌리는가?** 이미 commit됐다면 불가능하다. 재시도·만료·복구 경로를 설계한다.

**Q3. 재고 캐시로 예약을 확정해도 되는가?** 이 책의 설계에서는 DB가 최종 판단을 담당하며 표시용 캐시로 확정하지 않는다.

## 참고자료

- [캐시 어노테이션](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)
- [Spring Data Redis 캐시](https://docs.spring.io/spring-data/redis/reference/redis/redis-cache.html)
- [Redis eviction](https://redis.io/docs/latest/develop/reference/eviction/)

---

[전체 목차](../index.md) · [← 이전 장](../19-async-outbox/chapter.md) · [다음 장 →](../21-testing/chapter.md)
