---
title: "18장. 인증과 인가 구현하기"
description: "비밀번호·세션 토큰의 저장과 검증을 구분한다. 인증 이후에도 자원 소유권을 확인한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 18
part: 4
enableToc: true
---

# 18장. 인증과 인가 구현하기

## 학습 목표

- 비밀번호·세션 토큰의 저장과 검증을 구분한다.
- 인증 이후에도 자원 소유권을 확인한다.

## 로그인했다는 사실과 접근 권한

인증은 요청자가 누구인지 확인하는 과정이다. 인가는 그 사용자가 특정 작업을 볼 수 있는지 판단한다. 유효한 토큰이 있어도 다른 사용자의 작업 결과를 볼 수 있어서는 안 된다. 종합 프로젝트의 조회와 SSE 경로는 모두 작업 ownerId와 세션 userId를 비교한다.

사용자 ID를 요청 본문에서 받아 소유자로 저장하면 공격자가 다른 사용자를 지정할 수 있다. 인증 세션에서 사용자 ID를 가져오고, 작업 ID 형식 검사와 소유권 검사를 별도로 수행한다.

## 비밀번호는 빠른 해시만으로 저장하지 않는다

비밀번호는 복호화해 돌려줄 필요가 없다. 개별 salt와 비밀번호 해싱용 KDF를 사용한다. 예제는 Node.js 내장 비동기 scrypt를 사용하고 `scrypt-v1`이라는 형식 버전을 둔다. N=32768, r=8, p=3, maxmem=64MiB로 지정하며 동시에 수행하는 KDF를 2개로 제한한다. 이는 예제의 자원 예산이며 실제 서버에서 비용을 측정하고 최신 보안 지침을 확인해야 한다.

비동기 KDF는 이벤트 루프를 직접 막는 동기 호출보다 낫지만 CPU·메모리·libuv 작업 풀을 사용한다. 로그인 폭주에 대한 요청 제한과 동시성 제한이 함께 필요하다. 비밀번호 바이트 수 상한은 처리 비용과 입력 계약을 명확하게 한다.

저장 문자열에는 salt와 KDF 결과가 들어간다. 비교에는 길이를 확인한 뒤 `timingSafeEqual`을 사용한다. 이런 비교 하나만으로 로그인 전체가 일정 시간에 실행된다고 주장하지 않는다. 미존재 이메일에도 KDF를 실행해 큰 차이를 줄이지만 조회·네트워크·분기 차이는 여전히 존재한다.

## 불투명 세션 토큰

로그인 성공 시 32바이트 난수를 base64url로 인코딩해 토큰으로 발급한다. DB에는 원문 대신 SHA-256 해시와 사용자 ID·만료 시각을 저장한다. 비밀번호는 추측 가능한 값이므로 느린 KDF가 필요하지만, 충분히 긴 난수 토큰은 다른 위협 모델을 갖는다.

```text
클라이언트: Authorization: Bearer <원문 토큰>
서버: 토큰 해시 계산 → 세션 조회 → 만료 검사 → 사용자 식별
로그아웃: 세션 해시 행 삭제
```

이 설계는 JWT를 필수로 사용하지 않는다. JWT도 서명 검증·알고리즘 제한·발급자·대상·만료 검사와 폐기 정책이 필요하다. 형식 이름이 보안을 보장하지 않는다. 선택은 즉시 폐기, 다중 서비스 검증, 저장소 가용성 등 요구사항에 따른다.

## 토큰 전달과 서비스 경계

예제는 API 클라이언트의 Authorization 헤더를 사용한다. 브라우저 앱이라면 XSS와 CSRF 모델을 검토해 HttpOnly·Secure·SameSite 쿠키 등을 선택한다. 토큰을 URL 쿼리에 넣으면 로그·방문 기록·공유 링크에 남기 쉽다. 운영 외부 통신은 TLS를 사용하며 토큰과 비밀번호를 로그에 기록하지 않는다.

학습 예제에는 이메일 확인·비밀번호 재설정·다중 인증·계정 복구를 구현하지 않았다. 계정 시스템을 공개 서비스로 확장할 때는 이 흐름과 만료 세션 정리도 설계해야 한다.

## 실습과 관찰

`src/security.mjs`에서 같은 비밀번호도 매번 다른 salt로 다른 해시가 만들어지는지 테스트한다. HTTP 테스트는 등록·로그인·다른 사용자 접근·로그아웃 후 거부를 연결한다.

로그를 보고 비밀번호·Authorization 헤더·이메일이 그대로 찍히지 않는지 확인한다. 응답으로 받은 토큰도 예제 결과나 PR 본문에 붙여 넣지 않는다.

## 확인 문제

JWT를 쓰지 않고 DB 세션을 쓰면 인증 설계가 오래된 방식인가?

[해설 보기](../appendices/answers.md#장-18)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Crypto | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/crypto.html)
- [Password Storage - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Session Management - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

---

[이전 장](../17-transactions/chapter.md) · [책 목차](../index.md) · [다음 장](../19-web-security/chapter.md)
