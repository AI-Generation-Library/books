---
title: "09장. Buffer와 이벤트 기반 프로그래밍"
description: "문자열 길이·바이트 수·사용자가 보는 글자 수를 구분한다. EventEmitter 리스너의 실행 방식과 수명을 관리한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 9
part: 2
enableToc: true
---

# 09장. Buffer와 이벤트 기반 프로그래밍

## 학습 목표

- 문자열 길이·바이트 수·사용자가 보는 글자 수를 구분한다.
- EventEmitter 리스너의 실행 방식과 수명을 관리한다.

## 문자열과 바이트는 다르다

HTTP·파일·소켓은 바이트를 전달한다. JavaScript 문자열의 `length`는 UTF-16 코드 단위 수이므로 UTF-8 파일의 바이트 수와 같지 않다. 이모지는 여러 코드 단위를 사용하기도 하고, 사람이 한 글자로 보는 조합 문자는 여러 코드포인트일 수 있다. 어떤 길이를 제한하거나 세는지 먼저 정의해야 한다.

```js
import { EventEmitter } from 'node:events';
const b = Buffer.from('노드');
console.log('노드'.length, b.length); // 2 6
const bus = new EventEmitter();
bus.once('done', value => console.log(value));
bus.emit('done', 'first'); bus.emit('done', 'ignored');
```

[실행 파일](../examples/fundamentals/09-buffer-events.mjs)

`Buffer.from('노드')`는 UTF-8 기본 인코딩으로 바이트를 만든다. 문자열 길이는 2, 바이트 수는 6이다. HTTP `Content-Length`에는 문자열 길이가 아닌 바이트 수를 사용한다. 종합 프로젝트의 `characters`는 Unicode 코드포인트 수이며 화면상의 글자 묶음 수가 아니다.

## 청크를 독립 문자열로 바꾸면 생기는 문제

스트림의 청크 경계는 문자 경계와 일치하지 않을 수 있다. 한글의 UTF-8 바이트가 두 청크에 나뉘면 각 청크를 따로 `toString()` 하는 코드에서 대체 문자가 생길 수 있다. `TextDecoder`의 스트리밍 모드나 `StringDecoder`, 적절한 스트림 인코딩을 사용해 남은 바이트를 이어 붙인다.

종합 프로젝트는 `TextDecoder('utf-8', { fatal: true })`로 잘못된 UTF-8을 오류로 처리한다. 마지막에 `decode()`를 한 번 더 호출해 미완성 바이트가 남았는지 검사한다. 입력이 텍스트라는 계약을 조용한 문자 치환으로 우회하지 않기 위해서다.

`Buffer.alloc`은 초기화된 버퍼를 만든다. `allocUnsafe`는 이름처럼 이전 메모리 내용이 남을 수 있으므로 읽기 전에 전체를 채워야 한다. 단순한 애플리케이션 코드에서는 안전한 기본값을 택하고 실제 병목이 확인된 경우에만 최적화를 검토한다.

## 이벤트는 자동 병렬 실행이 아니다

`EventEmitter.emit()`은 등록된 일반 리스너를 동기적으로 호출한다. 리스너가 긴 계산을 하면 발행자도 기다린다. 리스너가 `async` 함수라면 반환 Promise를 emitter가 일반 함수 호출처럼 모두 기다려 주는 것도 아니다. 비동기 실패 경로를 명시적으로 연결해야 한다.

`on`은 계속 유지되고 `once`는 한 번 호출 후 제거된다. 연결마다 리스너를 등록했다면 연결 종료 시 제거한다. 리스너 개수 경고가 나왔을 때 상한만 올리면 누수 원인을 숨길 수 있다. 어떤 객체가 리스너와 그 클로저를 참조하는지 추적한다.

`error` 이벤트는 특별하다. 일반적인 EventEmitter에서 처리 리스너 없이 발생하면 예외로 이어질 수 있다. 스트림·연결·워커처럼 오류 이벤트를 내보내는 객체는 생성 직후 오류 처리 경로를 갖추고, 성공 경로뿐 아니라 종료와 실패 때도 리스너를 정리한다.

## 실습과 관찰

`node fundamentals/09-buffer-events.mjs`를 실행해 이벤트가 한 번만 처리되는지 확인한다. `test/core.test.mjs`에서는 한글·이모지 입력을 한 바이트씩 나누어 업로드한 뒤 결과를 검증한다. 실제 네트워크 청크 크기에 기대지 않고 가장 까다로운 경계를 직접 만든 테스트다.

`'🙂'.length`, `[...'🙂'].length`, `Buffer.byteLength('🙂')`를 비교해 각각 2·1·4라는 차이를 확인한다.

## 확인 문제

파일의 characters가 화면에서 보이는 글자 수와 달랐다. 반드시 버그인가?

[해설 보기](../appendices/answers.md#장-09)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Buffer | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/buffer.html)
- [Events | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/events.html)
- [Util | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/util.html)

---

[이전 장](../08-filesystem/chapter.md) · [책 목차](../index.md) · [다음 장](../10-streams/chapter.md)
