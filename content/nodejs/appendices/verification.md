---
title: "생성과 검증 기록"
description: "실행 결과와 미검증 범위를 명시합니다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# 생성과 검증 기록

## 작성 출처

- 작성일·검증일: 2026-10-14, Asia/Seoul.
- 작성 도구: Codex. 사용자가 제목·설명·8부 36장 계획을 승인한 뒤 대화에서 원고와 코드를 직접 작성했다.
- 모델: 정확한 실행 모델 ID를 확인하지 못해 null. 별도 생성 API 호출·외부 생성기 사용으로 기록하지 않는다.
- 입력: generation-input.json. 장별 공식 자료와 references.md를 근거로 원문을 대량 복제하지 않고 설명과 예제를 작성했다.
- 전체 사람 검수: 미수행. AI의 기술 검토와 자동 검사는 독립 전문가·사람 검수를 대신하지 않는다.

## 실제 환경

Windows / PowerShell / Node.js 24.18.0 / npm 11.16.0 / Python 3.12.12. 기본 테스트와 smoke는 로컬 HTTP 접속이 허용된 환경에서 실행했다.

| 직접 의존성 | 정확한 버전 |
| --- | --- |
| bullmq | 5.81.5 |
| express | 5.3.0 |
| pg | 8.23.1 |
| redis | 5.12.1 |
| @types/node | 24.19.2 |
| typescript | 5.9.3 |

전체 전이 의존성은 examples/package-lock.json에 고정한다. npm ci --ignore-scripts로 잠금 파일 재설치도 확인했다. 설치 당시 npm audit 보고는 취약점 0건이었다. 전이 의존성 cron-parser 4.9.0의 유지보수 종료 안내도 출력되었다. 이는 사용 경로·호환성을 검토해 상위 패키지 갱신 시 확인할 항목이다. audit 0건은 모든 코드의 보안 보증이 아니며 시간이 지나면 결과가 달라질 수 있다.

## 실행한 검사

| 검사 | 실제 결과와 범위 |
| --- | --- |
| npm test | 22개 통과, 실패·skip 0. 파일·UTF-8·크기·기존 파일 보존·KDF·만료 세션·동시 실행·취소·outbox·HTTP·SSE·로그아웃·권한·오류·실제 타임아웃·Worker |
| npm run typecheck | typescript/job-service.ts를 tsc --noEmit으로 검사, 종료 코드 0 |
| 독립 예제 | runtime·JavaScript·모듈·Promise·이벤트 루프·파일·Buffer/이벤트·내장 HTTP·Worker·성능 예제 10개 정상 실행 |
| 파일 복사 CLI | 임시 파일 복사와 내용 일치, 기존 대상 재실행 EEXIST/종료 코드 1 확인 |
| 실제 main.mjs 서버 smoke | 등록→로그인→업로드→완료 조회→로그아웃. bytes=11, characters=7, lines=2, 정상 종료 코드 |
| Compose 구성 | docker compose config --quiet 종료 코드 0. 실제 엔진·컨테이너 실행과 다름 |
| 문법·본문 링크·메타데이터 | 제출 전 별도 검사. 상세 집계는 아래 검사 요약에 기록 |

## 제한된 localhost 실험

memory 모드 / GET /health/live / closed-loop / 요청 100건 / 동시 4건 / 오류 0건.
총 117.09ms, 관측 854.02 req/s, p50 2.02ms, p95 8.94ms, p99 17.49ms.

같은 기계의 짧은 기능 확인 실험이다. 인증·업로드·DB·Redis·TLS·외부 네트워크를 포함한 용량 측정이 아니다. 샘플이 작고 실행마다 달라지므로 운영 성능이나 SLA로 일반화하지 않는다.

## 확인하지 않은 범위와 이유

- Docker Desktop 엔진 소켓이 없고 `docker desktop start`가 설치 레지스트리 정보 누락으로 실패했다. 구성 문법만 확인했고 이미지 빌드·컨테이너 실행·볼륨 권한은 미검증이다.
- 실제 PostgreSQL·Redis 서비스가 준비되지 않아 어댑터 통합 테스트는 실행하지 않았다. 통합 테스트 코드·SQL·Compose·재현 명령을 제공한다. skip을 통과로 기록하지 않는다.
- Linux SIGTERM·컨테이너 배포·TLS·실제 클라우드·다중 호스트·외부 장애 주입·백업 복원은 미검증이다.
- 캐시·멀티파트·WebSocket·메트릭/분산 추적 수집기 확장은 본문 설계 설명이며 종합 프로젝트에 전부 구현된 기능이 아니다.
- CPU 예제 실행은 확인했지만 CPU 프로파일·힙 스냅샷의 육안 분석과 누수 진단 완료를 주장하지 않는다.
- 전체 원고의 독립 전문가·사람 검수는 수행하지 않았다. 공식 문서 참조와 자동 검사로 모든 기술 설명의 정확성을 인증하지 않는다.

별도 npm run test:integration 실행은 환경 플래그가 없어 1개 skip(통과 0)였다. 이를 외부 서비스 검증 성공으로 계산하지 않았다.

## 다음 기여자의 재현 순서

examples에서 npm ci --ignore-scripts, npm test, npm run typecheck를 실행한다. npm start와 별도 터미널의 npm run smoke로 서버 흐름을 확인한다. Docker가 준비되면 README의 전용 서비스 통합 절차를 따른다. 저장소 루트에서는 python scripts/validate-books.py를 실행한다.

원고·코드를 수정하면 메타데이터와 검증 범위, 다운로드를 함께 갱신한다. ZIP 안의 책 메타데이터는 자기 자신을 다운로드로 가리키지 않도록 조정했고 예제 ZIP과 모든 원고·실행 소스를 포함한다. 예제 ZIP은 검증 문서를 함께 제공한다. node_modules·실행 DB·업로드·토큰·진단 파일은 포함하지 않는다.


## 제출 전 검사 요약

- JavaScript 실행 소스 33개 `node --check` 통과.
- 본문 JavaScript 코드 블록 25개 모듈 문법 검사 통과. 실행 검증과 구분한다.
- Markdown 48개, 로컬 링크·앵커 263개 검사에서 오류 0건.
- 외부 공식 참고 URL 86개 HTTP 200 응답 확인. 응답 성공은 내용 전체 검수를 뜻하지 않는다.
- `python scripts/validate-books.py`: 기존 책 3권과 Node.js 책을 포함한 4권 통과. Node.js는 36장·8부·다운로드 2개.
- 전체 책 ZIP을 별도 임시 폴더로 풀어 같은 메타데이터 검증기로 검사한다. 두 ZIP의 CRC와 원본 파일 일치도 확인한다.

[기계 판독 검사 결과](validation-results.json)에 환경·검사 집계·실행 출력을 보관했다. 토큰·비밀번호·실행 DB·업로드 파일은 포함하지 않는다.
