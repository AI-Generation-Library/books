---
title: "20장. Redis와 캐싱 전략"
description: "캐시 적중률과 원본 데이터의 일관성을 함께 고려한다. 캐시와 작업 큐의 Redis 운영 정책을 구분한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 20
part: 4
enableToc: true
---

# 20장. Redis와 캐싱 전략

## 학습 목표

- 캐시 적중률과 원본 데이터의 일관성을 함께 고려한다.
- 캐시와 작업 큐의 Redis 운영 정책을 구분한다.

## 먼저 원본을 정한다

캐시는 원본을 더 빨리 읽기 위한 복제다. 사용자의 권한과 작업 결과의 원본은 PostgreSQL이다. Redis에 값이 없거나 접속이 실패해도 원본 조회로 처리할 수 있을지, 실패를 사용자에게 반환할지 결정한다. 세션 저장소·작업 큐처럼 값이 사라지면 업무가 달라지는 사용법을 단순 캐시와 동일하게 취급하면 안 된다.

cache-aside는 캐시 조회 → 미스일 때 DB 조회 → 캐시 저장 순서다. 다음은 Redis가 준비된 환경에서의 흐름을 보여 주는 개념 코드이며 종합 프로젝트의 기본 경로에는 캐시를 넣지 않았다.

```js
async function cachedJob(redis, repo, id) {
  const key = `job:v1:${id}`;
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);
  const job = await repo.job(id);
  if (job) await redis.set(key, JSON.stringify(job), { EX: 15 });
  return job;
}
```

이 함수가 반환한 값을 사용자에게 바로 보내면 안 된다. 캐시 적중 여부와 관계없이 소유권을 검사하고 공개 필드만 선택해야 한다. 키에 사용자를 넣는 것만으로 누락된 인가 검사를 일반적으로 해결할 수는 없다.

## TTL과 무효화의 경합

작업 상태가 변할 때 캐시를 지워도, 동시에 진행 중이던 오래된 DB 읽기가 나중에 낡은 값을 다시 저장할 수 있다. TTL은 낡은 값이 남는 시간을 제한하지만 즉시 일관성을 보장하지 않는다. 상태 버전·짧은 TTL·변경 통지·원본 직접 조회 중 요구사항에 맞는 방법을 택한다.

인기 키가 동시에 만료되면 DB로 요청이 몰리는 스탬피드가 발생할 수 있다. TTL에 작은 무작위 차이를 주거나 한 요청만 재생성하도록 묶는 방법을 검토한다. 락을 쓴다면 만료·소유자 토큰·해제 조건을 함께 설계한다. 로컬 프로세스의 Promise 공유는 다른 인스턴스까지 보호하지 않는다.

## 캐시는 공짜 메모리가 아니다

키 길이·값 크기·종류·TTL·최대 메모리·eviction 정책을 관리한다. 캐시 적중률만 높고 직렬화 비용이 크다면 기대만큼 빨라지지 않을 수 있다. 원본 조회 지연과 전체 응답 지연을 비교한다. 캐시 장애 시 원본에 폭주가 전달되지 않도록 동시 실행 제한도 필요하다.

종합 프로젝트의 Redis는 BullMQ가 작업 상태를 관리하는 용도다. 그래서 Compose에서는 `noeviction`을 지정했다. 메모리가 찼을 때 임의 키 삭제로 큐 상태가 망가지는 것을 피하려는 선택이며, 무제한 사용을 허용한다는 뜻은 아니다. 용량·경보·정리·백업 정책이 필요하다. 업무 큐와 버릴 수 있는 캐시는 별도 인스턴스로 분리하는 편이 운영 정책을 명확하게 한다.

## Redis 연결의 수명

연결 생성·오류 이벤트·종료 경로를 갖춘다. 실패한 연결에 명령이 무한 대기하면 HTTP 요청도 끝나지 않을 수 있다. producer는 빠르게 실패해 outbox에 남기고 worker는 큐 소비를 재연결하며 유지하는 식으로 역할별 정책이 다를 수 있다. 클라이언트 라이브러리의 버전별 동작을 확인한다.

## 실습과 관찰

원본 직접 조회와 캐시 적용 조회를 비교하려면 먼저 전용 Redis와 DB를 준비한다. hit·miss·TTL 만료·Redis 장애 네 경우를 구분해 기록한다. 이번 집필 환경에서 캐시 예제 실행은 검증하지 않았으며 코드 문법 검사와 실행 검증을 구분한다.

종합 프로젝트의 Compose와 `src/bull-queue.mjs`를 읽어 큐 보관 정책을 확인한다. 캐시용 Redis 설정을 큐에 그대로 적용하지 않는 이유를 설명한다.

## 확인 문제

TTL을 10초로 설정했으니 변경 직후에도 항상 최신 값을 읽는가?

[해설 보기](../appendices/answers.md#장-20)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [node-redis guide (JavaScript) | Docs](https://redis.io/docs/latest/develop/clients/nodejs/)
- [Key eviction | Docs](https://redis.io/docs/latest/develop/reference/eviction/)
- [Going to production | BullMQ](https://docs.bullmq.io/guide/going-to-production)

---

[이전 장](../19-web-security/chapter.md) · [책 목차](../index.md) · [다음 장](../21-http-client/chapter.md)
