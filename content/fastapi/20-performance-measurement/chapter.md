---
title: "20장. FastAPI 성능 측정"
description: "Knowledge Hub의 검색 API는 개발자 노트북에서 40ms에 응답한다. 사용자가 늘자 일부 요청은 3초가 걸리지만 평균은 150ms라서 대시보드가 양호해 보인다. 문제를 해결하려고 worker를 늘렸더니 DB 연결이 더 많이 생겨 응답이 오히려 느려진다. 숫자는 이 장의 도입을 위한 가정이며 실"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 20
part: 6
---

## 학습 목표와 도입 사례

Knowledge Hub의 검색 API는 개발자 노트북에서 40ms에 응답한다. 사용자가 늘자 일부 요청은 3초가 걸리지만 평균은 150ms라서 대시보드가 양호해 보인다. 문제를 해결하려고 worker를 늘렸더니 DB 연결이 더 많이 생겨 응답이 오히려 느려진다. 숫자는 이 장의 도입을 위한 가정이며 실제 측정 결과가 아니다. 성능 문제는 빠른 한 요청의 시연으로 이해할 수 없다. 부하의 형태, 자원 대기, 지연 분포와 오류를 함께 읽어야 한다.

이 장의 목표는 실험 가능한 성능 가설을 만들고 올바른 부하를 생성하며 병목 근거를 수집하는 것이다. Python 3.12, FastAPI 0.121 이상, Pydantic 2를 기준으로 독립 실습한다. 외부 DB 없이 풀 대기를 흉내 내지만 그것이 PostgreSQL의 성능 수치라고 주장하지 않는다. 모든 표의 숫자는 가상의 설명용 자료이고, 실제 결과는 독자의 환경에서 별도로 기록해야 한다.

## 20.1 성능을 측정해야 하는 이유

성능 측정은 문제가 어느 자원에서 발생하는지 결정하기 위한 도구다. CPU가 여유롭다는 사실만으로 서버에 여유가 있다고 할 수 없다. DB 연결을 기다리거나 상대 API의 할당량 때문에 대기하면 CPU는 낮아도 사용자는 느린 응답을 받는다. 반대로 CPU가 높아도 지연과 오류가 서비스 목표 안에 있으면 반드시 장애는 아니다.

측정 전에 질문을 하나로 좁힌다. 예를 들어 “검색 결과 20개에 작성자 정보를 붙이는 단계에서 HTTP 풀 대기가 p95를 악화시키는가?”는 확인할 수 있다. “FastAPI는 빠른가?”는 데이터 크기, 네트워크, 업무 로직이 없어 실험 설계가 어렵다. 가설, 바꿀 변수, 관측 지표, 성공 기준을 먼저 기록한다. 테스트 이후 유리한 지표만 골라 성공을 선언하지 않는다.

기본 실험 조건에는 commit, Python과 라이브러리 버전, worker 수, CPU·메모리 제한, DB 데이터 양, connection pool, 캐시 상태, 부하 생성기 위치가 필요하다. 이 정보가 없으면 다른 사람의 결과를 재현하거나 이전 결과와 비교하기 어렵다. 성능 숫자를 문서에 넣을 때 조건을 함께 쓰는 이유도 여기에 있다.

## 20.2 Latency, Throughput, RPS

Latency는 한 작업이 시작해 완료되기까지 걸린 시간이다. 측정 경계에 따라 클라이언트 왕복, 서버 처리, DB 질의 시간으로 나뉜다. Throughput은 단위 시간에 완료한 작업량이다. RPS는 초당 요청 수를 뜻하지만 시작한 요청, 완료한 요청, 성공한 요청 중 무엇인지 밝혀야 한다. 서버가 503을 즉시 반환하면 전체 완료 RPS는 높아도 유효한 업무 처리량은 낮다.

요청 하나에서 내부 검색과 프로필 조회를 두 번 수행하면 외부 시스템의 요청 수는 사용자 RPS보다 많다. 큐 API가 초당 1000개의 202를 반환한다고 초당 1000개의 임베딩을 완료하는 것은 아니다. 이 차이를 놓치면 비동기 큐를 붙인 후 성능이 좋아졌다고 잘못 판단한다. 사용자 응답 시간, 작업 대기 시간, 작업 완료율을 서로 다른 지표로 관리한다.

