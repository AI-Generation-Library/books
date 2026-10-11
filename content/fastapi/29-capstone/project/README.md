---
title: "Knowledge Hub 로컬 모의 실습"
description: "FastAPI 완전 정복의 보충 학습 자료와 실습 안내."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
---

Python 3.12 이상에서 사용자 등록 → JWT 발급 → UTF-8 텍스트 업로드 → 사용자에게 허용된 문서 검색 → 작업 저장 → 모의 답변 → SSE 재생을 확인한다. 외부 API 키, 유료 LLM, PostgreSQL, Redis, GPU가 필요 없다. 실제 임베딩, LangGraph, 분산 큐, 운영 인증 시스템은 구현하지 않는다. 검색은 단어 집합 교집합이며 생성은 문서 발췌다. `mock_units`는 문자 수 기반 교육 지표이고 실제 토큰이나 비용이 아니다.

## 실행

이 README가 있는 project 디렉터리에서 PowerShell 명령을 실행한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:HUB_JWT_SECRET = (& .\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))")
.\.venv\Scripts\python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

별도 터미널에서 `http://127.0.0.1:8000/docs`를 열어 먼저 `POST /users`, `POST /token`에 `{"username":"alice","password":"local-password-12345"}`를 보낸다. 발급받은 토큰을 Authorize에 넣는다. 토큰 유효기간은 15분이다. 서버가 재시작되어도 같은 비밀 키를 유지하면 만료 전 토큰은 유효하다. 비밀 키를 바꾸면 기존 토큰은 검증되지 않는다.

텍스트 업로드 및 질문은 PowerShell에서 아래처럼 확인한다.

```powershell
$body = @{ username = 'alice'; password = 'local-password-12345' } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/token -ContentType application/json -Body $body).access_token
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/documents?title=guide' -ContentType 'text/plain; charset=utf-8' -Headers $headers -Body 'FastAPI supports asynchronous API services.'
$jobHeaders = @{ Authorization = "Bearer $token"; 'Idempotency-Key' = 'first-question' }
$job = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/jobs -ContentType application/json -Headers $jobHeaders -Body '{"question":"FastAPI"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/$($job.id)" -Headers $headers
curl.exe -N -H "Authorization: Bearer $token" "http://127.0.0.1:8000/jobs/$($job.id)/events"
```

기대 결과: 작업은 queued → running → succeeded로 바뀌고 SSE에는 state, sources, delta, done이 나타난다. 답변에는 업로드한 텍스트와 문서 ID가 나온다. 같은 사용자와 같은 Idempotency-Key로 같은 질문을 보내면 같은 작업 ID를 반환한다. 질문을 바꾸면 409다. 다른 사용자의 작업 조회는 404다. `GET /me`의 reserved는 완료 후 0으로 돌아간다.

## 테스트

```powershell
.\.venv\Scripts\python -m pytest -q
```

테스트는 TestClient 내부 ASGI 호출만 사용한다. 실제 네트워크 서버, 외부 모델, 브라우저가 필요 없다. 임시 SQLite 파일과 무작위 비밀 키를 사용한다.

## 의도적인 한계

- SQLite와 단일 프로세스만 지원한다. Uvicorn `--workers`를 추가하면 시작 복구 규칙이 다른 워커의 작업을 되돌릴 수 있으므로 사용하면 안 된다.
- 시작 시 running을 queued로 복구한다. 모의 처리에는 외부 부작용이 없으므로 가능한 제한적인 정책이다. 실제 모델 비용과 도구 실행에는 공급자 작업 ID, 임대, fencing token, outbox, 멱등성 기록이 필요하다.
- 모든 delta를 최종 트랜잭션에서 저장한 뒤 SSE로 전달한다. 실제 모델 토큰이 생성되는 즉시 전달하는 구현은 아니다. 영속 이벤트 재생을 보여준다.
- 사용자 격리는 owner 기준이다. 조직/공유 ACL, 문서 삭제, 권한 변경 중 스트림 철회, 비밀번호 재설정, 갱신 토큰, 로그인 속도 제한은 추가 설계가 필요하다.
- 문서 한 개 최대 64 KiB, 사용자당 30개를 허용한다. 문서 수 검사·삽입과 작업 수·예산 검사는 각각 트랜잭션으로 보호한다. 단어 검색은 작은 데이터만 대상으로 하며 대용량 인덱스가 아니다.
- 문자 기반 모의 예산은 100000이고 활성 작업은 사용자당 최대 5개다. 실제 공급자 사용량과 회계 정산을 대체하지 않는다.
- 운영 로그/메트릭, TLS, CSRF, 계정 유효성 확인, DB 마이그레이션, 파일 악성코드 검사, 외부 도구 승인, 장기 데이터 보존 정책을 제공하는 완성 플랫폼은 아니다.

29장의 운영 확장 설계는 이 최소판을 출발점으로 한다. 운영에서 필요한 PostgreSQL/pgvector, Redis, LangGraph 구성은 원고의 개념 예제이며 이 프로젝트의 실행 의존성이 아니다.

## 선택 실습: 컨테이너와 부하 생성

Docker와 k6 파일은 작성되어 있지만 이 책 제작 과정에서 빌드·서버 실행·부하 시험을 수행한 것은 아니다. 실행하려면 학습자가 도구를 설치하고 위의 비밀 키 환경변수를 설정해야 한다. SQLite 회복 정책 때문에 컨테이너도 하나만 실행한다.

```powershell
docker compose up --build
```

다른 터미널에서 로그인 토큰을 얻은 후 모의 서버에만 낮은 부하를 준다. 60회 실행은 기본 모의 예산 안에서 동작할 수 있는 교육용 시나리오다. 토큰이 만료되거나 사용량이 이미 많으면 실패할 수 있다.

```powershell
$env:HUB_TOKEN = $token
$env:RUN_ID = [guid]::NewGuid().ToString('N')
k6 run load.js
```

load.js는 작업 접수와 완료 조회를 확인한다. SSE의 실제 청크 도착 시점, 느린 구독자, 프록시 동작을 검증하는 스크립트는 아니다. 컨테이너를 중단해도 named volume에 DB가 남는다. 사용자 데이터 삭제는 별도의 의도적인 관리 작업이다.
