---
title: "25장. 동시성과 병렬성: 스레드와 프로세스"
description: "libuv 작업 풀·Worker Threads·자식 프로세스의 역할을 구분한다. 계산 분리의 이득과 전달 비용을 측정한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 25
part: 6
enableToc: true
---

# 25장. 동시성과 병렬성: 스레드와 프로세스

## 학습 목표

- libuv 작업 풀·Worker Threads·자식 프로세스의 역할을 구분한다.
- 계산 분리의 이득과 전달 비용을 측정한다.

## 비동기 I/O와 병렬 계산

동시성은 여러 작업의 진행을 겹쳐 관리하는 성질이고, 병렬성은 같은 시간에 여러 실행 자원에서 계산하는 성질이다. Node.js는 비동기 I/O로 많은 대기를 관리할 수 있지만 큰 JavaScript 계산을 자동 병렬화하지 않는다. CPU를 많이 쓰는 함수가 `async`여도 호출 스레드에서 실행된다.

libuv 작업 풀은 일부 내장 비동기 작업에 사용된다. Worker Threads는 별도의 JavaScript 실행 환경에서 계산하도록 애플리케이션이 만드는 스레드다. 작업 풀 크기를 키우는 것과 JavaScript Worker 수를 늘리는 것은 다른 조정이다. CPU와 메모리·컨테이너 제한을 고려해야 한다.

```js
import { parentPort, workerData } from 'node:worker_threads';
function fib(n) { return n < 2 ? n : fib(n - 1) + fib(n - 2); }
if (!Number.isInteger(workerData) || workerData < 0 || workerData > 35) throw new RangeError('n must be 0..35');
parentPort.postMessage(fib(workerData));
```

[실행 파일](../examples/fundamentals/25-worker.mjs)

```js
import { Worker } from 'node:worker_threads';
import { pathToFileURL } from 'node:url';
export function fibWorker(n) {
  return new Promise((resolve, reject) => {
    const worker = new Worker(new URL('./25-worker.mjs', import.meta.url), { workerData: n });
    worker.once('message', resolve); worker.once('error', reject);
    worker.once('exit', code => { if (code !== 0) reject(new Error(`Worker exited ${code}`)); });
  });
}
if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  console.log(await fibWorker(20));
}
```

[실행 파일](../examples/fundamentals/25-parallel.mjs)

예제는 설명을 위해 요청마다 Worker를 하나 만든다. 실제 짧은 작업에서는 생성·초기화·메시지 전달 비용이 계산 이득보다 클 수 있다. 운영에서는 제한된 크기의 Worker 풀과 대기열을 두고 과부하 시 거부하거나 지연시킨다.

## 데이터 전달과 메모리

메시지는 일반적으로 구조화 복제를 사용한다. 큰 데이터를 복사하면 시간과 메모리가 든다. 전송 가능한 ArrayBuffer를 넘기거나 SharedArrayBuffer를 공유하는 방법도 있지만 소유권·동기화·동시 접근 규칙이 필요하다. Buffer가 가진 풀 메모리를 무심코 전송하면 의도한 범위와 다른 비용이 생길 수 있다.

공유 메모리는 자동으로 안전한 상태 공유를 만드는 기능이 아니다. Atomics 같은 수단과 자료 구조의 프로토콜을 설계해야 한다. 이 책의 기본 프로젝트는 메시지와 DB 상태로 경계를 유지하고 공유 메모리를 도입하지 않는다.

## 자식 프로세스와 외부 명령

외부 프로그램을 실행하거나 더 강한 실패 격리가 필요하면 `child_process`를 검토한다. `spawn`은 입출력을 스트림으로 다룰 수 있고 `exec`는 셸 해석과 출력 버퍼 제한을 고려해야 한다. 사용자 입력을 셸 명령 문자열에 붙이면 명령 주입이 생길 수 있다. 실행 파일과 인자 배열을 분리하고 셸을 불필요하게 켜지 않는다.

Worker의 오류·비정상 exit를 기다리는 경로가 필요하다. 메시지만 기다리다 작업이 실패하면 호출자가 영원히 대기할 수 있다. 종료 기한과 취소 정책도 갖춘다. 작업 종료가 외부 부수 효과를 취소해 주는 것은 아니다.

## 스레드 수와 처리량

코어 수보다 훨씬 많은 계산 Worker를 만들면 문맥 전환과 메모리 사용이 증가할 수 있다. 컨테이너가 사용할 수 있는 CPU 예산과 다른 프로세스의 사용량도 함께 본다. 작업 크기·풀 크기·대기 시간·전체 HTTP p99를 측정해 결정한다.

## 실습과 관찰

`node fundamentals/25-parallel.mjs`를 실행하면 6765가 출력된다. 기본 테스트는 정상 메시지와 입력 제한 오류를 각각 확인한다. 재귀 피보나치는 계산 분리를 관찰하기 위한 예제이며 실무 알고리즘 선택의 권장안은 아니다.

같은 계산을 직접 실행한 경우와 Worker 실행을 비교할 때 Worker 생성 비용을 포함할지, 재사용 풀을 사용할지 명시한다. 평균 처리 시간만으로 HTTP 응답성 개선을 판단하지 않는다.

## 확인 문제

DB 조회가 느려 Worker Threads를 100개 만들었다. 일반적으로 올바른 첫 대응인가?

[해설 보기](../appendices/answers.md#장-25)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Worker threads | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/worker_threads.html)
- [Child process | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/child_process.html)
- [Thread pool work scheduling - libuv documentation](https://docs.libuv.org/en/v1.x/threadpool.html)

---

[이전 장](../24-uploads/chapter.md) · [책 목차](../index.md) · [다음 장](../26-performance/chapter.md)
