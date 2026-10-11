---
title: "23장. 로깅과 모니터링"
description: "Knowledge Hub 사용자가 “검색이 가끔 멈춘다”고 말한다. 개발자는 서버의 200 응답 로그를 찾지만 사용자가 어떤 요청을 보냈는지, 어디서 기다렸는지, 부분 답변만 받았는지 알 수 없다. 로그를 많이 쓰는 것과 문제를 설명할 수 있는 것은 다르다. 관측 자료가 요청·작업·배포 버전을 연결하고 "
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 23
part: 6
---

## 학습 목표와 도입 사례

Knowledge Hub 사용자가 “검색이 가끔 멈춘다”고 말한다. 개발자는 서버의 200 응답 로그를 찾지만 사용자가 어떤 요청을 보냈는지, 어디서 기다렸는지, 부분 답변만 받았는지 알 수 없다. 로그를 많이 쓰는 것과 문제를 설명할 수 있는 것은 다르다. 관측 자료가 요청·작업·배포 버전을 연결하고 적절한 시간 경계를 표현해야 한다.

이 장은 로그, 메트릭, trace의 역할을 나누고 함께 사용하는 법을 다룬다. Python 3.12, FastAPI 0.121 이상, Pydantic 2 기준의 독립 실습에서 JSON 로그와 Prometheus 형식 메트릭을 제공한다. 실제 Prometheus·Grafana·Sentry 서버 연결은 별도 환경이 필요한 확장 실습이다. 외부 SaaS로 사용자 자료를 보내는 작업을 자동으로 수행하지 않는다.

## 23.1 Uvicorn Access Log 이해

access log는 method, 경로, 상태 코드 같은 기본 요청 결과를 보여 준다. 하지만 외부 호출, DB 대기, 업무 작업 성공을 모두 설명하지 않는다. 특히 스트리밍은 시작 시 200을 보냈다가 이후 실패할 수 있다. access log의 200은 답변 생성 완료의 증거가 아니다. 완료 이벤트와 작업 상태를 따로 관측한다.

서버 로그에 나타난 client 주소도 프록시 구성에 따라 다르다. proxy headers를 어떤 주소에서 신뢰하는지 모르면 실제 사용자 IP로 오해할 수 있다. URL query에는 검색 내용과 토큰이 포함될 수 있으므로 전체 URL을 무조건 저장하지 않는다. 라우트 템플릿과 필요한 안전한 필드만 남기고 보존 기간과 접근 권한을 정한다.

## 23.2 Python logging 구조

