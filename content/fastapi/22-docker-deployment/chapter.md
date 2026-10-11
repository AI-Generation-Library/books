---
title: "22장. Docker와 배포 아키텍처"
description: "Knowledge Hub가 개발자의 가상환경에서 동작하지만 새 서버에서는 라이브러리 버전이 달라 시작하지 않는다. Docker는 애플리케이션과 실행에 필요한 파일을 이미지로 묶어 이런 차이를 줄인다. 그러나 컨테이너만 만들면 배포가 완성되는 것은 아니다. TLS, 상태 확인, 요청 배분, 종료, DB m"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 22
part: 6
---

## 학습 목표와 도입 사례

Knowledge Hub가 개발자의 가상환경에서 동작하지만 새 서버에서는 라이브러리 버전이 달라 시작하지 않는다. Docker는 애플리케이션과 실행에 필요한 파일을 이미지로 묶어 이런 차이를 줄인다. 그러나 컨테이너만 만들면 배포가 완성되는 것은 아니다. TLS, 상태 확인, 요청 배분, 종료, DB migration, 비밀 관리와 되돌리기 경로를 따로 설계해야 한다.

이 장은 재현 가능한 이미지와 로컬 Compose를 만들고, 운영 교체 과정에서 자원과 요청을 안전하게 정리하는 원리를 학습한다. Python 3.12, FastAPI 0.121 이상, Pydantic 2를 사용하며 예제는 독립 폴더에서 실행한다. Docker Engine의 Linux 컨테이너 모드가 필요하다. 여기서 제시하는 태그는 교육용이며 최신·취약점 없음·영구 불변을 뜻하지 않는다. 실제 공개 서버나 외부 레지스트리에 배포하는 실습은 하지 않는다.

## 22.1 Python 애플리케이션 컨테이너화

이미지는 파일과 실행 설정의 묶음이고 컨테이너는 그 이미지로 시작한 프로세스다. 컨테이너의 쓰기 레이어는 영속 데이터 저장소가 아니다. 문서, DB, 작업 이력은 외부 저장소나 명시적인 볼륨에 둔다. 컨테이너를 지웠다가 다시 만들 때 필요한 자료가 남는지 확인한다.

실행 계정은 필요한 권한만 가진다. API 서버가 root로 파일 시스템 전체를 수정할 이유는 대부분 없다. 이미지에 `.env`, API 키, SSH 키를 복사하지 않는다. 빌드 시 dependency를 받아야 한다면 비밀을 ARG나 레이어에 남기는 방식 대신 빌드 secret 기능을 검토한다. 컨테이너 격리는 운영 권한 설계를 대체하지 않으며 호스트의 Docker 제어 권한도 강한 권한이다.

## 22.2 FastAPI Dockerfile 작성

