---
title: "22장. 백그라운드 작업과 작업 큐"
description: "접수·전달·실행·결과 저장 단계를 분리한다. 최소 한 번 전달과 멱등 소비자의 관계를 설명한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 22
part: 5
enableToc: true
---

# 22장. 백그라운드 작업과 작업 큐

## 학습 목표

- 접수·전달·실행·결과 저장 단계를 분리한다.
- 최소 한 번 전달과 멱등 소비자의 관계를 설명한다.

## HTTP 요청 밖으로 작업 옮기기

업로드한 텍스트를 분석하는 작업이 오래 걸리면 HTTP 연결을 끝까지 붙잡는 대신 작업 ID를 반환하고 결과를 나중에 조회하게 할 수 있다. 큐는 생산자와 소비자의 속도를 분리하지만 처리 용량을 늘려 주는 마법은 아니다. 생산량이 소비량보다 계속 크면 대기 시간과 저장 공간이 커진다.

```text
uploading → queued → processing → completed
                         └→ retrying → processing
                         └→ failed
```

API는 파일 저장과 접수를 담당하고 worker는 분석을 담당한다. dispatcher는 DB의 outbox를 읽어 큐에 전달한다. 작업 상태는 사용자에게 보여 주는 업무 상태이고 BullMQ 내부 상태와 완전히 같은 개념은 아니다.

## outbox가 지키는 것

`enqueueJob()`은 queued와 outbox를 같은 DB 트랜잭션에 기록한다. dispatcher는 큐 추가가 성공한 뒤 outbox를 삭제한다. 큐에 메시지를 넣고 삭제 전에 죽으면 같은 작업을 다시 전달할 수 있다. 이 창을 없앴다고 주장하는 대신 중복 전달을 견디게 한다.

BullMQ의 `jobId`에 업무 작업 UUID를 사용하면 큐에 남아 있는 동일 ID 추가를 합칠 수 있다. 그러나 완료 작업이 보관 기한 이후 제거되면 다시 추가될 수도 있다. 따라서 큐 중복 제거만으로 업무의 영구적인 exactly-once를 보장할 수 없다.

## 소비자가 멱등적으로 동작하기

텍스트 통계는 같은 변경 불가능한 파일을 읽으면 같은 결과가 나오는 계산이다. 소비자는 완료 작업이면 바로 반환하고, 결과 저장은 완료 상태를 실패로 되돌리지 않게 한다. 중복 계산 자체는 가능하지만 이 예제의 결과 덮어쓰기는 같은 값이므로 안전한 범위에 있다.

이 성질을 결제·이메일 발송에 그대로 적용하면 안 된다. 외부 부수 효과에는 그 시스템의 멱등 키나 DB 기록·상태 전이·보상 정책이 필요하다. 중복 실행을 막는 락도 만료와 프로세스 정지 때문에 단독으로 충분하지 않을 수 있다.

## 재시도, stalled와 종료

예제는 최대 3회, 지수 백오프로 재시도한다. 작업 잠금을 갱신하지 못하면 stalled로 판단되어 다시 실행될 수 있다. 이벤트 루프를 오래 막는 CPU 작업은 잠금 갱신도 지연시킬 수 있으므로 별도 worker thread·프로세스·작업 서비스로 분리하는 선택을 검토한다.

일시적 실패와 영구 입력 오류를 구분하면 불필요한 재시도를 줄일 수 있다. 예제는 단순화를 위해 잘못된 UTF-8도 재시도 후 failed가 된다. 운영에서는 오류 분류와 실패 작업의 진단·수동 재처리 절차를 추가한다.

종료 시 신규 작업 수신을 멈추고 실행 중 작업을 기한 내 기다린다. 프로세스가 갑자기 죽어도 복구되는지 실제 Redis·DB 환경에서 시험해야 한다. 메모리 큐는 개발 데모이며 재시작 내구성을 제공하지 않는다.

## 예약 작업과 큐 용량

정기 정리 작업도 중복 실행을 예상해야 한다. 여러 인스턴스의 `setInterval`은 각각 실행된다. 공유 스케줄러를 사용하거나 작업 ID·실행 구간·DB 조건으로 반복에 안전하게 만든다. 대기 개수·가장 오래된 작업 나이·실패율·재시도율을 함께 모니터링하고 접수 상한을 정한다.

## 실습과 관찰

`src/queue.mjs`의 `dispatch()`를 읽고 큐가 실패했을 때 outbox를 지우지 않는 테스트를 확인한다. `src/bull-queue.mjs`에서 재시도·보관 기한·jobId를 찾는다.

PostgreSQL·Redis 통합 실습은 전용 서비스에서 수행한다. 이번 환경의 미실행 여부는 검증 기록을 따른다. 완료 작업을 중복 전달해도 결과가 유지되는 것은 기본 테스트로 확인했다.

## 확인 문제

BullMQ jobId를 썼으므로 완료 후 몇 달이 지나도 같은 업무가 다시 실행될 수 없는가?

[해설 보기](../appendices/answers.md#장-22)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Job Ids | BullMQ](https://docs.bullmq.io/guide/jobs/job-ids)
- [Retrying failing jobs | BullMQ](https://docs.bullmq.io/guide/retrying-failing-jobs)
- [Stalled | BullMQ](https://docs.bullmq.io/guide/jobs/stalled)
- [Graceful shutdown | BullMQ](https://docs.bullmq.io/guide/workers/graceful-shutdown)

---

[이전 장](../21-http-client/chapter.md) · [책 목차](../index.md) · [다음 장](../23-realtime/chapter.md)