## 20.3 평균 응답시간과 p95, p99

평균은 합계를 개수로 나눈 값이므로 분포의 꼬리를 숨길 수 있다. p95는 관측 요청의 약 95%가 그 값 이하였다는 뜻이며, p99는 더 드문 느린 요청을 설명한다. 백분위 계산 방식은 도구에 따라 보간 등 차이가 있을 수 있다. 작은 표본의 p99는 불안정하므로 표본 수와 관측 기간을 함께 표시한다.

각 worker가 계산한 p95를 평균내면 전체 p95가 되지 않는다. 히스토그램 bucket의 누적 수나 병합 가능한 분포를 사용해야 한다. 응답이 성공한 요청만 집계하면 느리다가 실패한 요청이 빠져 지연이 좋아 보일 수 있다. 성공 지연, 전체 지연, 오류율을 함께 보고 timeout의 집계 정책도 정한다.

아래는 **가상의 비교 표**다. 1000개 중 대부분은 빠르고 일부는 긴 대기라는 설명을 위한 수치이며 실제 실험값이 아니다.

| 실험 | 성공 RPS | 평균 | p95 | p99 | 오류율 |
|---|---:|---:|---:|---:|---:|
| 기준 설정 | 80 | 100ms | 180ms | 900ms | 0.2% |
| 풀만 크게 조정 | 86 | 95ms | 240ms | 1500ms | 1.0% |

두 번째 설정은 평균과 RPS만 보면 나아졌지만 꼬리 지연과 오류가 악화됐다. DB의 동시 실행량이 늘어 경쟁이 커진 것이 가설일 수 있다. 확정하려면 query latency와 pool wait, DB CPU·lock wait를 확인해야 한다. 표만으로 원인을 단정하지 않는다.

## 20.4 동시 사용자 수와 동시 요청 수

동시 사용자는 로그인한 사람 또는 시나리오를 수행하는 가상 사용자 수이고, 동시 요청은 그 순간 완료되지 않은 요청 수다. 사용자 한 명은 요청 사이에 화면을 읽으며 쉬기도 하고 여러 요청을 동시에 보내기도 한다. 따라서 “1000명 접속”만으로 부하를 정의할 수 없다. 동작 빈도와 think time, 요청 혼합 비율을 써야 한다.

안정된 시스템의 같은 경계에서 Little의 법칙 `L = λ × W`를 용량 추정에 활용할 수 있다. 평균 동시 요청 L, 완료율 λ, 평균 체류 시간 W다. 예를 들어 초당 100개가 완료되고 평균 체류 시간이 0.2초라고 가정하면 평균 동시 요청은 약 20개다. 과부하로 대기가 계속 증가하는 상황에서는 안정 상태의 계산을 그대로 적용하면 안 된다. 외부 호출 슬롯을 계산하려면 전체 요청 시간이 아니라 그 슬롯을 보유하는 시간을 사용한다.

## 20.5 k6를 활용한 부하 테스트

고정 VU 방식은 사용자가 응답을 받은 뒤 다음 요청을 시작하는 닫힌 모델이다. 서버가 느려지면 발생하는 요청 속도도 낮아진다. 일정한 도착률을 유지하려면 `constant-arrival-rate` 같은 열린 모델을 쓴다. k6는 사용 가능한 VU 안에서 지정한 iteration 도착률을 유지한다. [k6 constant-arrival-rate](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/)

iteration 하나가 요청 하나라는 가정이 있어야 설정한 rate를 RPS로 해석할 수 있다. 여러 HTTP 호출이나 재시도가 있다면 같지 않다. VU가 모자라면 dropped iterations가 생긴다. 이는 시스템에 도착하지 못한 테스트 작업이므로 HTTP 오류율에만 의존하면 목표 부하를 달성하지 못한 사실을 놓친다. 부하 생성기의 CPU, 네트워크, 파일 디스크립터도 관찰한다.

## 20.6 CPU-bound와 I/O-bound 병목 구분

