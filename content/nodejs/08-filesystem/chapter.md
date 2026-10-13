---
title: "08장. 파일 시스템과 프로세스 다루기"
description: "모듈·작업 디렉터리·사용자 입력 경로를 구분한다. 파일과 프로세스 자원을 성공·실패 모두에서 정리한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 8
part: 2
enableToc: true
---

# 08장. 파일 시스템과 프로세스 다루기

## 학습 목표

- 모듈·작업 디렉터리·사용자 입력 경로를 구분한다.
- 파일과 프로세스 자원을 성공·실패 모두에서 정리한다.

## 파일 API 선택

`node:fs`에는 동기·콜백 API가 있고 `node:fs/promises`에는 Promise API가 있다. 시작 시 작은 설정을 읽는 코드와 요청마다 대용량 파일을 읽는 코드는 비용이 다르다. 서버 요청 경로의 동기 파일 I/O는 다른 요청의 JavaScript 실행도 지연시킬 수 있다. 비동기 API라고 파일 전체를 메모리에 올리는 비용까지 사라지지는 않는다.

```js
import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const directory = await mkdtemp(join(tmpdir(), 'nodebook-'));
try {
  const filename = join(directory, 'note.txt');
  await writeFile(filename, '안녕 Node.js\n', 'utf8');
  console.log((await readFile(filename, 'utf8')).trim());
} finally { await rm(directory, { recursive: true, force: true }); }
```

[실행 파일](../examples/fundamentals/08-files.mjs)

`mkdtemp`는 겹치지 않는 임시 디렉터리를 만들고 그 경로를 반환한다. 이 코드가 만든 디렉터리만 `finally`에서 제거한다. 재귀 삭제를 사용할 때는 입력받은 경로나 상위 디렉터리가 아니라 자신이 만든 한정된 경로인지 확인해야 한다. 운영 파일을 지우는 예제와 테스트의 임시 파일 정리를 혼동하지 않는다.

## 경로 문자열의 함정

경로 구분자는 플랫폼마다 다를 수 있으므로 일반 파일 경로는 `path.join`·`path.resolve`를 사용한다. 사용자 입력 파일명을 그대로 결합하면 `../`나 절대 경로로 의도한 디렉터리를 벗어날 수 있다. 저장 이름을 서버가 생성한 ID로 정하고 원래 파일명은 표시용 메타데이터로만 보관하는 방식이 단순하다.

문자열 수준의 경계 검사만으로 심볼릭 링크 공격까지 해결되지는 않는다. 업로드 디렉터리는 신뢰할 수 없는 사용자가 파일·링크를 직접 만들지 못하도록 권한을 제한한다. 종합 프로젝트는 UUID만 파일 식별자로 허용하고 해당 디렉터리를 애플리케이션이 관리한다.

## 존재 확인과 실제 열기 사이의 경쟁

먼저 파일이 없는지 확인한 뒤 쓰면 두 요청이 같은 확인을 통과할 수 있다. 덮어쓰면 안 되는 새 파일은 `flags: 'wx'`로 생성 단계에서 배타성을 요청한다. DB와 파일 시스템은 서로 다른 자원이므로 파일 쓰기 성공과 DB 커밋 성공을 하나의 원자적 동작으로 가정해서도 안 된다.

짧은 임시 파일에 완성본을 쓴 뒤 이름을 바꾸는 방식은 부분 파일 공개를 줄일 수 있다. 다만 파일 시스템과 마운트 경계, 크래시 후 복구 요구에 따라 보장이 달라진다. 실패 시 임시 파일과 고아 파일을 정리하는 정책도 필요하다.

## 프로세스 경계의 값

`process.argv`에는 실행 파일·스크립트·사용자 인자가 들어간다. `process.env`의 값은 문자열이므로 숫자 포트와 불리언을 명시적으로 파싱한다. `'false'`도 JavaScript의 조건식에서는 참이다. 잘못된 설정은 첫 요청이 올 때까지 숨기기보다 시작 단계에서 거부한다.

정상 완료는 종료 코드 0, 실패는 0이 아닌 종료 코드로 전달한다. `process.exitCode`를 지정하면 출력과 정리를 마칠 여지가 있다. 즉시 `process.exit()`를 부르면 진행 중 출력·I/O가 끝나기 전에 종료될 수 있어 최종 기한 초과 같은 제한된 경로에서만 사용한다.

## 실습과 관찰

`node fundamentals/08-files.mjs`를 실행해 한글이 정상적으로 저장·복원되는지 확인한다. 이어서 `src/files.mjs`의 UUID 검사·`wx` 플래그·실패 시 삭제를 읽는다.

운영 환경 변수의 예시는 `src/runtime.mjs`의 `config()`에 있다. `PORT=NaN`을 전달하는 테스트가 서버를 열기 전에 실패하는지 확인한다. 셸마다 환경 변수 설정 구문이 다르므로 [예제 안내](../examples/README.md)의 PowerShell 명령을 따른다.

## 확인 문제

파일이 없다는 것을 확인했으니 다음 쓰기에서 기존 파일을 덮어쓸 수 없다고 말할 수 있는가?

[해설 보기](../appendices/answers.md#장-08)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [File system | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/fs.html)
- [Path | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/path.html)
- [URL | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/url.html)

---

[이전 장](../07-event-loop/chapter.md) · [책 목차](../index.md) · [다음 장](../09-buffer-events/chapter.md)
