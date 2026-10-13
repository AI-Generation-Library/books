# Node.js 완전 정복 · 실행 예제

Node.js 24.18.0 이상 24.x, npm 11 계열을 기준으로 한다. 정확한 의존성은 `package.json`과 `package-lock.json`, 실제 실행 결과는 [검증 안내](../appendices/verification.md)에 있다. 이 디렉터리에서 명령을 실행한다.

## 설치와 기본 검사

```powershell
npm ci --ignore-scripts
npm test
npm run typecheck
```

기본 테스트는 Node.js 내장 테스트 러너를 사용한다. 실제 로컬 HTTP 소켓·임시 파일·Worker Threads를 사용하고 저장소·작업 큐는 메모리 구현이다. TypeScript 검사는 `typescript/` 예제에만 적용한다. `fundamentals/`의 작은 예제는 해당 장의 명령으로 실행한다. 코드 문법 검사와 실제 실행은 구분한다.

## 외부 서비스 없는 전체 흐름

첫 번째 터미널:

```powershell
npm start
```

두 번째 터미널, 같은 디렉터리:

```powershell
npm run smoke
node scripts/load.mjs
```

smoke는 고유한 테스트 계정을 생성하고 로그인·업로드·결과·로그아웃을 검사한다. 정상 결과는 `{"bytes":11,"characters":7,"lines":2}`다. 토큰은 출력하지 않는다. 부하 스크립트는 기본 100건·동시 4건의 closed-loop localhost 실험이며 `/health/live`만 측정한다. 실제 업무 처리 용량이나 클라우드 성능이 아니다. 두 명령 모두 테스트 환경에서 실행한다. 서버는 Ctrl+C로 종료한다.

메모리 모드는 프로세스 재시작 시 사용자·세션·작업을 잃는다. 업로드 파일은 기본 `var/uploads`에 남을 수 있다. 학습 전용 경로를 사용하고 파일을 확인한 뒤 정리한다. 자동 영속 복구나 자동 만료 정리는 구현하지 않았다.

## PostgreSQL·Redis·별도 worker (Docker 환경 필요)

```powershell
docker compose config --quiet
docker compose up --build -d
npm run smoke
docker compose logs api worker
docker compose down
```

기존 로컬 서버가 3000을 사용 중이면 먼저 종료한다. Compose는 PostgreSQL 17.6, Redis 7.4.5, Node.js 24.18.0 이미지를 기준으로 작성했다. 실제 빌드·실행 검증 여부는 검증 안내를 확인한다. 운영에 적용하기 전 최신 보안 패치와 이미지 digest를 확인해 다시 검증한다.

Compose 초기화 서비스가 `001-initial.sql`을 적용한다. 이는 새 전용 DB 초기화용이며 운영 스키마의 일반 변경 관리 도구가 아니다. API와 worker는 같은 호스트의 `uploads` 볼륨을 공유한다. 다중 호스트 파일 저장소가 아니다. DB·Redis 포트는 호스트 127.0.0.1에만 공개한다. 비밀번호는 로컬 학습 전용 값이다.

`docker compose down`은 일반 정지에 사용한다. `-v`를 붙이면 DB·업로드 등 볼륨 데이터가 삭제될 수 있으므로 일반 종료 절차에는 사용하지 않는다.

### 실제 서비스 통합 테스트

서버 전체가 아닌 어댑터를 검증할 때는 **테스트 전용 DB·Redis**를 사용한다. Compose의 API·worker는 이 테스트 작업을 가로채지 않도록 중지한다. 예제는 생성한 행과 파일만 정리하지만 공용 큐의 다른 소비자와 함께 실행하지 않는다.

```powershell
docker compose stop api worker
$env:DATABASE_URL = 'postgres://nodebook:local-only-change-me@127.0.0.1:55432/nodebook'
$env:REDIS_URL = 'redis://127.0.0.1:56379'
$env:NODEBOOK_INTEGRATION = '1'
npm run test:integration
```

실행 후 `Remove-Item Env:NODEBOOK_INTEGRATION,Env:DATABASE_URL,Env:REDIS_URL`로 해당 셸의 테스트 설정을 지울 수 있다. integration 플래그가 없으면 통합 테스트는 skip된다. skip은 실제 DB·Redis 검증 성공을 뜻하지 않는다.

직접 준비한 서비스에 연결하려면 `MODE=production`, `DATABASE_URL`, `REDIS_URL`, `UPLOAD_DIR`을 설정하고 `npm run migrate`, `npm start`, 다른 터미널의 `npm run worker` 순으로 실행한다. 두 프로세스는 같은 파일 저장소에 접근해야 한다. 환경 변수는 터미널별로 설정해야 한다.

## API

| 경로 | 역할 |
| --- | --- |
| POST /auth/register | JSON `{email,password}`로 가입 |
| POST /auth/login | 세션 토큰 발급 |
| POST /auth/logout | bearer 세션 폐기 |
| POST /jobs | bearer 인증, `application/octet-stream`, 최대 1MiB |
| GET /jobs/:id | 소유자만 상태·결과 조회 |
| GET /jobs/:id/events | bearer 인증 SSE, 최대 30초·최신 상태 반복 |
| GET /health/live | 프로세스 응답 확인 |
| GET /health/ready | 접수 가능 여부·DB·큐 확인 |

이메일은 예제 수준의 형식 검사만 수행한다. 비밀번호는 12자 이상, UTF-8 128바이트 이하다. 세션은 1시간 만료다. UTF-8 이외 파일은 분석 단계에서 실패한다. 브라우저 기본 EventSource는 Authorization 헤더를 직접 설정하지 못하므로 bearer SSE는 fetch 스트리밍 등으로 읽는다. 토큰을 URL에 넣지 않는다.

## 설정

| 변수 | 기본값/역할 |
| --- | --- |
| MODE | `memory` 또는 `production`; 기본 memory |
| HOST / PORT | `127.0.0.1` / `3000` |
| UPLOAD_DIR | `var/uploads` |
| DATABASE_URL / REDIS_URL | production 모드 필수 |
| BASE_URL | smoke 대상, 기본 `http://127.0.0.1:3000` |
| TARGET_URL | localhost 부하 대상 |
| REQUESTS / CONCURRENCY | 부하 실험 100/4, 상한 10000/32 |

## 읽을 파일

`app.mjs` → `security.mjs`·`files.mjs` → 저장소 → `queue.mjs` → `bull-queue.mjs`·`worker.mjs` 순서로 읽는다. [아키텍처와 운영 한계](ARCHITECTURE.md)도 함께 확인한다. AI 작성 코드이며 전체 사람 검수를 거쳤다고 표시하지 않는다. 코드와 설명은 저장소의 CC0 조건을 따르고, 외부 패키지는 각각의 라이선스를 따른다.