CPU-bound 작업은 실행 코어 시간을 소비하고, I/O-bound 작업은 다른 자원 완료를 기다린다. `asyncio.sleep()`은 대기를 양보하지만 `time.sleep()`은 스레드를 붙잡는다. 긴 파이썬 계산을 `async def`에 넣어도 CPU 병렬화가 되지 않는다. CPU가 높으면서 loop lag가 높으면 이벤트 루프에서 직접 계산하는지 살펴본다.

CPU가 낮고 지연만 높으면 DB나 외부 서비스, 로컬 admission 대기 등을 조사한다. 요청 tracing으로 단계별 시간을 분해하면 도움이 된다. 외부 API가 200ms, DB가 30ms, 나머지가 10ms인데 사용자 latency가 1초라면 실행 전 대기나 스케줄링, 프록시의 추가 시간을 찾아야 한다. 단일 총 시간만으로 async 라이브러리 선택이 맞았는지 판단하기 어렵다.

## 20.7 이벤트 루프 지연 측정

이벤트 루프 지연은 예정된 콜백이나 코루틴이 실제로 실행되기까지의 추가 지연이다. 주기적으로 작은 sleep을 예약하고 예상 시점과 현재 단조 시각의 차이를 관측할 수 있다. `time.time()`은 시스템 시계 보정에 영향을 받을 수 있으므로 구간 시간에는 `loop.time()` 또는 `perf_counter()`를 사용한다.

loop lag가 높다고 무조건 한 함수의 블로킹만 원인인 것은 아니다. CPU quota 부족, 과도한 준비 Task 수, GC, 시스템 스케줄링도 영향을 준다. 샘플링 주기가 50ms라면 아주 짧은 스파이크를 정확히 복원하지 못한다. 계측 자체의 비용과 해상도를 함께 기록한다. 평균 loop lag만 보지 않고 max 또는 백분위, 지연이 커진 시점을 요청 로그와 연결한다.

## 최소 실습: 대기와 블로킹을 구별하기

다음 `main.py`는 **완전 실행 예제**다. `/lab/block`은 고의로 이벤트 루프를 막는 장애 재현 경로이므로 로컬 실습 외에는 배포하지 않는다. 작은 유한 deque로 loop lag를 보관한다. 모의 풀은 세마포어이며 실제 DB 연결이 아니다.

```python
import asyncio
import time
from collections import deque
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Query, Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.lag = deque(maxlen=1200)
    app.state.pool = asyncio.Semaphore(2)

    async def monitor():
        loop = asyncio.get_running_loop()
        while True:
            target = loop.time() + 0.05
            await asyncio.sleep(0.05)
            app.state.lag.append(max(0, loop.time() - target))

    task = asyncio.create_task(monitor())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(lifespan=lifespan)


@app.get("/documents")
async def documents(request: Request, delay_ms: int = Query(50, ge=0, le=500)):
    started = time.perf_counter()
    async with asyncio.timeout(2):
        async with request.app.state.pool:
            waited = time.perf_counter() - started
            await asyncio.sleep(delay_ms / 1000)
    return {"items": ["Knowledge Hub"], "pool_wait_ms": round(waited * 1000, 3)}


@app.get("/lab/block")
async def block(ms: int = Query(200, ge=0, le=500)):
    time.sleep(ms / 1000)  # 의도적인 결함
    return {"blocked_ms": ms}


@app.get("/diagnostics")
async def diagnostics(request: Request):
    samples = list(request.app.state.lag)
    return {"samples": len(samples), "max_loop_lag_ms": max(samples, default=0) * 1000}
```

**설치·서버 실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1"
python -m uvicorn main:app --port 8020 --workers 1
```

다른 터미널에서 diagnostics를 확인하고 `curl.exe "http://127.0.0.1:8020/lab/block?ms=300"`을 보낸다. 이후 diagnostics의 최대 loop lag가 기준보다 증가해야 한다. 정확히 300ms라고 고정해서 assert하지 않는다. monitor 실행 시점과 OS 스케줄링에 따라 관측값이 달라진다. 서버 시작 직후 샘플이 없을 수도 있으므로 먼저 잠시 기다린다.

다음은 `load.js`로 저장하는 **완전 실행 k6 예제**다. k6는 Python 패키지가 아니며 [공식 설치 안내](https://grafana.com/docs/k6/latest/set-up/install-k6/)에 따라 별도 설치한다. 아래 rate·시간·threshold는 실습 입력과 가정된 목표이며 실제 서비스의 SLO가 아니다.

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  discardResponseBodies: true,
  scenarios: {
    search: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 10,
      maxVUs: 40,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<300'],
    dropped_iterations: ['count==0'],
    checks: ['rate>0.99'],
  },
};

export default function () {
  const response = http.get('http://127.0.0.1:8020/documents?delay_ms=50', {
    timeout: '3s',
    tags: { name: 'documents' },
  });
  check(response, { 'status is 200': r => r.status === 200 });
}
```