Dockerfile은 바뀌는 빈도가 낮은 의존성 파일을 먼저 복사하고 소스를 나중에 복사하면 cache를 활용하기 쉽다. 다만 설치 결과의 재현성은 cache만으로 얻을 수 없다. 상위 패키지뿐 아니라 전이 의존성까지 검토한 lock을 사용하고 이미지 base도 운영에서는 digest로 고정한다. Docker 공식 안내는 작은 신뢰 가능한 기반 이미지, 불필요한 파일 제외, 버전 고정을 다룬다. [Docker build best practices](https://docs.docker.com/build/building/best-practices/)

다음은 로컬 실습용 `main.py` **완전 실행 예제**다. readiness는 예제 앱의 준비 상태만 확인하며 실제 DB나 broker의 준비를 확인한 구현이 아니다. 외부 자원이 있으면 시작 과정에서 제한된 검사와 초기화를 추가한다.

```python
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = True
    try:
        yield
    finally:
        app.state.ready = False


app = FastAPI(lifespan=lifespan)


@app.get("/live")
async def live():
    return {"alive": True}


@app.get("/ready")
async def ready(request: Request):
    prepared = getattr(request.app.state, "ready", False)
    return JSONResponse({"ready": prepared}, status_code=200 if prepared else 503)


@app.get("/documents")
async def documents():
    return {"items": ["Knowledge Hub"]}


@app.get("/events")
async def events():
    async def generate():
        for number in range(3):
            await asyncio.sleep(0.2)
            yield f"data: {number}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

실습용 `requirements.in`에 `fastapi>=0.121,<1`, `pydantic>=2,<3`, `uvicorn>=0.30,<1`을 각 줄에 쓴다. 깨끗한 가상환경에서 설치한 뒤 잠금 파일을 생성하는 **실행 명령**이다. `requirements.txt`를 생성해야 아래 Dockerfile이 완전히 실행 가능하다.

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requirements.in
.\.venv-build\Scripts\python.exe -m pip freeze | Set-Content -Encoding UTF8 requirements.txt
```

이 방법은 예제의 의존성 버전을 고정하지만 hash와 플랫폼별 해석까지 보장하는 엄격한 공급망 잠금 방식은 아니다. 실제 팀은 검토된 uv lock 또는 hash 잠금 도구를 선택하고 갱신·취약점 점검 절차를 둔다. Windows에서 얻은 lock에 플랫폼 전용 라이브러리가 있는 프로젝트라면 Linux 대상 잠금도 검증한다. 현재 예제는 최소 의존성만 설치한다.

`Dockerfile`의 **완전 실행 설정**이다. JSON 배열 CMD로 실행하면 shell을 중간에 두지 않고 프로세스에 신호를 전달할 수 있다.

```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-graceful-shutdown", "20"]
```

`.dockerignore`의 **완전 실행 설정**도 만든다. 이 목록 외의 민감 파일이 없다는 점은 별도로 검토한다.

```text
.venv*
.git
.env
.env.*
__pycache__
*.pyc
tests
work
```

`docker build -t knowledge-hub:lab .`으로 만들고 `docker run --rm -p 127.0.0.1:8022:8000 knowledge-hub:lab`으로 시작한다. `curl.exe http://127.0.0.1:8022/ready`는 ready true를 반환해야 한다. 빌드에 사용한 image ID와 lock 파일을 함께 기록한다. 태그 이름만 기록하면 나중에 같은 이름으로 다른 이미지가 덮일 수 있다.

## 22.3 Docker Compose 환경 구성

Compose는 여러 로컬 서비스를 하나의 설정으로 실행한다. 컨테이너끼리 통신할 때는 host의 localhost가 아니라 service 이름을 사용한다. API 컨테이너에서 `127.0.0.1`은 그 컨테이너 자신이다. DB나 Redis에는 Compose의 service DNS 이름을 사용하고 사용자에게 필요한 포트만 호스트에 노출한다.

아래 `compose.yaml`은 API와 Nginx를 연결하는 **완전 실행 설정**이다. DB가 없는 최소 예제이며 11·18장의 저장소 설정을 묵시적으로 포함하지 않는다.

```yaml
services:
  api:
    build: .
    init: true
    stop_grace_period: 25s
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2)"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
  proxy:
    image: nginx:1.28-alpine
    ports: ["127.0.0.1:8022:80"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf:ro"]
    depends_on:
      api:
        condition: service_healthy
```

`depends_on`의 준비 완료 조건은 시작 순서의 도움일 뿐, 이후 API 장애를 자동 복구하거나 트래픽에서 제거하는 로드밸런서 정책은 아니다. healthcheck가 unhealthy가 되었다고 모든 Compose 환경에서 컨테이너가 자동 재시작되는 것도 아니다. 재시작 정책과 외부 감독을 별도로 정한다. [Compose service reference](https://docs.docker.com/reference/compose-file/services/)

## 22.4 개발 및 운영 환경 분리

개발 환경은 reload와 소스 bind mount가 편리하다. 운영에서는 immutable image를 실행하고 reload를 사용하지 않는다. 개발용 DEBUG 로그, 기본 인증 계정, permissive CORS가 운영으로 넘어가지 않도록 설정 스키마를 나눈다. 운영 필수 secret이 빠졌을 때 조용히 기본값으로 시작하기보다 시작 실패로 드러내는 것이 좋다.

이미지 하나에 dev와 prod 설정을 구워 넣기보다 runtime 설정으로 구분한다. 같은 image digest를 시험 환경에서 검증하고 운영으로 승격하면 배포 대상의 동일성을 추적하기 쉽다. DB migration은 애플리케이션 worker 여러 개가 동시에 실행하지 않도록 별도 job으로 수행한다. 새 앱과 구 앱이 잠시 동시에 작동할 수 있도록 schema 변경의 호환성을 검토한다.

## 22.5 Uvicorn 운영 설정

개발의 `--reload`와 운영의 `--workers`는 목적이 다르다. 컨테이너 예제는 worker 하나를 쓰고 필요하면 바깥 replica 수로 확장하는 구조다. 단일 호스트에서는 여러 worker도 적합할 수 있다. 각 프로세스의 DB·HTTP 풀과 메모리 캐시가 따로 생긴다는 점을 연결·메모리 예산에 넣는다. Uvicorn은 동시성 제한과 graceful shutdown timeout 등의 설정을 제공한다. [Uvicorn settings](https://uvicorn.dev/settings/)

proxy headers를 믿는 대상도 제한한다. 인터넷에서 직접 보낸 `X-Forwarded-For`를 신뢰하면 실제 사용자 IP와 rate limit 기준이 위조될 수 있다. 프록시만 API에 접근할 수 있는 네트워크 경계를 만들고 실제로 신뢰하는 프록시 주소를 설정한다. 예제 Compose의 프록시 구성만으로 모든 proxy trust가 완성됐다고 주장하지 않는다.

## 22.6 Nginx Reverse Proxy

`nginx.conf`의 **완전 실행 설정**이다. 로컬 8022 포트로 받은 요청을 API에 전달하며 SSE 경로의 buffering을 끈다. WebSocket은 이 예제 앱에 없으므로 별도 upgrade 설정을 넣지 않는다.

```nginx
events {}
http {
    upstream hub { server api:8000; }
    server {
        listen 80;
        client_max_body_size 10m;
        location / {
            proxy_pass http://hub;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 2s;
            proxy_read_timeout 30s;
        }
        location /events {
            proxy_pass http://hub;
            proxy_buffering off;
            proxy_read_timeout 60s;
            proxy_set_header Host $host;
        }
    }
}
```

기존 `docker run`을 끝내고 `docker compose up --build`를 실행한다. `/documents`와 `curl.exe -N http://127.0.0.1:8022/events`를 확인한다. 이벤트가 0, 1, 2로 나타나야 한다. proxy_read_timeout은 전체 요청의 최대 시간이 아니라 읽기 사이의 대기 제한이라는 성격을 가진다. [Nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

이 최소 upstream은 컨테이너 교체와 DNS 재해석을 모두 처리하는 운영 discovery 구성이 아니다. API 주소가 바뀌면 선택한 Nginx 버전과 설정의 DNS 동작을 검증하고 reload 또는 지원되는 동적 resolver 구성을 사용한다. 프록시 앞에서 요청이 거절된 경우 API 로그에는 나타나지 않으므로 프록시 로그도 수집한다.

## 22.7 HTTPS와 인증서 관리

TLS는 흔히 로드밸런서나 프록시에서 종료하고 내부 API로 전달한다. 인증서는 실제 서비스 도메인에 발급하고 자동 갱신을 설정하며 만료 시각을 모니터링한다. 인증서 발급 자체와 배포된 인증서 reload는 다른 단계다. 갱신 파일이 생겼는데 프록시가 계속 이전 인증서를 들고 있을 수 있다.

로컬 HTTP 실습을 외부 공개용 설정으로 복사하지 않는다. 실제 HTTPS에는 도메인 검증, DNS, 443 노출, 인증서 저장 권한, 갱신 작업이 필요하다. secret이나 개인 키를 Docker image에 넣지 말고 제한된 파일 mount 또는 비밀 저장소로 제공한다. 브라우저의 secure cookie, SSE, WebSocket의 wss와 프록시 scheme 인식도 함께 검증한다.

## 22.8 Health Check와 Graceful Shutdown

liveness는 프로세스가 살아 있고 정상적으로 실행할 수 있는지, readiness는 새 요청을 받아도 되는지 질문한다. DB가 잠시 느려졌다고 liveness까지 실패시켜 모든 앱을 재시작하면 장애를 키울 수 있다. readiness의 외부 점검에도 짧은 timeout과 제한된 빈도를 적용한다. status endpoint가 비싼 전체 업무를 수행하면 점검 자체가 부하가 된다.

종료 순서는 새 트래픽에서 제거, 진행 요청 drain, 프로세스 종료 신호, 자원 정리다. 앱의 graceful timeout보다 컨테이너의 종료 유예가 더 짧으면 finally가 끝나기 전에 강제 종료된다. 예제는 Uvicorn 20초, Compose 25초로 작은 여유를 둔다. 이것은 모든 스트림이 안전하게 종료된다는 보증이 아니다. 장시간 SSE와 Agent 작업에는 최대 수명, 재연결, checkpoint와 내구성 큐가 필요하다.

## 22.9 무중단 배포 전략

rolling 교체는 일부 인스턴스씩 바꾸고, blue-green은 새 환경을 준비한 뒤 트래픽을 전환하며, canary는 일부 요청으로 위험을 관찰한다. 어느 방식도 DB schema 호환성을 자동으로 해결하지 않는다. 새 컬럼을 추가하고 양쪽 앱이 읽을 수 있게 하는 expand 단계와 구 필드를 제거하는 contract 단계를 나누는 방법을 고려한다.

무중단이라는 말은 프로세스가 둘 있다는 사실보다 사용자의 성공률과 복구 계약으로 평가해야 한다. 구 worker의 스트림을 어떻게 종료할지, 배포 중 최대 DB 연결이 얼마나 늘어나는지, 되돌린 앱이 새 DB 자료를 읽을 수 있는지 검증한다. 이미지가 다시 이전 버전이 되었다고 외부 부수 효과와 migration이 자동 rollback되는 것은 아니다.

## 22.10 CI/CD 파이프라인 구축

기본 흐름은 lint·테스트, 이미지 빌드, 취약점 및 설정 검토, immutable 식별자로 보관, 시험 환경 검증, 단계적 승격, 배포 후 관측이다. 실패한 단계가 다음 단계로 넘어가지 않도록 한다. DB migration은 실행자와 실행 횟수를 명확히 정하고, 배포 전후 smoke test에 readiness뿐 아니라 간단한 업무 조회를 포함한다.

아래는 **CI 설정 예제**이며 실제 registry push나 배포를 수행하지 않는다. 저장소에 `tests`와 잠금된 `requirements-test.txt`가 준비되어야 한다. action 태그는 예제용이며 운영에서는 검토한 commit SHA로 고정한다.

```yaml
name: verify-image
on: [push, pull_request]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install -r requirements-test.txt
      - run: python -m pytest -q
      - run: docker build -t knowledge-hub:ci .
```

운영 배포에서는 레지스트리와 cloud 권한을 최소화하고 short-lived credential을 사용할 수 있는지 검토한다. 배포 완료 조건은 이미지 생성이 아니라 새 버전의 readiness, 업무 성공률, 지연, 오류가 목표 안에 있는 것이다. 문제 발생 시 이전 digest로 돌아갈 수 있도록 식별자와 설정 버전을 함께 보관한다.

## 확인 문제와 해설

1. image 태그가 같으면 실행 파일도 같은가? **해설:** 태그는 다른 이미지로 이동할 수 있다. 운영 추적에는 digest 또는 immutable 정책을 사용한다.
2. Compose healthcheck가 실패하면 반드시 자동 재시작되는가? **해설:** 상태 표시와 재시작 정책은 별개다. 외부 감독과 실제 runtime 정책을 검증해야 한다.
3. graceful timeout은 30초인데 플랫폼 종료 유예는 10초다. 어떤 문제가 생기는가? **해설:** 요청과 자원 정리가 끝나기 전에 강제 종료될 수 있다. drain과 shutdown 예산을 전체적으로 맞춘다.
4. 실습 통과 기준은 무엇인가? **해설:** 잠금 파일 생성 후 이미지가 빌드되고 비root 계정으로 readiness·조회가 동작하며 프록시를 통한 SSE가 순서대로 온다. 실제 Docker 실행 여부를 기록하고 공개 배포 성공과 혼동하지 않는다.

## 요약과 다음 장

배포는 이미지를 만드는 것에 더해 시작, 준비, 트래픽, 종료와 되돌리기의 계약을 만드는 일이다. lock·digest, 최소 권한, proxy trust, stream drain과 DB 호환성을 함께 다룬다. 다음 장에서는 배포 후 상태를 볼 수 있도록 로그, 메트릭, trace를 연결한다.

## 공식 참고자료

- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [Compose service reference](https://docs.docker.com/reference/compose-file/services/)
- [FastAPI Docker deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Uvicorn settings](https://uvicorn.dev/settings/)
- [Nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 21장 FastAPI 성능 최적화](../21-optimization/chapter.md) · [23장 로깅과 모니터링 →](../23-observability/chapter.md)
