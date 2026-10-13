---
title: "26장. 병목을 측정하고 개선하기"
description: "처리량·지연 분포·오류율·자원 포화를 함께 읽는다. 측정 조건과 병목 가설을 분리해 실험한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 26
part: 6
enableToc: true
---

# 26장. 병목을 측정하고 개선하기

## 학습 목표

- 처리량·지연 분포·오류율·자원 포화를 함께 읽는다.
- 측정 조건과 병목 가설을 분리해 실험한다.

## 먼저 질문을 좁힌다

느리다는 보고만으로는 무엇을 바꿔야 할지 알 수 없다. 특정 API의 p99인지, 작업 접수부터 완료까지 걸리는 시간인지, 로그인 순간의 지연인지 구분한다. 평균 지연은 일부 매우 느린 요청을 숨길 수 있다. 사용자 요구와 연결된 지표를 정의한다.

처리량이 늘어도 오류율과 대기 시간이 급증했다면 좋은 개선이 아닐 수 있다. CPU·RSS·이벤트 루프 지연·DB 풀 대기·큐의 가장 오래된 작업 나이를 함께 본다. 외부 의존성의 응답 시간과 애플리케이션 자체 계산 시간을 나누면 가설을 좁히기 쉽다.

```js
import { monitorEventLoopDelay, performance } from 'node:perf_hooks';
import { setTimeout as delay } from 'node:timers/promises';
const histogram = monitorEventLoopDelay({ resolution: 10 }); histogram.enable();
await delay(20);
const start = performance.now(); while (performance.now() - start < 40) { /* 의도적인 CPU 부하 */ }
await delay(20); histogram.disable();
console.log({ p99Ms: histogram.percentile(99) / 1e6, memory: process.memoryUsage() });
```

[실행 파일](../examples/fundamentals/26-performance.mjs)

이 예제는 의도적으로 짧은 CPU 부하를 만들어 이벤트 루프 지연을 관찰한다. histogram 값은 나노초 단위이므로 ms로 바꾼다. 숫자는 기계·다른 프로세스·샘플 수에 따라 달라지며 특정 p99 값을 정답으로 고정하지 않는다.

## 재현 가능한 부하

입력 크기·요청 비율·동시 연결·생성 방식·시험 시간·워밍업·성공 기준을 기록한다. 부하 생성기와 서버가 같은 CPU를 쓰면 생성기 한계가 서버 한계처럼 보일 수 있다. 응답을 기다리고 다음 요청을 보내는 closed-loop 방식은 서버가 느려질수록 요청 생성량도 줄어드는 특성이 있다.

실제 사용자는 계속 요청을 생성할 수 있으므로 도착률을 고정한 시험도 필요할 수 있다. 어떤 모델을 썼는지 명시한다. 운영 서비스에 허가 없이 부하를 가하지 않고 테스트 환경과 제한된 데이터로 실험한다.

## 프로파일로 가설 확인

```sh
node --cpu-prof fundamentals/26-performance.mjs
```

실행 후 생성된 프로파일을 개발 도구로 열어 시간이 쌓인 호출 경로를 본다. CPU 프로파일은 CPU에서 실행 중인 코드의 분포이지 DB 응답을 기다린 모든 시간을 설명하는 자료는 아니다. I/O 지연은 별도 타이밍과 추적으로 연결한다.

같은 알고리즘을 다른 문법으로 바꾼 작은 차이보다 불필요한 전체 읽기·중복 조회·무제한 병렬 호출·과도한 로그 직렬화가 더 큰 병목일 수 있다. 최적화 전후에 같은 입력과 조건을 사용하고 정확성 테스트도 유지한다.

## 대기열과 과부하

안정적인 구간에서 평균 동시 처리량·도착률·평균 체류 시간은 서로 관련된다. 처리 시간이 두 배가 되면 같은 도착률에서도 대기 중 요청 수가 커질 수 있다. 무한 대기열은 오류를 늦게 드러낼 뿐 메모리와 지연을 소비한다.

큐 크기·작업 기한·동시 실행 수·거부 정책을 함께 정한다. 처리량이 약간 낮더라도 과부하에서 빠르게 실패하고 회복되는 시스템이 사용자의 전체 성공률을 높일 수 있다.

## 실습과 관찰

`node fundamentals/26-performance.mjs`를 여러 번 실행해 p99 값이 고정되어 있지 않은지 확인한다. CPU 프로파일은 실습 디렉터리에 생기며 Git에서 제외한다.

부하 측정 보조 스크립트는 [load.mjs](../examples/scripts/load.mjs)다. 학습용 closed-loop 도구로, 전문 벤치마크나 운영 용량 인증을 대신하지 않는다. 실제 실행 결과와 조건은 검증 기록에 별도로 남긴다.

## 확인 문제

평균 응답 시간만 개선되었으므로 성능 개선이 완료되었다고 판단할 수 있는가?

[해설 보기](../appendices/answers.md#장-26)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Performance measurement APIs | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/perf_hooks.html)
- [Command-line API | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/cli.html)
- [Profiling Node.js Applications | Node.js Learn](https://nodejs.org/en/learn/getting-started/profiling)

---

[이전 장](../25-threads-processes/chapter.md) · [책 목차](../index.md) · [다음 장](../27-memory/chapter.md)
