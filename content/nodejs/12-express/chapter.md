---
title: "12장. Express로 웹 애플리케이션 구성하기"
description: "미들웨어 실행 순서와 오류 경로를 설계한다. 앱 구성과 포트 열기를 분리한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 12
part: 3
enableToc: true
---

# 12장. Express로 웹 애플리케이션 구성하기

## 학습 목표

- 미들웨어 실행 순서와 오류 경로를 설계한다.
- 앱 구성과 포트 열기를 분리한다.

## 반복되는 HTTP 처리 묶기

Express는 라우팅·파라미터·미들웨어·응답 유틸리티를 제공한다. HTTP의 동작을 바꾸는 마법이 아니라 공통 코드를 정리하는 도구다. 이 책은 Express 5를 사용한다. 의존성의 실제 패치 버전은 잠금 파일과 검증 안내에서 확인한다.

```js
import express from 'express';
export function makeApp() {
  const app = express();
  app.use(express.json({ limit: '8kb' }));
  app.get('/hello', (req, res) => res.json({ message: 'hello' }));
  app.use((req, res) => res.status(404).json({ error: 'NOT_FOUND' }));
  return app;
}
```

앞선 미들웨어가 응답을 끝내면 뒤의 라우터가 실행되지 않을 수 있다. `next()`를 호출하면 다음 단계로 넘기고, 오류를 넘기면 오류 처리 경로로 이동한다. 응답을 보낸 뒤 또 `next()`를 호출하면 중복 응답 원인이 된다.

## 요청별 문맥과 공통 정책

종합 프로젝트는 먼저 요청 ID와 보안 응답 헤더를 설정한다. 그 뒤 헬스 체크, 종료 중 신규 요청 차단, JSON 파싱, 인증 시도 제한, 실제 라우터를 등록한다. 마지막에 404와 오류 처리기를 둔다. 같은 미들웨어라도 순서가 달라지면 보호 범위가 달라진다.

JSON 파서는 `application/json` 본문을 처리한다. 원시 파일 업로드는 다른 Content-Type을 사용하므로 파일 스트림을 별도로 처리한다. `express.json()`을 모든 업로드 파서로 생각하면 멀티파트나 바이너리 데이터를 잘못 처리하게 된다.

## Express 5의 비동기 오류

Express 5는 라우트·미들웨어가 반환한 Promise의 거부를 오류 처리로 연결한다. 그러나 반환하지 않은 별도 Promise, 나중에 실행되는 타이머 콜백의 예외까지 자동으로 모두 수집하지는 않는다. 기다려야 하는 작업은 `await`하거나 반환해 핸들러의 수명에 연결한다.

```js
app.use((error, req, res, next) => {
  if (res.headersSent) return next(error);
  res.status(500).json({ error: 'INTERNAL_ERROR' });
});
```

오류 미들웨어는 네 인자를 유지한다. 응답을 이미 보낸 경우에는 기본 오류 처리기로 넘긴다. 운영 응답에 스택·SQL·비밀정보를 넣지 않으면서 요청 ID로 내부 기록과 연결한다.

## 테스트할 수 있는 구성 함수

`createApp({ repo, queue, root })`는 의존성을 전달받아 앱을 만든다. `main.mjs`가 런타임 설정을 읽고 실제 포트를 연다. 이 구조에서는 테스트가 임시 저장소와 임시 포트를 사용할 수 있다. 폴더를 여러 계층으로 나누기 전에 외부 자원 생성과 요청 처리를 분리하는 것이 먼저다.

정적 파일은 공개할 폴더만 지정한다. 프로젝트 루트 전체를 공개하면 설정·소스·업로드가 의도치 않게 노출될 수 있다. 인증이 필요한 사용자 파일은 소유권을 검사한 별도 경로를 통해 제공해야 한다.

## 실습과 관찰

`npm start`로 메모리 모드 서버를 실행하고 다른 터미널에서 `npm run smoke`를 실행한다. 서버 종료는 Ctrl+C다. `src/app.mjs`에서 미들웨어 순서를 실제로 따라가 보자.

테스트의 readiness 오류 응답을 확인하면 내부 예외 메시지를 수신자에게 그대로 보내지 않는다는 것을 볼 수 있다. 보호된 업로드·작업 경로와 공개 헬스 체크의 경계도 비교한다.

## 확인 문제

async 함수 안에서 시작한 Promise를 반환하지 않았다. 그 Promise의 실패를 Express 5가 항상 처리하는가?

[해설 보기](../appendices/answers.md#장-12)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Error Handling · Express.js](https://expressjs.com/en/guide/error-handling/)
- [Using middleware · Express.js](https://expressjs.com/en/guide/using-middleware.html)
- [5.x API Reference · Express.js 5.x](https://expressjs.com/en/5x/api.html)

---

[이전 장](../11-http/chapter.md) · [책 목차](../index.md) · [다음 장](../13-rest-api/chapter.md)
