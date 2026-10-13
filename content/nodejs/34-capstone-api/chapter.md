---
title: "34장. 인증과 데이터 관리 API 구현"
description: "가입부터 세션 폐기까지 연결한다. 업로드 접수와 조회의 데이터 경계를 구현한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 34
part: 8
enableToc: true
---

# 34장. 인증과 데이터 관리 API 구현

## 학습 목표

- 가입부터 세션 폐기까지 연결한다.
- 업로드 접수와 조회의 데이터 경계를 구현한다.

## API를 조립하는 실제 파일

`src/app.mjs`가 HTTP 계약과 미들웨어를, `security.mjs`가 입력·비밀번호·토큰 정책을 맡는다. 저장소는 메모리와 PostgreSQL 두 구현이다. 실행 파일은 설정에 따라 자원을 만들고 앱에 전달한다. 테스트는 같은 앱 함수를 사용하면서 자원만 대체한다.

처음부터 모든 파일을 읽기보다 요청 하나의 흐름을 따른다. 가입은 자격 증명 검증 → salt와 KDF → 유니크 이메일 저장 → 공개 필드 응답 순서다. 로그인은 조회 → KDF 비교 → 무작위 세션 생성 → 해시 저장 → 원문 토큰 반환이다. 로그아웃은 인증한 세션 행을 삭제한다.

## 세션과 소유권

`authenticated` 미들웨어는 bearer 토큰 형식과 길이를 확인하고 해시로 세션을 조회한다. 만료된 세션은 허용하지 않는다. 클라이언트가 보낸 ownerId를 믿지 않고 세션의 userId로 새 작업의 소유자를 정한다.

작업 조회의 `owned()`는 ID 형식을 검사하고, 미존재와 타인 소유를 같은 404로 처리한다. 반환 객체는 id·state·result만 포함한다. DB의 password_hash나 내부 소유권 필드를 그대로 직렬화하지 않는다. SSE도 동일한 함수를 사용한다.

## 업로드 접수의 상태 전이

작업 행을 uploading으로 만든 뒤 파일을 저장하고 queued와 outbox를 기록한다. 파일 전송 실패 시 부분 파일을 지우고 작업을 failed로 바꾼다. DB 자체가 실패해 그 상태 변경도 실패할 수 있다는 점을 복구 설계에서 인정한다.

응답은 202와 Location이다. 분석 결과를 기다리지 않으므로 느린 worker가 HTTP 연결을 계속 붙잡지 않는다. 메모리 모드에서는 짧은 dispatcher 주기로 상태가 빠르게 진행될 수 있다. 서버가 반환한 상태보다 후속 GET 상태가 앞서 있어도 정상이다.

## PostgreSQL로 바꾸기

`npm run migrate`는 초기 전용 DB를 준비한다. 실제 저장소는 매개변수 쿼리와 유니크 제약을 사용하고 queued+outbox는 같은 client 트랜잭션으로 저장한다. 풀이 사용 중인 연결과 기다리는 요청을 관찰하고 모든 획득 경로에서 release를 보장한다.

메모리 테스트는 HTTP 정책과 상태 전이를 확인한다. PostgreSQL 오류 코드·트랜잭션·SQL 문법은 별도 실제 서비스 통합 검증 대상이다. 이번 환경에서 수행하지 못한 검사도 안내에 남겨 다음 기여자가 재현할 수 있게 한다.

## 테스트를 읽는 방법

정상 흐름 테스트는 가입 → 로그인 → 업로드 → 완료 조회 → SSE → 로그아웃 → 거부 순서다. 타인 접근 테스트는 별도 사용자 두 명을 만들고 두 조회 경로를 검사한다. 입력 실패 테스트는 JSON 문법·중복 이메일·잘못된 로그인·형식·크기·ID를 확인한다. 버그가 재발하면 해당 경계를 재현하는 테스트를 보강한다.

## 실습과 관찰

`npm start`와 다른 터미널의 `npm run smoke`를 실행한다. 반환 결과는 바이트 11·코드포인트 7·줄 2다. 입력 `안녕\nNode`의 UTF-8 바이트와 문자 수를 직접 계산해 결과의 의미를 확인한다.

토큰은 smoke 스크립트 내부에서만 사용하며 출력하지 않는다. 직접 HTTP 클라이언트로 실행할 때도 실제 토큰을 소스·스크린샷·PR에 저장하지 않는다.

## 확인 문제

사용자가 요청 본문에 ownerId를 보냈다. 타입이 UUID라면 그 값을 소유자로 저장해도 되는가?

[해설 보기](../appendices/answers.md#장-34)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Crypto | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/crypto.html)
- [5.x API Reference · Express.js 5.x](https://expressjs.com/en/5x/api.html)
- [GitHub](https://node-postgres.com/features/queries)

---

[이전 장](../33-capstone-design/chapter.md) · [책 목차](../index.md) · [다음 장](../35-capstone-worker/chapter.md)