`k6 run load.js`를 실행해 전체 요청 수, HTTP 오류, checks, p95, dropped iterations를 기록한다. rate를 20에서 60으로 바꾼 뒤 나머지 조건을 유지한다. 모의 풀 두 슬롯이 각 50ms 작업을 처리한다고 가정하면 이상적인 상한은 약 40회/초이나 오버헤드와 timeout, 실행 스케줄링으로 실측은 달라진다. 더 큰 입력 rate에서 풀 대기가 증가하는지 확인한다. 앞의 가정값을 벤치마크 수치로 책이나 보고서에 인용하지 않는다.

## 20.8 DB 커넥션 풀과 응답시간 분석

DB에 접속하지도 못한 채 기다리는 시간과 질의 실행 시간이 모두 endpoint latency에 들어간다. query가 10ms인데 pool wait가 500ms면 인덱스 추가만으로 해결되지 않을 수 있다. 세션을 언제 열고 언제 닫는지, 트랜잭션 중 외부 API를 기다리는지, 스트리밍 동안 연결을 보유하는지부터 확인한다.

SQLAlchemy 풀의 기본 구조는 연결 빌림과 반환이며, pool size와 overflow 등의 정책이 별도로 있다. [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

한 worker의 pool size가 10, overflow가 5이고 worker 네 개라고 가정하면 앱에서 DB로 가능한 연결은 최대 60개가 된다. 배포 교체 동안 구 worker와 신 worker가 겹치면 더 늘 수 있다. DB에는 관리자, migration, 다른 서비스 연결도 필요하다. 전체 예산에서 앱의 몫을 나눠야 한다. pool timeout이 발생했는데 DB 연결 수를 무작정 늘리면 DB CPU나 lock 경합이 새로운 병목이 될 수 있다.

실제 분석에서는 acquire 앞뒤의 단조 시각, SQL 실행 span, transaction duration, 반환 후 풀 상태를 수집한다. 라이브러리의 내부 private 필드를 읽어 운영 메트릭을 만드는 방식은 버전 변경에 취약하다. 지원되는 event와 instrumentation을 쓰거나 repository 경계에서 대기를 측정한다. 계측이 실제 acquire 전체 시간을 포함하는지도 검증한다.

## 20.9 부하 테스트 시나리오 설계

단계는 작은 smoke, 정상 부하, 한계 탐색, 급증, 장시간 soak로 나눌 수 있다. 모든 실험을 한 번에 실행하면 원인과 결과가 섞인다. 먼저 아주 작은 부하에서 응답의 정확성과 데이터 준비를 검증한다. 그 뒤 정상 부하를 충분히 유지해 안정 상태를 관찰하고 조금씩 늘린다. 한계점에서는 성공 RPS가 더 이상 증가하지 않는지, 대기와 오류가 얼마나 빠르게 늘어나는지 본다.

Knowledge Hub의 현실적인 혼합은 조회, 검색, 업로드 등록, 상태 조회가 다를 것이다. 읽기 캐시가 모두 warm인 부하와 cold인 부하를 구분한다. 같은 문서 하나만 반복 조회하면 캐시 적중률과 DB page cache가 실제보다 높다. 사용자별 권한과 결과 크기도 섞어야 한다. SSE는 연결 수, 첫 이벤트 시간, 이벤트 간격, 전체 완료 시간을 별도로 측정한다. 짧은 HTTP latency만으로 장기 연결을 평가하지 않는다.

열린 모델과 닫힌 모델을 함께 해석하면 유용하다. 실제 사용자의 행동은 닫힌 모델이 자연스러울 수 있지만, 외부에서 유입되는 일정 요청률에 대한 과부하 분석은 열린 모델이 필요하다. 닫힌 모델에서 서버가 느려질수록 요청 발생도 줄어드는 현상을 응답 지연 개선으로 착각하지 않는다. 장애가 난 구간이 통계에서 빠지는 coordinated omission의 위험을 인지하고 테스트 목적에 맞는 도착 모델을 고른다.

실험 종료 후에도 확인할 것이 있다. 대기 Task 수와 열린 연결, 큐 길이, 메모리가 기준으로 돌아오는지 본다. 응답 지연이 회복됐어도 뒤에서 비용을 쓰는 버려진 작업이 남으면 시스템은 회복하지 않은 것이다. 변경 전후를 같은 환경에서 반복하고 편차가 큰 결과는 한 숫자로 단정하지 않는다. 부하 생성기가 포화된 결과와 서버가 포화된 결과를 구분해 보고한다.

## 측정 결과를 읽는 순서

먼저 목표 부하가 실제 도착했는지 확인한다. dropped iterations나 client timeout이 많으면 입력부터 해석해야 한다. 다음으로 유효 성공률과 반환 데이터의 정확성을 본다. 그 뒤 지연 분포와 자원 대기를 연결한다. 마지막으로 CPU·메모리·DB·외부 호출을 조사해 개선 후보를 정한다. 서버 access log만 보면 클라이언트가 포기한 요청과 앞단에서 거절된 요청이 누락될 수 있으므로 앞단·앱·클라이언트 경계를 비교한다.

성능 보고서에는 “풀 2에서 4로 변경하니 빨라졌다”보다 “동일 입력 rate와 결과 크기에서 pool wait가 감소했고, p95는 줄었으며 DB CPU와 오류율은 목표 안에 있었다”라고 쓴다. 반대로 처리량을 높이면서 정확성 검사를 제거하거나 캐시만 warm으로 바꾸면 동일 실험이 아니다. 최적화의 효과를 정직하게 보여 주는 것이 측정의 최종 목적이다.

## 확인 문제와 해설

1. 평균 50ms인데 p99가 2초인 API를 어떻게 평가하는가? **해설:** 서비스 목표와 오류율, 표본 수를 보고 느린 경로를 조사한다. 평균만으로 적합하다고 판단하지 않는다.
2. k6 rate가 100이면 반드시 서버에 100RPS가 도착하는가? **해설:** iteration당 호출 수와 VU 수, dropped iterations에 따라 다르다. 입력 설정과 실제 도착을 구분해야 한다.
3. CPU 20%인데 요청이 느리다. worker를 늘려야 하는가? **해설:** 풀 대기, 외부 API, DB lock부터 확인한다. 공유 자원이 병목이면 worker 증가가 경쟁을 악화시킬 수 있다.
4. 실습의 풀 상한 40회/초는 측정 결과인가? **해설:** 두 슬롯과 50ms로 계산한 이상적인 가정이다. 실측의 HTTP 성공 RPS·대기·오류와 함께 비교한다.
5. 실습 통과 기준은 무엇인가? **해설:** 블로킹 경로 후 loop lag가 증가하고, 높은 입력 rate에서 모의 풀 대기가 증가하는 현상을 기록한다. 실제 값·환경·오류·dropped iterations를 남기고 가정값과 구별한다.

## 요약과 다음 장

성능 측정은 지연 하나를 재는 일이 아니다. 도착률, 완료율, 성공률과 분포를 구분하고 자원 대기를 연결해야 한다. 같은 조건에서 한 변수를 바꿔 실험하며 종료 후 회복도 확인한다. 다음 장은 이 근거를 바탕으로 블로킹 제거, 풀 조정, 쿼리와 직렬화 최적화를 적용한다.

## 공식 참고자료

- [k6 constant-arrival-rate](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/)
- [k6 open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Python asyncio event loop](https://docs.python.org/3.12/library/asyncio-eventloop.html)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 19장 FastAPI 테스트 전략](../19-testing/chapter.md) · [21장 FastAPI 성능 최적화 →](../21-optimization/chapter.md)
