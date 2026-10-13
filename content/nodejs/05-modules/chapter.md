---
title: "05장. 모듈 시스템 제대로 이해하기"
description: "ESM과 CommonJS의 로딩 방식과 경계를 이해한다. 파일 위치와 공개 패키지 진입점을 명시한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 5
part: 1
enableToc: true
---

# 05장. 모듈 시스템 제대로 이해하기

## 학습 목표

- ESM과 CommonJS의 로딩 방식과 경계를 이해한다.
- 파일 위치와 공개 패키지 진입점을 명시한다.

## 두 모듈 시스템

CommonJS는 `require()`와 `module.exports`를, ESM은 `import`와 `export`를 사용한다. 기존 패키지와 코드를 읽으려면 둘 다 알아야 한다. 새 예제는 ESM을 기준으로 작성한다. `.mjs`는 ESM, `.cjs`는 CommonJS로 해석되며 `.js`는 가까운 `package.json`의 `type` 등 모듈 해석 규칙의 영향을 받는다. 의도를 명시하면 실행 환경에 따른 혼동을 줄일 수 있다.

ESM의 상대 경로 import에는 실제 파일 확장자를 적는다. 브라우저 번들러가 확장자 생략을 허용했다고 Node.js의 기본 로더도 동일하게 동작한다고 가정하지 않는다. 내장 모듈은 `node:fs`처럼 `node:` 접두사를 사용해 외부 패키지와 구분한다.

```js
import legacy from './05-legacy.cjs';
console.log(legacy.add(2, 3));
console.log(new URL('./05-legacy.cjs', import.meta.url).protocol);
```

[실행 파일](../examples/fundamentals/05-modules.mjs)

이 예제에서 가져오는 CommonJS 파일은 다음과 같다.

```js
module.exports = { add: (a, b) => a + b };
```

[실행 파일](../examples/fundamentals/05-legacy.cjs)

CommonJS의 `module.exports`를 ESM에서 가져올 때 기본 import를 사용하면 전체 내보내기 값을 받을 수 있다. CommonJS의 이름 있는 내보내기 추론에는 제약이 있으므로 모든 속성이 항상 named import로 제공된다고 믿지 않는다. 최신 Node.js에는 일부 ESM을 `require`하는 기능도 있지만 top-level await 등 제약이 있다. 이 책은 상호 운용 경계를 단순하게 유지한다.

## 로딩, 캐시와 부수 효과

같은 모듈을 여러 번 가져온다고 매번 독립 인스턴스가 만들어지는 것은 아니다. 모듈 최상위에서 DB 연결을 생성하면 테스트에서도 import만으로 연결이 시작될 수 있다. 외부 자원 생성은 명시적인 팩터리나 시작 함수에 두면 대체·종료·오류 처리가 쉬워진다.

순환 참조가 있는 두 모듈이 서로 초기화 완료를 기대하면 부분 초기화 상태나 초기화 전 접근 문제가 발생한다. `app → service → repository`처럼 방향을 두고 공통 타입·정책을 별도 모듈로 분리한다. 폴더를 나누는 것만으로 순환이 사라지지는 않는다.

## 파일 기준 경로와 패키지 경계

ESM에서 모듈 옆 파일은 `new URL('./config.json', import.meta.url)`로 지정할 수 있다. 파일 URL을 운영체제 경로로 바꿔야 할 때는 `fileURLToPath`를 쓴다. URL의 `pathname`을 그대로 Windows 경로로 쓰면 드라이브 문자와 URL 인코딩 때문에 잘못될 수 있다.

패키지를 배포한다면 `exports`로 외부에 공개할 진입점을 정의한다. 내부 파일 경로에 소비자가 직접 의존하면 리팩터링이 호환성 문제로 번진다. ESM과 CommonJS 양쪽 진입점을 제공하는 패키지는 각각의 동작과 상태 공유 문제를 검증해야 한다. 배포 절차는 부록에서 다룬다.

## 실습과 관찰

`node fundamentals/05-modules.mjs`를 실행하면 `5`와 `file:`이 출력된다. import 경로에서 `.cjs`를 제거해 실패를 관찰한 뒤 원상 복구한다. 실행 위치를 바꾸더라도 모듈 기준 URL이 같은 파일을 가리키는지 확인한다.

종합 프로젝트의 `createApp()`과 `runtime()`을 찾아 어떤 함수가 단순 앱 구성을 하고 어떤 함수가 외부 자원을 여는지 비교한다.

## 확인 문제

테스트를 위해 서비스 모듈을 import했는데 실제 DB에 연결된다. 모듈 구조를 어떻게 바꾸는가?

[해설 보기](../appendices/answers.md#장-05)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Modules: ECMAScript modules | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/esm.html)
- [Modules: CommonJS modules | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/modules.html)
- [Modules: Packages | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/packages.html)

---

[이전 장](../04-npm-project/chapter.md) · [책 목차](../index.md) · [다음 장](../06-async/chapter.md)
