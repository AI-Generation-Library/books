---
title: "21장. 외부 API를 안정적으로 호출하기"
description: "HTTP 실패와 네트워크 실패를 구분한다. 전체 호출 기한·취소·안전한 재시도를 설계한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 21
part: 5
enableToc: true
---

# 21장. 외부 API를 안정적으로 호출하기

## 학습 목표

- HTTP 실패와 네트워크 실패를 구분한다.
- 전체 호출 기한·취소·안전한 재시도를 설계한다.

## 외부 호출도 애플리케이션의 자원이다

외부 API가 느리면 대기 요청·소켓·메모리가 쌓인다. 호출 대상마다 최대 동시 실행 수와 전체 기한을 정한다. DB 풀이 제한되어 있다고 외부 HTTP 호출 수도 자동으로 제한되는 것은 아니다. `mapLimit` 같은 제한은 결과가 빨리 오는 정상 상황보다 장애 상황에서 효과가 크다.

```js
export async function getJson(url, { signal, timeoutMs = 2000 } = {}) {
  const deadline = AbortSignal.timeout(timeoutMs);
  const combined = signal ? AbortSignal.any([signal, deadline]) : deadline;
  const response = await fetch(url, { signal: combined });
  if (!response.ok) { await response.body?.cancel(); throw new Error(`HTTP ${response.status}`); }
  return response.json();
}
```

[실행 파일](../examples/fundamentals/21-fetch.mjs)

이 함수는 HTTP 상태가 실패여도 `fetch` 자체는 정상 응답 객체를 반환할 수 있다는 점을 처리한다. 네트워크 실패는 예외로, HTTP 실패는 `response.ok` 검사로 확인한다. 응답을 읽거나 취소해 연결 자원도 정리한다. 실제 대용량 API에서는 `response.json()`이 본문 전체를 메모리에 올리는 비용과 응답 크기 제한을 추가해야 한다.

## 타임아웃은 어디까지 적용되는가

예제는 호출자의 취소 신호와 자체 deadline을 `AbortSignal.any`로 결합한다. 헤더 수신뿐 아니라 본문 소비도 같은 fetch 신호의 영향을 받는다. 그러나 이후 수행하는 DB 쓰기나 임의 계산은 자동으로 취소되지 않는다. 신호를 지원하는 작업에 명시적으로 전달하고 단계를 시작하기 전에 취소 여부를 확인한다.

`Promise.race([fetch(...), timeout])`만 사용하면 호출자에게 오류를 돌려줘도 실제 fetch가 계속 실행될 수 있다. 완료 통지와 실제 자원 중단을 분리해 생각해야 한다. 서버에서 변경이 이미 일어났다면 클라이언트 취소로 롤백되지도 않는다.

## 재시도할 실패와 하지 않을 실패

잘못된 입력이나 잘못된 자격 증명은 같은 요청을 반복해도 개선되지 않는다. 일시적인 연결 실패·429·일부 5xx는 제한된 재시도를 검토할 수 있지만, 작업의 멱등성과 서버의 안내를 함께 본다. `Retry-After`가 있다면 정책에 반영한다.

지수 백오프에 jitter를 더하면 여러 클라이언트가 동시에 재시도하는 폭주를 줄일 수 있다. 각 시도에 2초씩 10번을 허용하는 것과 전체 사용자 요청 기한을 3초로 정하는 것은 다르다. 시도 횟수·총 소요 시간·남은 기한을 함께 제한한다.

결제나 작업 생성처럼 부수 효과가 있는 POST는 응답을 받지 못했더라도 서버가 수행했을 수 있다. 상대 API의 멱등 키 지원이나 결과 확인 절차 없이 자동 반복하지 않는다. GET도 업무 구현이 실제로 부수 효과를 갖지 않는지 계약을 확인한다.

## 연결과 대상의 경계

Node.js의 내장 fetch는 HTTP 클라이언트 구현을 이용하며 연결을 관리한다. 요청마다 별도 클라이언트나 dispatcher를 만들면 재사용 이점을 잃을 수 있다. 연결 한도·프록시·TLS 설정을 변경한다면 사용 라이브러리와 버전에 맞춰 검증한다.

외부 응답도 신뢰할 수 없는 입력이다. JSON 스키마·크기·허용 필드를 검증하고 민감한 응답을 로그에 그대로 기록하지 않는다. 임의 URL을 받는 기능에는 19장의 SSRF 경계도 적용한다.

## 실습과 관찰

`test/http.test.mjs`는 로컬 성공 응답·404·이미 취소된 신호를 검사한다. 인터넷 공개 API에 기대지 않아 오프라인에서도 대상 동작을 통제할 수 있다. 별도로 느린 응답 서버를 만들어 본문이 지연될 때의 기한도 실험할 수 있다.

현재 함수는 자동 재시도를 구현하지 않았다. 업무별 안전성을 확인한 뒤 감싸는 계층에 정책을 추가한다. 이미 시작한 작업의 수명이 남지 않는지도 검증한다.

## 확인 문제

타임아웃 예외를 받았으므로 상대 서버의 작업도 취소되었다고 판단해도 되는가?

[해설 보기](../appendices/answers.md#장-21)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Global objects | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/globals.html)
- [Using the Fetch API with Undici in Node.js | Node.js Learn](https://nodejs.org/en/learn/getting-started/fetch)
- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after)

---

[이전 장](../20-redis-cache/chapter.md) · [책 목차](../index.md) · [다음 장](../22-job-queue/chapter.md)
