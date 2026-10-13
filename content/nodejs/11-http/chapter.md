---
title: "11장. 내장 HTTP 모듈로 서버 만들기"
description: "요청과 응답을 바이트 스트림으로 이해한다. 라우팅·본문·연결의 수명을 구분한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 11
part: 3
enableToc: true
---

# 11장. 내장 HTTP 모듈로 서버 만들기

## 학습 목표

- 요청과 응답을 바이트 스트림으로 이해한다.
- 라우팅·본문·연결의 수명을 구분한다.

## HTTP 요청의 구성

클라이언트는 메서드·대상 경로·헤더·선택적인 본문을 보낸다. 서버는 상태 코드·헤더·본문을 반환한다. TCP 청크 하나가 HTTP 본문 하나이거나 JSON 객체 하나라는 보장은 없다. Node.js가 HTTP 메시지를 해석한 뒤에도 애플리케이션은 본문의 형식과 크기를 검증해야 한다.

`IncomingMessage`는 읽을 수 있는 스트림이고 `ServerResponse`는 응답 쓰기 인터페이스다. 요청 헤더가 도착해 핸들러가 호출되었다고 본문 전체가 이미 수신되었다는 뜻은 아니다. 업로드의 크기 제한과 연결 중단 처리는 이 차이에서 출발한다.

```js
import { createServer } from 'node:http';
import { once } from 'node:events';
const server = createServer((req, res) => {
  if (req.method !== 'GET' || req.url !== '/hello') { res.writeHead(404).end(); return; }
  const data = Buffer.from(JSON.stringify({ message: '안녕' }));
  res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': data.length });
  res.end(data);
});
server.listen(0, '127.0.0.1'); await once(server, 'listening');
try { const r = await fetch(`http://127.0.0.1:${server.address().port}/hello`); console.log(r.status, await r.json()); }
finally { await new Promise(resolve => server.close(resolve)); }
```

[실행 파일](../examples/fundamentals/11-http.mjs)

이 예제는 운영 서버처럼 계속 실행하지 않고 로컬 임시 포트에서 자신에게 요청을 보낸 뒤 종료한다. 테스트가 고정 포트를 서로 차지하지 않게 운영체제에 포트 0을 요청한다. `listening` 이벤트를 기다린 뒤 요청하므로 시작 시점의 경쟁도 피한다.

## 라우팅과 본문 직렬화

메서드와 경로는 함께 확인한다. 읽기 API와 삭제 API가 같은 경로를 사용할 수도 있다. 쿼리 문자열이 있으면 `new URL(req.url, 'http://localhost')`처럼 경로와 검색 인자를 분리한다. 외부 공개 URL을 만들 때는 신뢰할 수 없는 Host 헤더를 그대로 기준으로 사용하지 않는다.

객체를 JSON 문자열로 바꾼 뒤 Buffer를 만들면 응답 바이트 수를 알 수 있다. `Content-Type`은 수신자가 해석할 형식이고 `Content-Length`는 전송 바이트 수다. 모든 응답에 길이를 미리 알아야 하는 것은 아니며 스트리밍 응답에서는 다른 전송 방식이 사용된다.

응답 헤더를 보낸 뒤에는 다른 상태 코드와 JSON 오류 본문으로 바꾸기 어렵다. 두 경로가 동시에 `res.end()`를 호출하지 않도록 반환 흐름을 정리한다. 성공·입력 오류·내부 오류마다 누가 응답을 끝내는지 명확해야 한다.

## 연결 재사용과 타임아웃

요청 한 건과 소켓 한 개의 수명은 같지 않다. 연결을 재사용하면 매번 연결을 만드는 비용을 줄일 수 있지만 유휴 연결·느린 헤더·끝나지 않는 본문을 제한해야 한다. `headersTimeout`, `requestTimeout`, keep-alive 설정의 목적과 단위는 서로 다르다.

DB 쿼리가 끝나지 않는 문제를 HTTP 수신 타임아웃 하나로 해결할 수도 없다. 요청 수신 기한, 애플리케이션 작업 기한, 외부 호출 기한을 각각 설정하고 종료 신호를 전달한다. 일부 timeout 이벤트는 자동으로 모든 작업을 취소하지 않는다. 해당 API의 동작을 확인한다.

## 실습과 관찰

`node fundamentals/11-http.mjs`를 실행한다. `200`과 한글 메시지가 출력되고 프로세스가 종료되어야 한다. `/hello` 대신 없는 경로를 요청하도록 바꾼 경우 404를 확인한다.

종합 프로젝트의 `src/main.mjs`에서는 HTTP 서버와 Express 앱을 연결한다. 라이브러리를 도입해도 연결·헤더·본문의 수명은 계속 고려해야 한다.

## 확인 문제

응답을 일부 스트리밍한 뒤 오류가 났다. 500 JSON을 새로 보내도 되는가?

[해설 보기](../appendices/answers.md#장-11)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [HTTP | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/http.html)
- [Anatomy of an HTTP Transaction | Node.js Learn](https://nodejs.org/en/learn/http/anatomy-of-an-http-transaction)

---

[이전 장](../10-streams/chapter.md) · [책 목차](../index.md) · [다음 장](../12-express/chapter.md)
