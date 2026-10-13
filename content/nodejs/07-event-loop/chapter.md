---
title: "07장. 이벤트 루프의 내부 동작"
description: "I/O·타이머·마이크로태스크의 실행 문맥을 구분한다. 실행 순서 암기 대신 보장되는 관계를 검증한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 7
part: 2
enableToc: true
---

# 07장. 이벤트 루프의 내부 동작

## 학습 목표

- I/O·타이머·마이크로태스크의 실행 문맥을 구분한다.
- 실행 순서 암기 대신 보장되는 관계를 검증한다.

## 호출 스택과 예약된 후속 작업

JavaScript 함수가 실행 중이면 같은 스레드에서 다른 JavaScript 콜백이 그 함수를 중간에 끊고 실행되지 않는다. 함수가 반환되고 적절한 처리 지점에 도달해야 Promise 후속 작업이나 I/O 콜백을 실행할 수 있다. 이것이 긴 동기 계산이 여러 요청을 함께 지연시키는 이유다.

libuv 이벤트 루프는 I/O 통지, `setImmediate`, 타이머 등 서로 다른 종류의 후속 작업을 처리한다. Promise 반응과 `queueMicrotask`는 JavaScript 마이크로태스크 처리와 연결되고, `process.nextTick`은 Node.js의 별도 큐를 사용한다. 이들을 하나의 단순 FIFO 대기열로 설명하면 실제 순서를 잘못 예측하게 된다.

## 순서는 실행 문맥을 포함해서 설명한다

Node.js 24에서 ESM의 최상위 평가는 비동기 모듈 평가 문맥의 영향을 받는다. 따라서 CommonJS 최상위에서 본 `nextTick`과 Promise의 순서를 ESM 예제에 그대로 옮기면 안 된다. top-level await 유무나 이미 마이크로태스크 안에 있는지도 영향을 준다.

```js
import { readFile } from 'node:fs';
console.log('sync');
queueMicrotask(() => console.log('microtask'));
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));
readFile(new URL(import.meta.url), () => {
  setTimeout(() => console.log('io:timeout'), 0);
  setImmediate(() => console.log('io:immediate'));
});
// ESM의 최상위 평가 문맥과 I/O 콜백의 문맥을 구분한다.
```

[실행 파일](../examples/fundamentals/07-event-loop.mjs)

이 실험에서 `sync`는 먼저 출력된다. 같은 I/O 콜백 안에서 예약한 `io:immediate`는 `io:timeout`보다 앞선다. 파일 I/O가 언제 끝나는지까지 포함한 전체 출력의 한 가지 순서만 정답으로 고정하지 않는다. 테스트는 보장되는 관계와 애플리케이션의 결과를 중심으로 작성한다.

## 타이머는 정확한 실행 시각을 보장하지 않는다

`setTimeout(fn, 100)`은 100ms 뒤에 반드시 실행하겠다는 예약이 아니다. 최소 대기 기준에 도달했더라도 앞선 JavaScript 작업과 운영체제 스케줄링 때문에 더 늦어질 수 있다. libuv 1.45 이후의 타이머 처리 변화처럼 런타임 버전도 영향을 주므로 오래된 그림만으로 현재 동작을 단정하지 않는다.

`setInterval(async () => ...)`은 반환한 Promise가 끝나기를 기다리지 않는다. 작업이 주기보다 오래 걸리면 중첩 실행될 수 있다. 예제의 outbox dispatcher는 이전 실행이 끝난 뒤 다음 타이머를 등록한다. 처리 순서와 동시 실행 제한이 중요하다면 이런 수명 관리가 필요하다.

## 기아와 공정성

`process.nextTick`이나 마이크로태스크를 재귀적으로 계속 등록하면 I/O를 처리할 기회를 빼앗을 수 있다. 긴 계산을 작은 덩어리로 나누고 이벤트 루프로 제어권을 돌려주거나 Worker로 이동하는 방법을 검토한다. `await Promise.resolve()`만 반복한다고 항상 I/O 처리 기회를 주는 것은 아니다.

`timer.unref()`는 해당 타이머 하나만으로 프로세스를 계속 살려 두지 않게 한다. 작업 완료를 보장하는 기능은 아니다. 종합 프로젝트의 서버 소켓이 살아 있을 때 주기적 dispatcher가 동작하고, 종료 시에는 명시적으로 dispatcher를 중지하고 실행 중 작업을 기다린다.

## 실습과 관찰

`node fundamentals/07-event-loop.mjs`를 여러 번 실행한다. `io:immediate`와 `io:timeout`의 상대 순서를 기록하고, 최상위 마이크로태스크 순서는 ESM 문맥과 함께 적는다. 같은 코드를 `.cjs` 문법으로 바꾼 실험과 비교할 때는 두 파일 형식을 기록한다.

26장의 이벤트 루프 지연 실험으로 넘어가 타이머 간격이 긴 동기 계산의 영향을 받는지 확인한다. 실행 순서와 운영 지연의 관계를 연결하는 것이 목표다.

## 확인 문제

await Promise.resolve()를 긴 루프 안에 넣었으므로 HTTP 요청도 충분히 처리할 수 있다는 주장이 맞는가?

[해설 보기](../appendices/answers.md#장-07)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [The Node.js Event Loop | Node.js Learn](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [Understanding setImmediate() | Node.js Learn](https://nodejs.org/en/learn/asynchronous-work/understanding-setimmediate)
- [Process | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/process.html)

---

[이전 장](../06-async/chapter.md) · [책 목차](../index.md) · [다음 장](../08-filesystem/chapter.md)
