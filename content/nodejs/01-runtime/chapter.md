---
title: "01장. Node.js는 무엇이고 어떻게 동작하는가"
description: "런타임·엔진·프레임워크를 구분한다. JavaScript 실행과 I/O 대기를 분리해 설명한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 1
part: 1
enableToc: true
---

# 01장. Node.js는 무엇이고 어떻게 동작하는가

## 학습 목표

- 런타임·엔진·프레임워크를 구분한다.
- JavaScript 실행과 I/O 대기를 분리해 설명한다.

## JavaScript를 실행하는 환경

JavaScript라는 언어만으로는 파일을 열거나 TCP 연결을 만들 수 없다. 언어의 구문과 객체를 해석·실행하는 엔진에, 운영체제 기능을 연결하는 API와 프로그램 수명 관리 기능을 더해야 한다. Node.js는 이런 실행 환경이다. Express는 그 환경 위에서 HTTP 애플리케이션을 만들기 편하게 하는 라이브러리다. Express를 설치하지 않아도 Node.js로 서버를 만들 수 있다.

브라우저와 Node.js는 같은 언어를 사용하지만 제공하는 전역 객체가 다르다. 브라우저의 `document`는 DOM을 가리키고, Node.js의 `process`는 현재 프로세스의 인자·환경·종료 상태를 다룬다. 두 환경에 모두 있는 `fetch`도 보안 정책이나 연결 관리까지 완전히 같다고 가정하면 안 된다. 서버는 브라우저의 CORS 보호를 대신 적용하지 않는다.

## V8, Node.js 바인딩, libuv와 운영체제

```text
애플리케이션 JavaScript
  ├─ V8: JavaScript 실행, 객체와 메모리 관리
  └─ Node.js API와 네이티브 바인딩
       └─ libuv/운영체제: 이벤트 통지, 일부 작업의 스레드 풀 실행
```

예를 들어 네트워크 응답을 기다리는 동안 JavaScript가 루프를 돌며 수신 여부를 검사할 필요는 없다. 운영체제의 I/O 통지 기능을 이용하고, 결과를 처리할 시점에 JavaScript 콜백을 실행한다. 반면 큰 배열을 정렬하는 JavaScript 연산은 호출한 스레드를 계속 점유한다. `async`라는 키워드를 붙여도 이 연산이 자동으로 다른 CPU로 이동하지 않는다.

기본 JavaScript 실행 스레드가 하나라는 말은 프로세스에 스레드가 하나뿐이라는 뜻이 아니다. V8과 libuv는 내부 작업을 수행하고, 애플리케이션도 Worker Threads를 만들 수 있다. 파일 시스템 작업·일부 DNS 조회·암호화 작업 등은 libuv 작업 풀과 관련된다. 모든 네트워크 요청이 이 풀의 한 스레드를 점유한다고 설명하면 동작을 잘못 이해하게 된다.

## 동시 요청을 처리한다는 의미

한 요청이 DB 응답을 기다리는 동안 다른 요청의 코드를 실행할 수 있다. 이것이 I/O 중심 서버에서 유용하다. 그러나 같은 이벤트 루프에서 한 콜백이 500ms 동안 CPU를 사용하면, 이미 도착한 다른 요청도 그 콜백이 끝나기를 기다릴 수 있다. 처리량뿐 아니라 사용자별 지연 시간을 함께 봐야 하는 이유다.

| 작업 | 먼저 검토할 접근 |
| --- | --- |
| 외부 API·DB 호출 | 비동기 I/O, 타임아웃, 동시 실행 수 제한 |
| 큰 파일 전송 | 스트림, 백프레셔, 요청 크기 제한 |
| 긴 JavaScript 계산 | 알고리즘 개선, Worker 풀, 별도 작업 서비스 |
| 짧은 배치·CLI | 단순한 순차 실행부터 시작하고 측정 |

런타임 선택은 유행보다 요구사항을 기준으로 한다. CPU 계산이 있다고 Node.js를 무조건 배제할 필요는 없지만, HTTP 처리와 긴 계산을 같은 실행 흐름에 넣는 비용은 설계에 반영해야 한다.

## 실습과 관찰

`examples` 디렉터리에서 다음을 실행한다.

```sh
node fundamentals/01-runtime.mjs
```

```js
import { version, versions, platform } from 'node:process';
console.log({ version, v8: versions.v8, uv: versions.uv, platform });
console.log(typeof document, typeof fetch); // undefined function
```

[실행 파일](../examples/fundamentals/01-runtime.mjs)

버전 문자열은 설치 환경에 따라 달라진다. 마지막 출력은 `undefined function`이다. `document`가 없고 `fetch`가 함수라는 뜻이다. V8 버전과 Node.js 버전이 별개로 표시되는 이유를 설명해 보자. `process.versions.uv`도 기록해 두면 이벤트 루프 동작을 비교할 때 환경 차이를 추적할 수 있다.

## 확인 문제

DB 대기는 거의 없는데 CPU가 꽉 차고 모든 요청이 느려졌다. async 함수를 더 많이 호출하면 해결되는가?

[해설 보기](../appendices/answers.md#장-01)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Process | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/process.html)
- [Don't Block the Event Loop (or the Worker Pool) | Node.js Learn](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)

---

[책 목차](../index.md) · [다음 장](../02-environment/chapter.md)
