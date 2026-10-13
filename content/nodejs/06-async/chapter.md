---
title: "06장. 콜백에서 Promise와 async/await까지"
description: "비동기 작업의 완료와 실패를 호출자에게 전달한다. 순차 실행과 제한된 동시 실행을 선택한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 6
part: 2
enableToc: true
---

# 06장. 콜백에서 Promise와 async/await까지

## 학습 목표

- 비동기 작업의 완료와 실패를 호출자에게 전달한다.
- 순차 실행과 제한된 동시 실행을 선택한다.

## 비동기는 완료 통지의 방식

동기 함수는 결과를 반환하거나 예외를 던진다. 전통적인 Node.js 콜백 API는 첫 번째 인자로 오류를, 나머지 인자로 결과를 전달한다. 콜백을 등록한 바깥 함수가 이미 반환된 뒤 실패가 발생할 수 있으므로 바깥의 `try/catch`만으로 잡을 수 없다. 콜백 안에서 오류를 처리하거나 Promise API를 사용한다.

Promise는 아직 완료되지 않은 작업의 최종 결과를 나타낸다. `async` 함수는 항상 Promise를 반환하며, 함수 안에서 던진 오류는 그 Promise의 거부로 전달된다. `await`는 현재 비동기 함수의 이후 실행을 미루지만 프로세스의 모든 요청을 멈추지는 않는다.

```js
import { setTimeout as delay } from 'node:timers/promises';
const first = delay(10, 'A');
const second = delay(5, 'B');
console.log(await Promise.all([first, second])); // 입력 순서: A, B
try { await Promise.reject(new Error('expected')); }
catch (error) { console.log(error.message); }
```

[실행 파일](../examples/fundamentals/06-async.mjs)

`Promise.all`의 결과 배열은 완료 순서가 아니라 입력 순서를 따른다. 한 항목이 거부되면 전체가 거부되지만 이미 시작한 나머지 작업을 자동 취소하지 않는다. 이것은 실패를 빨리 알리는 기능과 자원 정리가 다른 문제라는 뜻이다.

## 순서가 필요한 작업과 독립적인 작업

사용자를 생성한 뒤 그 ID로 권한을 저장한다면 순차 실행이 필요하다. 서로 독립적인 두 조회는 동시에 시작할 수 있다. 그러나 DB 풀이 5개인데 10만 건을 한 번에 `Promise.all`로 시작하면 실제 연결 수만 제한될 뿐 Promise·대기열·입력 데이터는 메모리에 쌓일 수 있다.

순차 실행은 `for...of` 안에서 `await`한다. 제한된 동시 실행은 작업을 수행할 worker 수를 정하고 항목을 가져가게 한다. 예제의 `mapLimit`은 최대 동시 실행 수를 지키고 입력 순서대로 결과를 반환한다. 실패 이후에는 새 작업 시작을 멈추고 이미 시작한 작업이 정리될 때까지 기다린다.

```js
import { mapLimit } from './src/map-limit.mjs';
const result = await mapLimit([1, 2, 3], 2, async value => value * 10);
console.log(result); // [10, 20, 30]
```

## 놓치기 쉬운 오류 경로

`array.forEach(async fn)`은 콜백의 Promise를 모아 기다리지 않는다. `try { task(); } catch {}`도 `task`가 반환한 Promise의 나중 실패를 잡지 못한다. `await task()` 또는 `return task()`로 수명과 오류 전파를 연결해야 한다. 타이머 콜백에서 던진 오류 역시 등록 함수의 `try/catch` 범위를 벗어난다.

진짜 백그라운드 작업이라면 완료 여부·실패 로그·종료 시 대기·재시도 정책을 명시한다. 단순히 `void task()`로 반환값을 버리는 것은 작업 큐를 만드는 방법이 아니다. 프로세스가 종료되면 메모리에만 존재하던 작업도 사라진다.

취소는 협력적이다. AbortSignal을 받는 함수는 신호를 실제 I/O와 대기에도 전달해야 한다. 이미 DB에서 커밋한 변경이나 외부에 보낸 메시지가 취소 신호만으로 되돌아가지는 않는다.

## 실습과 관찰

`node fundamentals/06-async.mjs`를 실행한다. 이어서 `npm test`에서 동시 실행 수·순서·실패·취소 관련 테스트를 찾아 읽는다. `map-limit.mjs`의 `Promise.allSettled`를 `Promise.all`로 바꾸면 호출자에게 실패가 전달되는 시점과 실행 중 작업의 수명이 어떻게 달라지는지 생각해 본다.

운영 실험에서는 입력 개수와 동시 실행 수를 따로 바꾸며 지연과 메모리를 측정한다. 하나를 바꿨다면 나머지 조건은 고정한다.

## 확인 문제

Promise.all이 첫 오류로 거부되었다. 다른 요청도 모두 중단되었다고 가정해도 되는가?

[해설 보기](../appendices/answers.md#장-06)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Promise.all() - JavaScript | MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all)
- [Global objects | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/globals.html)
- [Timers | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/timers.html)

---

[이전 장](../05-modules/chapter.md) · [책 목차](../index.md) · [다음 장](../07-event-loop/chapter.md)
