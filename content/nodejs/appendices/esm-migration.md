---
title: "CommonJS에서 ESM으로"
description: "기존 프로젝트의 모듈 경계를 점진적으로 옮깁니다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# CommonJS에서 ESM으로

## 먼저 분류한다

진입점·테스트·설정 도구·의존성의 모듈 지원을 확인한다. package.json의 type을 한 번 바꾸면 같은 패키지 범위의 .js 해석이 달라질 수 있다. 일부 파일을 .mjs로 옮기고 CommonJS로 남길 파일을 .cjs로 명시하는 방식으로 경계를 작게 만든다.

## 바뀌는 문법과 경로

`require`를 `import`, `module.exports`를 `export`로 바꾸되 단순 문자열 치환으로 끝내지 않는다. 상대 import의 확장자, 동적 import의 비동기성, __dirname 대체, 모듈 최상위 부수 효과와 순환 참조를 확인한다. 모듈 옆 자료는 new URL('./data.json', import.meta.url)로 다룰 수 있고 경로 문자열이 필요하면 fileURLToPath를 사용한다.

CommonJS 모듈을 가져올 때는 기본 import로 module.exports를 받은 뒤 속성을 사용하는 방법이 분명하다. 이름 있는 내보내기 추론을 모든 패키지에 기대하지 않는다. 반대 방향의 ESM 로딩은 런타임 버전·top-level await 등 제약을 확인한다.

## 검증 순서

1. 현재 동작과 시작·종료 테스트를 고정한다.
2. 한 경계씩 변환하고 테스트·CLI·설정 파일을 검사한다.
3. 순환 참조와 초기화 순서를 확인한다.
4. 패키지라면 외부 소비자용 ESM·CommonJS 샘플에서 각각 검증한다.
5. 지원 Node.js 범위와 변경된 공개 진입점을 기록한다.

캐시 초기화를 위해 매번 다른 query가 붙은 import URL을 만드는 식의 우회는 모듈 인스턴스와 메모리를 늘릴 수 있다. 테스트 가능성을 위해 자원 생성 함수를 분리하는 편이 소유권을 명확하게 한다.

[공식 ESM 문서](https://nodejs.org/docs/latest-v24.x/api/esm.html) · [패키지 문서](https://nodejs.org/docs/latest-v24.x/api/packages.html)
