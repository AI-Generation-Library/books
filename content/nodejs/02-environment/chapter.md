---
title: "02장. 개발 환경과 첫 번째 프로그램"
description: "Node.js와 npm 버전을 확인하고 실행 위치를 구분한다. REPL·스크립트·디버거를 목적에 맞게 사용한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 2
part: 1
enableToc: true
---

# 02장. 개발 환경과 첫 번째 프로그램

## 학습 목표

- Node.js와 npm 버전을 확인하고 실행 위치를 구분한다.
- REPL·스크립트·디버거를 목적에 맞게 사용한다.

## 실습 기준 고정하기

이 책의 실행 확인 환경은 Windows와 Node.js 24.18.0, npm 11.16.0이다. 기술 설명은 Node.js 24 계열을 대상으로 한다. 최신 패치가 나왔다면 보안 수정과 의존성 호환성을 검토해 적용하고, 실제 사용한 버전을 기록한다. `engines` 필드는 지원 범위를 표현하지만 모든 npm 설정에서 설치를 강제로 막는 장치는 아니다.

공식 배포판 또는 공식 사이트에서 안내하는 버전 관리 도구를 사용한다. 팀에서 버전 관리 도구를 선택했다면 설정 파일도 저장소에 둔다. Node.js 실행 파일이 여러 개 설치되면 터미널의 PATH 순서에 따라 다른 버전이 실행될 수 있다. 설치 후에도 현재 터미널에서 확인해야 한다.

```sh
node --version
npm --version
node -p "process.execPath"
```

## REPL과 파일 실행

`node`만 입력하면 대화형 실행 환경인 REPL에 들어간다. 작은 표현식을 확인하기 좋지만 여러 파일의 모듈 관계나 실제 프로세스 시작 동작을 대신 검증하지는 않는다. `.exit`로 종료할 수 있다. 파일을 실행할 때는 해당 파일이 존재하는 위치와 현재 작업 디렉터리를 구분한다.

```sh
node -e "console.log(process.cwd())"
node fundamentals/03-javascript.mjs
```

`process.cwd()`는 명령을 시작한 디렉터리다. 모듈 파일 옆 자료를 열려면 현재 작업 디렉터리를 추측하기보다 `new URL('./data.json', import.meta.url)`처럼 모듈 위치를 기준으로 만든다. Docker의 `WORKDIR`, IDE의 실행 설정, 테스트 러너가 작업 디렉터리를 바꿀 수 있다.

## 개발 편의와 운영 실행 분리

짧은 수정 반복에는 `node --watch src/main.mjs`를 사용할 수 있다. 파일 변경 시 프로세스를 다시 시작하므로 메모리에 저장한 데이터가 사라진다. 종합 프로젝트의 메모리 모드도 같다. 개발용 재시작 기능을 영속성 기능으로 오해하지 않는다.

```sh
node --inspect-brk fundamentals/03-javascript.mjs
```

디버거를 연결해 첫 줄부터 멈추고, 중단점·지역 변수·호출 스택을 확인한다. 디버그 포트는 프로그램 제어 권한과 관련되므로 로컬에만 열고 외부에 노출하지 않는다. 로그를 추가하는 방법과 중단점으로 실행을 멈추는 방법은 서로 보완적이다. 타이밍 민감한 문제는 중단점 때문에 재현 양상이 달라질 수 있다.

## 오류 메시지 읽는 순서

명령 자체가 없으면 PATH와 설치를, 파일을 찾지 못하면 경로와 실행 위치를, 모듈을 찾지 못하면 설치·확장자·패키지 설정을 확인한다. `EADDRINUSE`는 보통 포트를 다른 프로세스가 점유했다는 뜻이다. 이유를 모르면서 관리자 권한으로 재실행하거나 보안 설정을 광범위하게 바꾸는 대신 실패 계층을 좁힌다.

## 실습과 관찰

먼저 [예제 안내](../examples/README.md)의 설치 절차를 수행한다. 그 뒤 `node fundamentals/01-runtime.mjs`를 책 폴더가 아닌 `examples`에서 실행한다. 다음에는 상위 디렉터리로 이동해 같은 상대 경로 명령을 실행해 보자. 실패한다면 코드 문법보다 경로가 원인인지 확인한다.

디버거에서는 `03-javascript.mjs`의 두 번째 `next()` 호출 직전에 멈춰 클로저 변수 `n`을 확인한다. 터미널 종료와 프로그램 종료를 구분하고, 필요한 작업이 끝나면 디버그 프로세스도 정리한다.

## 확인 문제

IDE에서는 실행되지만 터미널에서는 설정 파일을 찾지 못한다. 가장 먼저 비교할 값은 무엇인가?

[해설 보기](../appendices/answers.md#장-02)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Command-line API | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/cli.html)
- [REPL | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/repl.html)
- [Node.js — Node.js Releases](https://nodejs.org/en/about/previous-releases)

---

[이전 장](../01-runtime/chapter.md) · [책 목차](../index.md) · [다음 장](../03-javascript/chapter.md)
