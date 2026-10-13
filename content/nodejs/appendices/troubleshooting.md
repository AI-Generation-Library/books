---
title: "오류 진단과 명령 참고"
description: "실패 계층을 좁히고 재현 정보를 남기는 절차입니다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# 오류 진단과 명령 참고

| 증상 | 먼저 확인할 것 |
| --- | --- |
| node 명령 없음 | 설치·PATH·새 터미널·process.execPath |
| ERR_MODULE_NOT_FOUND | 작업 위치·확장자·잠금 설치·모듈 경계 |
| require가 정의되지 않음 | .mjs/.cjs·package.json type·실행 방식 |
| EADDRINUSE | 기존 프로세스·지정 포트·중복 서버 |
| EACCES | 해당 파일/포트 권한·샌드박스·바인딩 정책 |
| EEXIST | 배타적 파일 생성. 기존 자료를 자동 삭제하지 않는다. |
| 400/413/415 | JSON 문법·바이트 상한·Content-Type |
| 401 | bearer 형식·로그인·만료·로그아웃·메모리 모드 재시작 |
| 타인 작업 404 | 존재 여부를 숨기는 소유권 정책 |
| 테스트가 끝나지 않음 | 서버·소켓·타이머·큐·DB close 경로 |
| 큐에 접수했으나 진행 없음 | outbox·Redis·worker·공유 파일·작업 오류 |
| Docker 소켓 없음 | 엔진 실행 상태·설치 정보·현재 context |
| DB 연결 거부 | 서비스 건강·호스트/컨테이너 주소 차이·포트·비밀 |

실패 명령·작업 디렉터리·OS·Node.js와 npm 버전·오류 코드·재현 입력을 남긴다. 비밀번호·토큰·접속 비밀은 제거한다. 이유를 모른 채 관리자 권한이나 무한 재시도를 추가하지 않는다.

```sh
node --version
npm --version
npm ls --depth=0
npm test
npm run typecheck
docker compose config --quiet
```

문법 검사, 테스트, 실제 외부 환경 실행을 구분한다. Docker 구성 검사가 통과해도 이미지 다운로드·DB 연결·볼륨 권한은 아직 확인하지 않은 것이다. 실제 집필 결과는 검증 안내에 있다.
