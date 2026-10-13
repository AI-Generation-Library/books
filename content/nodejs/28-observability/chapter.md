---
title: "28장. 로그·메트릭·트레이스로 동작 관찰하기"
description: "요청 문맥을 유지하며 안전한 구조화 로그를 남긴다. 증상·원인·업무 상태를 다른 지표로 관찰한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 28
part: 6
enableToc: true
---

# 28장. 로그·메트릭·트레이스로 동작 관찰하기

## 학습 목표

- 요청 문맥을 유지하며 안전한 구조화 로그를 남긴다.
- 증상·원인·업무 상태를 다른 지표로 관찰한다.

## 세 가지 자료의 역할

로그는 개별 사건과 문맥을, 메트릭은 시간에 따른 집계 상태를, 트레이스는 여러 작업·서비스를 잇는 실행 경로를 보여 준다. 한 가지로 모든 질문을 해결하려 하지 않는다. 느린 요청의 전체 경로를 찾는 데는 추적이, 큐 적체 추이를 보는 데는 메트릭이 유용하다.

종합 프로젝트는 JSON 구조화 로그와 요청 ID를 실제 구현한다. 메트릭 서버와 OpenTelemetry 수집기를 구성한 프로젝트라고 주장하지 않는다. 해당 확장은 아래 설계 기준을 따라 별도로 구성·검증해야 한다.

## 요청 문맥을 비동기 흐름에 전달하기

```js
import { AsyncLocalStorage } from 'node:async_hooks';
const context = new AsyncLocalStorage();
function withRequest(next) {
  context.run({ requestId: crypto.randomUUID() }, next);
}
function log(message) {
  console.log(JSON.stringify({ requestId: context.getStore()?.requestId, message }));
}
```

실제 코드는 `src/app.mjs`에 있다. 요청마다 별도 store를 만들고 비동기 실행 문맥에 요청 ID를 연결한다. 전역 변수에 마지막 요청 ID를 저장하는 방법은 동시에 들어온 요청이 서로 덮어쓰므로 안전하지 않다.

AsyncLocalStorage가 다른 프로세스와 큐 메시지까지 자동으로 이어지는 것은 아니다. 작업 ID·추적 문맥을 메시지에 명시적으로 전달하고 새 소비 작업에서 연결한다. 큐 대기와 실제 처리 시간을 별도로 기록하면 원인을 구분하기 쉽다.

## 측정할 값과 라벨

HTTP 요청 수·오류율·지연 분포, DB 풀 대기, 이벤트 루프 지연, 큐 대기 나이, 작업 실패율을 우선한다. URL 전체·사용자 ID·이메일·작업 ID를 메트릭 라벨로 사용하면 시계열 수가 폭증할 수 있다. 라우트 템플릿과 제한된 오류 코드처럼 종류가 한정된 값을 쓴다.

로그에는 필요할 때 작업 ID를 남길 수 있지만 보관과 개인정보 정책을 적용한다. 비밀번호·토큰·본문 전체를 자동 기록하지 않는다. 예제의 요청 로그는 메서드·상태·소요 시간·서버 생성 요청 ID를 남긴다. 사용자 제공 ID를 그대로 신뢰해 로그 조작이나 충돌을 만들지 않는다.

## 알림은 조치와 연결한다

CPU가 높다는 알림 하나보다 사용자 오류율 증가·작업 완료 기한 위반처럼 실제 영향과 연결된 신호가 유용하다. 큐 대기 나이가 늘고 처리량이 줄면 worker·DB·Redis·파일 접근을 순서대로 확인할 수 있어야 한다. 경보마다 확인할 자료와 담당 행동을 정한다.

트레이싱 샘플링을 적용했다면 모든 실패 요청의 흔적이 남는다고 가정하지 않는다. 요청 ID·업무 상태 기록·집계 지표를 보완적으로 유지한다. 관측 코드도 이벤트 루프와 로그 저장소에 부하를 주므로 전송 실패와 버퍼 상한을 고려한다.

## 실습과 관찰

`npm start` 후 `npm run smoke`를 실행하고 같은 HTTP 응답의 X-Request-Id와 로그의 requestId를 비교한다. 로그인 요청의 비밀번호가 로그에 없는지도 확인한다.

다음 확장 실습에서는 라우트 템플릿별 지연과 오류율을 집계하고 작업 ID를 라벨로 넣지 않는다. 실제 수집기·대시보드 검증은 이번 실행 범위에 포함하지 않았다.

## 확인 문제

AsyncLocalStorage를 사용했으므로 Redis 큐를 소비하는 별도 worker에서도 요청 ID가 자동으로 유지되는가?

[해설 보기](../appendices/answers.md#장-28)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Asynchronous context tracking | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/async_context.html)
- [JavaScript | OpenTelemetry](https://opentelemetry.io/docs/languages/js/)
- [Metric and label naming | Prometheus](https://prometheus.io/docs/practices/naming/)

---

[이전 장](../27-memory/chapter.md) · [책 목차](../index.md) · [다음 장](../29-resilience/chapter.md)
