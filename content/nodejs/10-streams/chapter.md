---
title: "10장. Stream과 백프레셔"
description: "큰 데이터를 제한된 메모리로 전달한다. 전송 흐름·오류·부분 파일 정리를 함께 설계한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 10
part: 2
enableToc: true
---

# 10장. Stream과 백프레셔

## 학습 목표

- 큰 데이터를 제한된 메모리로 전달한다.
- 전송 흐름·오류·부분 파일 정리를 함께 설계한다.

## 전체 읽기와 스트리밍

1GB 파일을 `readFile()`로 읽으면 파일 크기만큼의 메모리와 이후 변환 비용을 고려해야 한다. 동시에 여러 사용자가 요청하면 사용량이 요청 수에 따라 커진다. 스트림은 데이터를 청크로 읽고 처리하며 다음 단계에 전달한다. 데이터를 반드시 전부 보관해야 하는 알고리즘이라면 스트림 API를 쓴다고 메모리 사용이 자동으로 작아지지는 않는다.

Readable은 데이터를 내보내고 Writable은 받아 쓴다. Transform은 읽고 쓰는 양쪽 역할을 하며 변환을 수행한다. 압축·해시·크기 제한처럼 청크마다 처리할 수 있는 작업을 연결하기 좋다.

```js
import { createReadStream, createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
const [source, destination] = process.argv.slice(2);
if (!source || !destination) {
  console.error('Usage: node fundamentals/10-copy-cli.mjs source destination'); process.exitCode = 2;
} else {
  try { await pipeline(createReadStream(source), createWriteStream(destination, { flags: 'wx' })); console.log('copied'); }
  catch (error) { console.error(error.code || error.name); process.exitCode = 1; }
}
// 실패 시 부분 파일이 남을 수 있다. 운영용 업로드 구현의 정리 방식은 src/files.mjs를 참고한다.
```

[실행 파일](../examples/fundamentals/10-copy-cli.mjs)

이 파일은 원본을 대상에 복사하는 최소 CLI다. 대상이 이미 있으면 덮어쓰지 않는다. 이 짧은 예제는 실패 시 부분 파일을 남길 수 있음을 코드에 명시했다. 종합 프로젝트의 업로드 함수는 자신이 만든 파일을 실패 시 제거한다.

## 느린 소비자가 흐름을 제어하게 하기

쓰기 버퍼가 계속 커지면 스트리밍의 이점이 사라진다. `writable.write(chunk)`가 `false`를 반환하면 생산자는 `drain` 등 적절한 신호를 기다려야 한다. `false`는 그 청크가 거부되었다는 뜻이 아니라 추가 쓰기 전에 기다리라는 신호다. 같은 청크를 다시 쓰면 중복 데이터가 될 수 있다.

`highWaterMark`는 내부 버퍼링의 기준이며 전체 프로세스 메모리의 절대 상한이 아니다. 여러 스트림·요청·변환 단계가 각각 버퍼를 가지며 커널과 라이브러리도 메모리를 사용한다. 데이터 크기 제한과 동시 요청 제한을 별도로 둬야 한다.

## pipeline으로 성공과 실패 연결

`node:stream/promises`의 `pipeline`은 연결된 스트림의 완료를 기다리고 오류를 Promise 거부로 전달한다. 중간 단계가 실패하면 관련 스트림이 파괴될 수 있다. 요청 소켓을 pipeline에 직접 넣은 경우 클라이언트가 JSON 오류 응답 대신 연결 종료를 관찰할 수도 있다. HTTP 응답을 보낼 수 있는 시점과 전송 중단을 구분해야 한다.

종합 프로젝트는 `Content-Length`가 이미 한도를 넘으면 스트리밍 전에 413을 반환한다. 헤더가 없거나 실제 전송량이 다를 수도 있으므로 Transform에서 실제 바이트 수도 센다. 스트리밍 중 한도 초과 때는 연결 중단과 서버 측 파일 정리까지 검증해야 한다.

## 자원 정리와 경계 입력

수신 취소·디스크 부족·중간 변환 오류·잘못된 UTF-8·빈 파일을 각각 생각한다. 파일을 만들었다면 실패 시 누가 지우는지, 성공 파일은 언제 삭제하는지 정한다. `try/finally`를 넣는 것만으로 다른 자원인 DB의 상태까지 원복되지는 않는다. 24장에서는 이런 경계를 API 수준으로 확장한다.

## 실습과 관찰

예제 디렉터리에서 원본이 있는 경로와 새 대상 경로를 직접 지정한다.

```sh
node fundamentals/10-copy-cli.mjs fundamentals/01-runtime.mjs copy-result.mjs
```

첫 실행은 `copied`, 같은 대상에 재실행하면 `EEXIST`와 실패 종료 코드를 반환한다. 결과 파일은 실습 후 직접 확인하고 제거한다. `npm test`에서는 임시 디렉터리를 사용하므로 실습 원본을 변경하지 않는다.

`src/files.mjs`의 제한 Transform과 `test/core.test.mjs`의 부분 파일 제거 테스트를 함께 읽는다.

## 확인 문제

write()가 false를 반환해 같은 청크를 다시 write했다. 어떤 문제가 생길 수 있는가?

[해설 보기](../appendices/answers.md#장-10)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Stream | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/stream.html)
- [Backpressuring in Streams | Node.js Learn](https://nodejs.org/en/learn/modules/backpressuring-in-streams)

---

[이전 장](../09-buffer-events/chapter.md) · [책 목차](../index.md) · [다음 장](../11-http/chapter.md)
