---
title: "19장. 웹 서비스의 보안 경계"
description: "입력·권한·브라우저 정책·서버 네트워크 경계를 구분한다. 요청 제한과 비밀정보 관리의 실제 적용 범위를 설명한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 19
part: 4
enableToc: true
---

# 19장. 웹 서비스의 보안 경계

## 학습 목표

- 입력·권한·브라우저 정책·서버 네트워크 경계를 구분한다.
- 요청 제한과 비밀정보 관리의 실제 적용 범위를 설명한다.

## 공격 표면을 요청 흐름에 표시하기

입력은 URL·헤더·본문·파일·외부 API 응답·메시지 큐 등 여러 경로로 들어온다. 경계마다 허용 형식·최대 크기·인증·실패 응답을 정한다. JSON 파서의 크기 제한이 파일 업로드나 외부 응답 크기까지 제한하지는 않는다.

SQL 값은 매개변수로 넘기고, HTML 출력은 출력 문맥에 맞게 인코딩한다. 사용자가 올린 HTML·SVG 등을 같은 출처에서 그대로 제공하면 저장형 XSS와 연결될 수 있다. 파일 확장자나 요청 Content-Type만으로 실제 파일의 안전성이 증명되지는 않는다.

## XSS, CSRF, CORS는 다른 문제

XSS는 신뢰할 수 없는 내용이 사용자 브라우저에서 실행되는 문제다. HttpOnly 쿠키는 JavaScript의 쿠키 읽기를 제한하지만 XSS가 사용자의 권한으로 요청을 보내는 모든 위험을 없애지는 않는다.

CSRF는 브라우저가 인증 수단을 자동 첨부하는 상황의 요청 위조와 관련된다. SameSite 쿠키, CSRF 토큰, 출처 검사 등 요구사항에 맞는 보호가 필요하다. CORS는 어떤 브라우저 출처가 응답을 읽을 수 있는지를 제어하는 정책이며 인증·인가나 서버 간 요청 차단을 대신하지 않는다.

## 서버가 대신 호출하는 URL

임의의 URL을 받아 `fetch`하면 내부 관리 API·클라우드 메타데이터 등에 접근하는 SSRF 문제가 생길 수 있다. 외부 연동 대상을 고정하거나 엄격히 허용하고, 리다이렉트·DNS 결과·네트워크 출구 정책을 함께 검토한다. 단순 문자열 접두사 비교는 완전한 URL 검증이 아니다.

종합 프로젝트는 임의 URL 다운로드 기능을 제공하지 않는다. 다른 기능을 추가할 때 입력 경계가 새로 열리는지 검토해야 한다.

## 요청 제한과 프록시 신뢰

예제의 인증 제한기는 메모리 기반이고 키 개수에도 상한이 있다. 서버를 여러 개 띄우면 인스턴스마다 제한이 따로 적용되므로 게이트웨이 또는 공유 저장소가 필요하다. 공격자별 제한뿐 아니라 전체 KDF·업로드·큐 용량도 제한해야 한다.

`X-Forwarded-For`는 신뢰하는 프록시가 관리할 때만 근거로 쓴다. Express의 `trust proxy`를 환경에 맞지 않게 켜면 IP 제한을 우회하거나 잘못된 URL·보안 판단으로 이어질 수 있다. 예제는 이를 무조건 활성화하지 않는다.

## 비밀정보와 운영 오류

비밀번호·토큰·접속 URL의 비밀번호를 로그에 넣지 않는다. `.env`를 커밋하지 않고, 운영에서는 비밀 저장소·권한·교체 절차를 갖춘다. 유출된 비밀을 Git에서 지우는 것만으로 이미 노출된 값이 무효화되지는 않는다. 해당 값을 폐기하고 교체해야 한다.

공개 오류 응답에는 안전한 코드와 요청 ID를, 내부 기록에는 진단에 필요한 제한된 정보를 남긴다. 디버그 포트·힙 스냅샷·코어 덤프는 실제 사용자 데이터와 비밀정보를 담을 수 있으므로 접근과 보관을 제한한다.

## 실습과 관찰

HTTP 테스트에서 잘못된 JSON, 과도한 인증 요청, 큰 업로드, 타인 작업 접근을 확인한다. 같은 정책이 SSE에도 적용되는지 본다.

운영 설계에는 계정별 저장 용량·동시 업로드·세션 만료 정리·분산 제한을 추가해야 한다. 예제의 경계와 미구현 기능은 [프로젝트 설계](../examples/ARCHITECTURE.md)에 명시했다.

## 확인 문제

CORS를 허용하지 않았으니 외부 스크립트와 다른 서버는 API에 요청할 수 없는가?

[해설 보기](../appendices/answers.md#장-19)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Production Best Practices: Security · Express.js](https://expressjs.com/en/advanced/best-practice-security.html)
- [Express behind proxies · Express.js](https://expressjs.com/en/guide/behind-proxies.html)
- [Server Side Request Forgery Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

---

[이전 장](../18-authentication/chapter.md) · [책 목차](../index.md) · [다음 장](../20-redis-cache/chapter.md)
