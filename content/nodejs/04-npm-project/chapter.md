---
title: "04장. npm과 프로젝트의 기본 구조"
description: "직접 의존성과 개발 의존성, 잠금 파일의 역할을 구분한다. 동일한 의존성 트리로 설치하고 실행 명령을 공유한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 4
part: 1
enableToc: true
---

# 04장. npm과 프로젝트의 기본 구조

## 학습 목표

- 직접 의존성과 개발 의존성, 잠금 파일의 역할을 구분한다.
- 동일한 의존성 트리로 설치하고 실행 명령을 공유한다.

## package.json은 프로젝트의 실행 계약

프로젝트 이름·버전·모듈 방식·지원 런타임·실행 명령·의존성을 한곳에 둔다. 종합 프로젝트는 `private: true`로 우발적인 npm 배포를 막고, `type: module`로 `.js`의 기본 모듈 해석을 명시한다. 실제 예제 파일은 `.mjs`를 사용하므로 파일 자체로 ESM임을 드러낸다.

```json
{
  "private": true,
  "type": "module",
  "engines": { "node": ">=24.18.0 <25" },
  "scripts": { "start": "node src/main.mjs", "test": "node --test test/*.test.mjs" }
}
```

소스는 `src`, 테스트는 `test`, DB 변경은 `migrations`, 보조 명령은 `scripts`에 두었다. 폴더 이름 자체가 정답이라기보다 다른 개발자가 코드를 찾는 비용과 의존 방향이 중요하다. 시작 파일에서 포트를 열고, 앱 구성 함수는 테스트가 직접 불러올 수 있도록 분리한다.

## 버전 범위와 잠금 파일

직접 의존성을 정확한 버전으로 지정해도 그 패키지가 다시 의존하는 패키지는 여러 개다. `package-lock.json`은 설치할 전체 트리와 무결성 정보를 기록한다. 팀과 CI가 같은 트리를 설치하려면 함께 커밋해야 한다. 운영체제별 선택적 의존성 같은 차이는 여전히 존재할 수 있다.

`npm install`은 의존성을 추가·변경할 때 사용한다. `npm ci`는 이미 작성된 잠금 파일에 맞춰 설치하며 `package.json`과 맞지 않으면 실패한다. 설치 디렉터리도 정리하므로 사용자가 수동으로 넣은 파일을 `node_modules`에 보관하면 안 된다. 소스 관리에는 의존성 디렉터리 대신 선언과 잠금 파일을 넣는다.

```sh
npm ci --ignore-scripts
npm test
npm run typecheck
```

## 실행 의존성과 개발 의존성

Express와 DB 드라이버는 애플리케이션 실행에 필요하다. TypeScript 컴파일러와 타입 정의는 이 예제에서는 검사에 쓰는 개발 의존성이다. 운영 이미지를 만들 때 `--omit=dev`로 제외할 수 있지만, TypeScript를 빌드하는 프로젝트라면 빌드 단계에서는 컴파일러가 필요하다. 빌드 단계와 실행 단계를 혼동하지 않는다.

`--ignore-scripts`는 설치 생명주기 스크립트를 실행하지 않게 한다. 이 책의 예제는 이 방식으로 설치·검증했다. 네이티브 확장 빌드 등 스크립트가 필요한 패키지를 도입하면 별도 검토해야 한다. 무조건 모든 프로젝트에 같은 옵션을 적용하면 필요한 생성 파일이 누락될 수 있다.

## 의존성 갱신도 코드 변경이다

취약점 보고는 영향 경로와 사용 기능을 확인하는 출발점이다. `npm audit`가 경고하지 않는다고 애플리케이션 보안이 증명되지는 않는다. 반대로 `npm audit fix --force`를 무작정 실행하면 호환되지 않는 변경이 들어올 수 있다. 작은 변경 단위로 갱신하고 테스트·배포·롤백 기록을 남긴다.

## 실습과 관찰

제공한 `examples/package.json`과 잠금 파일을 열어 직접 의존성과 전이 의존성을 비교한다. `npm ls --depth=0`으로 실제 설치된 직접 의존성을 확인한다. 버전은 [검증 기록](../appendices/verification.md)에 있는 값과 비교한다.

`npm run`을 실행하면 사용 가능한 스크립트가 표시된다. 한 번의 명령으로 테스트를 실행할 수 있는지 확인하고, 임의로 잠금 파일을 지우는 대신 변경 이유와 설치 결과를 추적한다.

## 확인 문제

package.json에 모든 직접 의존성을 고정했으므로 잠금 파일을 삭제해도 재현 가능한가?

[해설 보기](../appendices/answers.md#장-04)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [npm-ci | npm Docs](https://docs.npmjs.com/cli/v11/commands/npm-ci)
- [package.json | npm Docs](https://docs.npmjs.com/cli/v11/configuring-npm/package-json)
- [package-lock.json | npm Docs](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json)

---

[이전 장](../03-javascript/chapter.md) · [책 목차](../index.md) · [다음 장](../05-modules/chapter.md)