logging은 logger가 기록을 만들고 handler가 출력하며 formatter가 형식을 정하는 구조다. logger의 계층과 propagation 때문에 같은 기록이 여러 handler에 출력될 수 있다. 모듈마다 설정을 다시 실행하기보다 앱 시작에서 설정을 한 번 정의한다. library에는 logger를 두되 root handler를 강제로 바꾸지 않는 편이 좋다. [Python logging](https://docs.python.org/3.12/library/logging.html)

운영 로그는 stdout·stderr로 내보내고 수집기가 전달할 수 있다. 느린 디스크나 원격 전송을 요청 경로에서 동기 실행하면 로그가 지연의 원인이 된다. 큐 handler를 사용할 때에도 큐를 유한하게 하고 넘칠 때 처리 정책을 정한다. 로그를 하나도 버리지 않으려고 무한히 보관하면 장애 때 메모리가 고갈될 수 있다.

## 23.3 JSON 구조화 로그

JSON 로그는 문자열 검색 대신 필드로 조회할 수 있게 한다. 시각, level, service, request_id, event, duration_ms, route, status를 안정적인 schema로 정의한다. 오류는 안전한 종류와 코드로 표현하고 비밀번호·Authorization·원문 문서·LLM prompt를 기본 로그에서 제외한다. 운영자의 질문에 필요한 필드만 넣는다.

한 줄에 JSON 하나를 쓰면 수집기가 처리하기 쉽다. multiline traceback은 구조화된 예외 필드로 넣거나 별도 안전한 오류 수집기로 보낸다. 기록 형식이 JSON이라고 민감 정보가 자동으로 숨겨지는 것은 아니다. logging formatter에서 임의 객체를 전부 직렬화하는 편의 기능은 예상하지 못한 자료를 노출할 수 있다.

## 23.4 Request ID와 로그 추적

request ID는 같은 요청의 로그를 연결하는 상관관계 키다. 인증이나 권한을 증명하는 값이 아니다. 앞단이 전달한 ID를 사용할 때 길이와 형식을 제한하고, 없거나 잘못되면 새로 생성한다. 외부 호출에는 안전한 상관관계 헤더를 전달할 수 있지만 secret을 섞지 않는다.

`ContextVar`는 비동기 작업의 실행 문맥에 값을 보관할 수 있다. 요청 진입 시 set하고 `finally`에서 token으로 reset한다. 별도 Task는 생성 당시의 context를 복사할 수 있으므로 응답 이후 업무 작업에는 request ID뿐 아니라 job ID도 기록한다. 큐 worker까지 자동으로 이어지는 것은 아니므로 메시지의 안전한 metadata로 전달해야 한다.

## 23.5 Prometheus 메트릭 수집

메트릭은 집계 가능한 숫자를 제공한다. Counter는 누적 사건 수, Gauge는 현재 값, Histogram은 관측 분포를 표현할 때 사용한다. 요청 수와 latency를 라우트·method·상태로 분류하면 전체 흐름을 볼 수 있다. 사용자 ID나 원시 URL을 label로 넣으면 시계열이 급증한다. Prometheus 공식 지침은 label cardinality 관리와 일관된 instrumentation을 강조한다. [Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/)

`/documents/123` 대신 `/documents/{document_id}`를 label로 사용한다. 요청 ID는 로그·trace에 적합하고 메트릭 label에는 적합하지 않다. Histogram bucket은 목표 지연과 분포를 반영한다. 밀리초로 이름을 붙이고 초를 넣는 단위 혼동을 피한다. 여러 worker를 실행할 때 프로세스 메모리의 registry가 전체 값을 합산하지 않는다는 점도 고려해야 한다.

## 최소 실습: 요청 ID, 완료 로그, latency histogram

아래 `main.py`는 **완전 실행 예제**다. pure ASGI middleware로 안쪽 앱 호출 완료 시간을 잰다. 이는 클라이언트의 왕복 시간과 동일하지 않으며 BackgroundTasks까지 포함될 수 있다. 실제 wire 전송 완료를 완벽하게 측정한다고 주장하지 않는다. 단일 worker 실습이며 다중 worker 메트릭 집계는 별도 구성이다.

```python
import json
import logging
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, Response
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

request_id = ContextVar("request_id", default="-")
registry = CollectorRegistry()
requests = Counter("hub_requests_total", "HTTP requests", ["route", "method", "status"], registry=registry)
duration = Histogram(
    "hub_request_duration_seconds", "ASGI app duration", ["route", "method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5), registry=registry,
)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "knowledge-hub",
            "request_id": request_id.get(),
            "event": record.getMessage(),
            "route": getattr(record, "route", None),
            "status": getattr(record, "status", None),
            "duration_ms": getattr(record, "duration_ms", None),
        }, ensure_ascii=False)


logger = logging.getLogger("hub")
logger.setLevel(logging.INFO)
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers[:] = [handler]


class Observe:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        raw = headers.get(b"x-request-id", b"")
        try:
            identity = str(UUID(raw.decode("ascii"))) if len(raw) <= 36 else str(uuid4())
        except (ValueError, UnicodeDecodeError):
            identity = str(uuid4())
        token = request_id.set(identity)
        started = time.perf_counter()
        status = 500

        async def wrapped_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = list(message.get("headers", [])) + [
                    (b"x-request-id", identity.encode("ascii"))
                ]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            elapsed = time.perf_counter() - started
            route = getattr(scope.get("route"), "path", "unmatched")
            method = scope["method"] if scope["method"] in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
            try:
                if route != "/metrics":
                    requests.labels(route, method, str(status)).inc()
                    duration.labels(route, method).observe(elapsed)
                    logger.info("request_finished", extra={
                        "route": route, "status": status, "duration_ms": round(elapsed * 1000, 3),
                    })
            finally:
                request_id.reset(token)


app = FastAPI()
app.add_middleware(Observe)


@app.get("/documents/{document_id}")
async def document(document_id: int):
    logger.info("document_read")
    return {"id": document_id, "title": "Knowledge Hub"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})
```

**설치와 실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1" "prometheus-client>=0.21,<1"
python -m uvicorn main:app --port 8023 --workers 1
```

`curl.exe -i http://127.0.0.1:8023/documents/1`에서 x-request-id를 확인한다. 로그의 document_read와 request_finished에 같은 ID가 나와야 한다. `/documents/2`도 조회한 뒤 `/metrics`를 보면 ID마다 다른 label이 생기지 않고 `/documents/{document_id}` 아래 요청 수가 증가한다. `curl.exe -H "X-Request-ID: invalid" ...`으로 잘못된 ID를 보내도 정상 UUID로 교체된다. Uvicorn 자체 access log는 이 formatter를 사용하는 것이 아니므로 모든 stdout가 JSON인 구성이라고 부르지 않는다.

계측 코드는 별도 try/finally로 context reset을 보장한다. 큰 서비스에서는 logging·metric 오류가 업무 흐름을 방해하지 않도록 계측 계층의 실패 정책도 검증한다. route template가 없는 요청은 unmatched 한 값으로 모아 label 폭증을 피한다.

## 23.6 Grafana 대시보드 구축

Grafana에 Prometheus를 data source로 연결하고 요청 수, 오류율, latency, in-flight, loop lag, DB pool wait, 큐 대기 나이를 같은 시간축으로 배치한다. 모든 상세 로그를 대시보드로 만들기보다 운영자가 질문에 답할 수 있는 작은 패널 집합을 먼저 만든다. 전체 서비스와 endpoint별 drill-down을 연결한다. Grafana는 data source의 질의로 대시보드를 구성한다. [Grafana Dashboards](https://grafana.com/docs/grafana/latest/visualizations/dashboards/)

아래는 **PromQL 질의 예제**이며 실습 메트릭 이름과 bucket을 기준으로 한다. 여러 인스턴스의 bucket을 합친 뒤 quantile을 계산한다.

```promql
sum(rate(hub_requests_total[5m]))

sum(rate(hub_requests_total{status=~"5.."}[5m]))
/
sum(rate(hub_requests_total[5m]))

histogram_quantile(0.95,
  sum by (le, route) (rate(hub_request_duration_seconds_bucket[5m]))
)
```

분모가 0일 때의 표시는 대시보드에서 처리하고 자료 없음과 오류율 0을 혼동하지 않는다. 5xx 외에도 사용자 취소, 429, 큐 등록 거절, SSE 생성 실패를 업무 기준으로 별도 관리한다. 히스토그램의 해상도는 bucket에 제한되므로 출력 숫자를 지나치게 정밀하게 표시하지 않는다.

## 23.7 OpenTelemetry와 분산 추적

trace는 요청의 실행을 span으로 나누어 시간 관계를 보여 준다. 검색 span 안에 DB span, 디렉터리 HTTP span, 결과 조합 span이 있으면 어느 단계가 느렸는지 볼 수 있다. 프로세스 간에는 trace context를 전달하고, queue 작업은 원래 요청과 링크 또는 parent 정책을 명시한다. request ID와 trace ID는 목적이 겹치지만 동일한 계약은 아니다.

OpenTelemetry는 계측 API·SDK와 exporter를 분리한다. 자동 FastAPI 계측만 추가했다고 수집 서버에 자료가 저장되지는 않는다. SDK provider, resource의 service 이름, exporter, collector, sampling과 종료 flush를 구성해야 한다. [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)

**개념 예제**로 `FastAPIInstrumentor.instrument_app(app)`를 기존 앱에 적용할 수 있지만 실제 전송을 위해 위 구성이 필요하다. auto instrumentation과 manual instrumentation을 동시에 중복 적용하지 않는다. span attribute에 원문 문서, prompt, 인증 헤더를 무조건 넣지 않는다. sampling이 낮으면 실패 요청을 놓칠 수 있으므로 비용·개인정보·진단 가치를 함께 검토한다. trace에서 보이는 기간이 event loop 대기까지 포함하는지도 확인한다.

## 23.8 Sentry 기반 오류 추적

오류 추적기는 비슷한 예외를 묶고 배포 버전·발생 빈도·영향 사용자를 연결하는 데 도움이 된다. 단순 500 로그보다 어떤 release부터 오류가 늘었는지 찾기 쉽다. 하지만 SDK를 켜면 요청 본문과 주변 context가 외부 저장소로 전달될 수 있으므로 실제 수집 필드와 개인정보 정책을 검토한다.

Sentry 설정은 환경에서 DSN과 release를 받고 PII 전송을 기본 비활성화하며 scrub hook을 검토한다. trace 수집 여부와 sample rate도 명시적으로 정한다. 인증 토큰과 원문 문서를 보낼 필요는 보통 없다. SDK가 알려진 프레임워크를 자동 감지하더라도 사용 버전과 통합 동작을 확인한다. 이 책은 외부 Sentry로 전송하는 실행을 하지 않으며 공식 SDK의 FastAPI 통합 소스를 참고한다. [Sentry Python FastAPI integration](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/fastapi.py)

예외 수집이 사용자에게 보내는 오류 계약을 대체하지는 않는다. 내부 오류는 안전한 코드로 매핑하고 request ID를 제공한다. 예상 가능한 404를 모든 예외와 같은 수준으로 알리면 중요한 결함이 알림 속에 묻힌다. 오류 grouping이 서로 다른 원인을 하나로 묶는지, 같은 오류를 과도하게 나누는지도 운영 중 검토한다.

## 23.9 응답시간, 오류율, 처리량 모니터링

세 지표를 함께 보면 의미가 생긴다. 처리량이 떨어지고 latency가 올라가면 병목 가능성이 있다. 처리량이 갑자기 0인데 오류율도 0이면 서비스가 건강한 것이 아니라 수집 실패나 앞단 라우팅 문제일 수 있다. HTTP 성공률과 업무 성공률을 구별하고 202 작업의 완료율, SSE done 비율을 별도로 둔다.

자원 메트릭을 원인 후보로 연결한다. DB 풀 대기, 열린 외부 연결, 큐 가장 오래된 작업, in-flight 요청, 메모리, loop lag를 본다. 사용자 ID를 label로 남기는 대신 업무 집계가 필요하면 별도 통계 저장소를 사용한다. 프로세스별 메트릭에는 instance label을 통해 여러 worker가 어떻게 수집되는지 검증한다. `/metrics`는 인터넷 전체에 노출할 이유가 없으며 관리 네트워크에서 접근을 제한한다.

## 23.10 장애 대응과 알림 설계

좋은 알림은 사용자 영향과 즉시 실행할 행동을 연결한다. CPU 80% 같은 원인 후보만으로 야간 호출을 만들기보다 성공률·지연의 서비스 목표와 오류 예산 소모를 기준으로 설계한다. 단, 곧 데이터 손실이 날 디스크 고갈 같은 예외는 미리 알릴 수 있다. 짧은 급증과 지속 장애를 구분하기 위해 여러 시간창을 사용하고 기준은 실제 트래픽에서 검토한다.

알림에는 서비스, 환경, 영향, 시작 시각, 확인할 대시보드, runbook, 최근 배포 정보를 넣는다. 연결이 끊긴 외부 공급자 때문에 모든 endpoint에서 같은 알림이 폭주하면 하나의 사건으로 묶고 중복을 줄인다. 장애 해소 알림도 실제 지표 회복을 기준으로 한다. 관측 자료 자체가 없어진 경우의 알림을 별도로 만들면 조용한 실패를 줄일 수 있다.

## 확인 문제와 해설

1. access log의 200은 SSE 작업 완료를 의미하는가? **해설:** 응답 시작의 성공일 수 있다. done 이벤트와 작업 상태, 스트림 실패 지표가 필요하다.
2. `/documents/123`를 label로 넣어도 되는가? **해설:** 자료 수에 비례해 시계열이 증가한다. `/documents/{document_id}`를 쓰고 개별 ID는 안전한 로그·trace 경계에서 다룬다.
3. worker별 p95를 평균내면 전체 p95가 되는가? **해설:** 아니다. bucket count를 합쳐 전체 분포에서 계산한다.
4. 실습 평가 기준은 무엇인가? **해설:** 응답과 로그의 request ID가 일치하고 잘못된 ID는 교체되며 route template로 메트릭이 집계된다. 단일 worker와 ASGI 완료 시간이라는 측정 범위를 명시한다.

## 요약과 다음 장

로그는 사건, 메트릭은 집계, trace는 실행 경로를 설명한다. 세 자료를 안전한 상관관계 키로 연결하고 높은 cardinality와 민감 정보 수집을 제한한다. 다음 장에서는 이 자료를 사용해 실제 장애를 재현하고 취소·deadline·과부하를 다룬다.

## 공식 참고자료

- [Python logging](https://docs.python.org/3.12/library/logging.html)
- [Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/visualizations/dashboards/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [OpenTelemetry FastAPI instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Sentry Python FastAPI integration source](https://github.com/getsentry/sentry-python/blob/master/sentry_sdk/integrations/fastapi.py)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 22장 Docker와 배포 아키텍처](../22-docker-deployment/chapter.md) · [24장 운영 장애와 고급 동시성 →](../24-incidents-concurrency/chapter.md)
