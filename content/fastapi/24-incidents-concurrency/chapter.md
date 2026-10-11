---
title: "24장. 운영 장애와 고급 동시성"
description: "Knowledge Hub의 AI 요청이 급증했다. CPU는 낮지만 응답은 수십 초가 걸리고, 사용자가 화면을 닫은 뒤에도 공급자 호출 비용이 계속 발생한다. 새 worker를 추가하자 DB 연결이 더 빨리 고갈된다. 이 상황에서 재시작은 증상을 잠깐 감출 수 있지만 원인을 설명하지 않는다. 대기하는 작업"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 24
part: 6
---

## 학습 목표와 도입 사례

Knowledge Hub의 AI 요청이 급증했다. CPU는 낮지만 응답은 수십 초가 걸리고, 사용자가 화면을 닫은 뒤에도 공급자 호출 비용이 계속 발생한다. 새 worker를 추가하자 DB 연결이 더 빨리 고갈된다. 이 상황에서 재시작은 증상을 잠깐 감출 수 있지만 원인을 설명하지 않는다. 대기하는 작업과 실제 실행하는 작업, 프로세스 수명과 업무 수명을 분리해서 보아야 한다.

Python 3.12, FastAPI 0.121 이상, Pydantic 2의 독립 실습으로 자원 반환, 취소, deadline, 입장 제한을 확인한다. 숫자는 실습 입력과 설명용 가정이다. 장애 재현은 로컬에서 수행한다.

## 24.1 이벤트 루프 블로킹 장애

이벤트 루프는 준비된 코루틴을 실행하다 await로 양보하면 다른 작업으로 이동한다. 긴 동기 함수가 이 스레드를 점유하면 새 요청, timeout 처리, heartbeat, 취소 전달까지 늦어질 수 있다. 따라서 “timeout이 1초인데 5초 뒤에야 발생했다”는 상황이 가능하다. 타이머가 등록되어 있어도 이벤트 루프가 실행할 기회가 없으면 즉시 처리할 수 없다.

loop lag, health endpoint 지연, 단일 코어 사용량과 stack sample을 본다. 특정 worker만 느린지도 비교한다. 큰 정규식, JSON 파싱, 문서 파서, sync SDK를 조사하고 I/O 대기는 제한된 스레드로, 긴 CPU 작업은 프로세스로 옮긴 뒤 재측정한다.

## 24.2 DB 커넥션 풀 고갈

풀 고갈은 요청이 연결을 빌릴 수 없는 상태다. 연결이 실제 query를 수행하는지, 외부 API를 기다리며 트랜잭션을 열어 두는지, 종료하지 않은 스트림이 보유하는지 구별한다. 요청 수가 늘었기 때문일 수도 있지만 누락된 close 또는 rollback이 원인일 수도 있다. “DB가 느리다”는 한 문장으로 섞으면 해결을 잘못 고른다.

SQLAlchemy의 풀은 설정된 자원 한도 아래에서 연결을 빌리고 반환한다. [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)

분석 순서는 acquire wait, 보유 시간, query 시간, 열린 transaction, DB lock과 연결 수다. `AsyncSession`은 요청 또는 독립 작업마다 만들고 동시 Task가 공유하지 않는다. pool timeout을 없애면 실패가 사라지는 대신 대기 작업이 계속 쌓일 수 있다. 풀을 늘리기 전 반환 경로와 전체 worker 연결 예산을 점검한다. DB가 포화된 상황에서 연결을 늘리면 한 요청당 실행 시간도 증가할 수 있다.

## 24.3 메모리 누수와 리소스 정리

메모리 증가는 해제되지 않은 파일·소켓·Task·큐·모델 객체의 참조에서 시작할 수 있다. 완료된 Task를 집합에 보관하면서 제거하지 않거나, 사용자별 cache에 TTL과 크기 제한이 없으면 트래픽에 비례해 증가한다. 연결 종료 후 생산자가 계속 큐에 넣는 스트리밍 구현은 요청이 사라져도 자료가 남는다.

자원은 생성한 계층이 소유하고 명시적인 수명 경계에서 닫는다. `async with`, context manager, 의존성 yield, lifespan의 `finally`가 기본 도구다. HTTP client는 앱 수명, DB session은 짧은 요청·업무 수명, 외부 stream은 실제 소비 수명에 맞춘다. 관측은 RSS와 Python 할당 snapshot, 열린 연결, active Task, 큐 길이를 함께 본다. [Python tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html)

객체 해제 후에도 RSS가 바로 낮아지지 않을 수 있다. tracemalloc에 나타나지 않는 네이티브 메모리도 있다. 부하 반복마다 사용량이 계속 증가하는지와 살아 있는 참조 경로를 함께 확인한다.

## 24.4 Race Condition과 공유 상태

비동기 코드도 race가 있다. 값을 읽고 await한 뒤 쓰면 두 Task가 같은 값을 읽을 수 있다. GIL은 업무 연산의 원자성을 보장하지 않는다. `asyncio.Lock`은 한 이벤트 루프에서 공유 상태 접근을 직렬화할 수 있지만 다른 worker의 메모리에는 같은 락이 없다. DB의 원자 update, unique 제약, version 조건이 프로세스 간 규칙의 기본이다.

`미처리 확인 → 임베딩 → 완료 표시`에는 중복 실행 창이 있다. lease 만료 후 구 worker가 결과를 덮지 않도록 완료 갱신에 attempt/version 조건을 넣는다. 분산 락만으로 외부 부수 효과가 모두 안전해지지는 않는다.

## 24.5 Task 취소와 CancelledError

`Task.cancel()`은 다음 적절한 대기 지점에서 취소를 전달하도록 요청한다. 즉시 실행 중인 Python 코드를 강제로 중단하는 인터럽트가 아니다. `CancelledError`를 잡으면 필요한 정리를 수행한 뒤 다시 raise하는 것이 일반적이다. Python의 구조화된 동시성 기능도 취소를 내부적으로 사용하므로 취소를 삼키면 종료와 timeout 계약이 깨질 수 있다. [Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html)

`finally`는 취소 시에도 실행되지만 그 안에서 오래 기다리는 정리 작업 역시 중단될 수 있다. 정리는 짧게 만들고 필요한 경우 제한된 shield를 검토한다. shield가 전체 작업을 영원히 보호하게 만들면 종료가 끝나지 않는다. 요청 취소와 꼭 완료해야 하는 업무 commit을 구분한다. 중요한 업무는 요청 Task에 억지로 보호막을 씌우기보다 내구성 작업으로 옮기는 설계가 더 분명하다.

`to_thread()`를 기다리는 코루틴의 취소는 실행 중인 스레드를 멈추지 않는다. SDK 자체 timeout과 연결 정리를 설정한다. 요청 슬롯 반환 뒤에도 스레드가 남을 수 있으므로 실제 입장·완료 수를 별도로 관측한다.

## 24.6 Timeout과 Deadline 설계

timeout은 특정 단계의 대기 한도이고 deadline은 전체 작업이 끝나야 하는 시각이다. 검색 1초, 생성 1초, 재시도 1초를 각각 설정하면 전체는 3초 이상 걸릴 수 있다. 사용자가 허용한 총 2초 안에 끝내려면 단조 시각으로 deadline을 정하고 각 단계에 남은 예산을 전달한다. 네트워크 read timeout처럼 데이터 조각 사이 제한과 전체 기간 제한은 다르다.

Python 3.12의 `asyncio.timeout_at()`은 이벤트 루프의 단조 시각 기준 deadline을 표현한다. timeout context 밖에서 `TimeoutError`를 처리한다. context 안에서 광범위하게 취소를 잡아 무시하면 timeout 동작도 왜곡될 수 있다. 여러 서버 사이에서 단조 시각 숫자 자체를 보내면 시계 기준이 다르므로 사용할 수 없다. 남은 예산 또는 안전하게 해석하는 절대 시각 계약을 전달한다.

deadline에는 입장 대기·외부 호출·재시도·조합을 포함한다. 앱 deadline과 프록시 timeout 사이에 오류 응답을 전송할 여유도 둔다.

## 24.7 클라이언트 연결 종료 시 작업 정리

클라이언트가 떠났다고 일반 HTTP endpoint의 작업이 항상 자동 취소되는 것은 아니다. HTTP disconnect 이벤트, 반복적인 연결 확인, 서버의 send 실패 등을 통해 관측한다. 응답을 기다리는 동안 독립적인 disconnect watcher가 필요한 경우도 있다. body를 읽는 작업과 disconnect 감시가 동시에 같은 receive를 소비하면 문제가 생길 수 있으므로 서버·프레임워크의 receive 계약을 확인한다.

SSE에서는 응답 생성자의 finally에서 상위 stream과 생산 Task를 정리한다. 일반 조회는 사용자가 떠났다면 불필요한 계산을 중지할 수 있다. 반면 이미 승인한 문서 색인 작업은 브라우저를 닫아도 계속 실행해야 할 수 있으므로 내구성 큐와 상태 조회 계약을 사용한다. 어떤 작업을 취소할지 업무 기준을 명시한다. `is_disconnected()`는 관측 보조 수단이지 외부 작업 종료를 보증하는 마법이 아니다.

## 최소 실습 A: 입장 제한과 전체 deadline

다음 `main.py`는 **완전 실행 예제**다. 로컬 모의 작업만 수행한다. 연결 종료는 짧은 단계 사이에서 확인하므로 긴 단일 I/O를 즉시 취소하는 watcher 구현은 아니다. 슬롯은 획득 성공 여부를 기록하고 한 번만 반환한다.

```python
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, Response


class ClientGone(Exception):
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.slots = asyncio.Semaphore(2)
    app.state.active = 0
    app.state.completed = 0
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/work")
async def work(request: Request, budget_ms: int = Query(300, ge=20, le=1000)):
    state = request.app.state
    acquired = False
    deadline = asyncio.get_running_loop().time() + budget_ms / 1000
    try:
        async with asyncio.timeout_at(deadline):
            try:
                async with asyncio.timeout(0.02):
                    await state.slots.acquire()
                    acquired = True
                    state.active += 1
            except TimeoutError:
                raise HTTPException(503, "실행 용량 부족", headers={"Retry-After": "1"}) from None

            for _ in range(6):
                if await request.is_disconnected():
                    raise ClientGone()
                await asyncio.sleep(0.02)
            state.completed += 1
            return {"result": "Knowledge Hub"}
    except TimeoutError:
        raise HTTPException(504, "전체 시간 예산 초과") from None
    except ClientGone:
        # 실제로 떠난 사용자에게 204가 전달된다는 뜻은 아니다.
        return Response(status_code=204)
    except asyncio.CancelledError:
        raise
    finally:
        if acquired:
            state.active -= 1
            state.slots.release()


@app.get("/state")
async def state(request: Request):
    return {"active": request.app.state.active, "completed": request.app.state.completed}
```

**설치와 실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1" "httpx>=0.28,<1"
python -m uvicorn main:app --port 8024 --workers 1
```

정상 `/work`는 200, `?budget_ms=30`은 전체 deadline에 걸려 504를 기대한다. 그 뒤 `/state`의 active가 0이면 반환 경로가 작동한 것이다. 환경의 scheduling과 입장 경쟁에 따라 짧은 deadline에서는 503과 504 경계가 달라질 수 있다. 어느 timeout이 먼저 발생했는지 기록하는 것이 운영에서 중요하다. 내구성 업무를 중단하거나 외부 효과를 rollback한 예제로 해석하지 않는다.

다음 `burst.py`는 **완전 실행 클라이언트 예제**다. 서버를 띄운 상태에서 실행한다. 실제 TCP 연결을 사용하므로 transport mock의 완벽한 스케줄을 가정하지 않는다.

```python
import asyncio
from collections import Counter
import httpx


async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8024", timeout=2) as client:
        responses = await asyncio.gather(*[client.get("/work") for _ in range(20)])
        print("status_counts", dict(Counter(r.status_code for r in responses)))
        print("after_burst", (await client.get("/state")).json())
        short = await client.get("/work?budget_ms=30")
        print("short_budget", short.status_code)
        print("after_timeout", (await client.get("/state")).json())


asyncio.run(main())
```

충분한 동시 요청에서 200과 503을 함께 기대한다. 먼저 끝난 슬롯을 다음 요청이 받을 수 있으므로 성공 개수를 고정하지 않는다. 종료와 timeout 후 active가 0이고 다음 요청이 성공하는지 확인한다. 앞단 요청 한도도 적용해 입장 대기 작업의 등록량을 제한한다.

## 24.8 Worker 장애와 프로세스 재시작

프로세스가 강제 종료되면 메모리 캐시와 Task는 사라진다. `finally`가 항상 실행되는 것도 아니다. OS는 프로세스의 소켓·파일 자원을 회수할 수 있지만 외부 시스템에 이미 기록한 효과는 남는다. 중요한 작업은 메모리의 완료 플래그만 믿지 말고 영속 상태와 멱등 재처리를 사용한다.

같은 입력이 매번 crash를 일으키면 restart loop가 생긴다. 원인·종료 코드를 기록하고 입력을 격리한다. 준비된 worker에만 트래픽을 보내며 종료 전에는 새 요청을 제거한다. worker 장애 후 남은 인스턴스가 추가 부하를 감당할 여유도 계산한다.

## 24.9 대량 트래픽에서의 과부하 제어

과부하는 입력량이 처리 능력을 넘는 상태다. 큐를 늘리면 즉시 실패가 줄어 보일 수 있지만 기다림과 메모리 사용이 늘고 deadline을 넘긴 작업이 계속 수행된다. bounded queue, 짧은 admission wait, 동시 실행 한도, 사용자별 rate limit을 조합한다. 클라이언트가 빠르게 재시도하지 않도록 429 또는 503과 재시도 지침을 제공한다.

rate limit은 시간당 양, concurrency limit은 동시에 점유하는 자원, queue capacity는 기다리는 양을 제한한다. 셋은 대체 관계가 아니다. 빠른 요청과 긴 AI 요청을 같은 슬롯으로 섞으면 긴 요청이 전체 용량을 잡을 수 있다. 업무별 bulkhead와 우선순위, 사용자 공정성을 설계한다. 재시도도 일반 요청과 같은 총 예산 안에 포함하고 장애 대상에는 차단기를 적용한다.

서버만 제한하면 충분하지 않을 수 있다. 프록시의 body 크기와 연결 수, Uvicorn 동시성, HTTP 풀, DB 풀, worker queue가 연결된 시스템이다. 한 계층의 대기 한도가 다른 계층보다 길면 이미 떠난 요청의 일을 계속 수행할 수 있다. 전체 deadline과 자원 소유자를 그림으로 그려 경계를 맞춘다. 의도적으로 거절하는 상태를 건강한 과부하 방어로 해석하고 일반 프로그래밍 오류와 구별한다.

## 24.10 장애 재현 및 원인 분석 실습

실패 가설을 쓰고 재현 조건을 줄인다. race는 await 경계, 풀 고갈은 반환 누락, 블로킹은 긴 동기 구간으로 재현한다. 실험은 로컬의 폐기 가능한 환경에서 수행한다.

아래 `incident_checks.py`는 **완전 실행 예제**다. 실제 DB가 없는 작은 동시성 실험이며 race와 취소 후 슬롯 반환을 결정적으로 확인한다. 표준 라이브러리만 필요하다.

```python
import asyncio
from contextlib import suppress


async def lost_update():
    value = 0
    arrived = 0
    both_ready = asyncio.Event()

    async def increment():
        nonlocal value, arrived
        previous = value
        arrived += 1
        if arrived == 2:
            both_ready.set()
        await both_ready.wait()
        await asyncio.sleep(0)
        value = previous + 1

    await asyncio.gather(increment(), increment())
    assert value == 1  # 두 요청을 처리했지만 갱신 하나가 사라졌다.


async def locked_update():
    value = 0
    lock = asyncio.Lock()

    async def increment():
        nonlocal value
        async with lock:
            previous = value
            await asyncio.sleep(0)
            value = previous + 1

    await asyncio.gather(*[increment() for _ in range(20)])
    assert value == 20


async def cancel_and_release():
    slot = asyncio.Semaphore(1)
    entered = asyncio.Event()
    cleaned = asyncio.Event()

    async def worker():
        async with slot:
            entered.set()
            try:
                await asyncio.sleep(60)
            finally:
                cleaned.set()

    task = asyncio.create_task(worker())
    await entered.wait()
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    assert task.cancelled() and cleaned.is_set()
    async with asyncio.timeout(0.1):
        await slot.acquire()
    slot.release()


async def main():
    await lost_update()
    await locked_update()
    await cancel_and_release()
    print("race reproduced; lock and cancellation cleanup passed")


asyncio.run(main())
```

`python incident_checks.py`의 메시지가 나오면 세 실험이 통과한다. locked_update는 같은 프로세스에서만 규칙을 보장한다는 한계를 기록한다. 취소가 잘 전달되고 정리가 끝난 후 자원을 다시 획득할 수 있다는 것은 정상 완료 테스트보다 중요한 추가 증거다. 단순히 task.cancel을 호출했다는 사실만으로 평가를 끝내지 않는다.

## 실무 장애 분석의 순서

영향 범위·시작 시점을 최근 배포, endpoint, 입력 크기, worker와 연결한다. 불필요한 재시도와 작업 등록을 제한하고 request ID·trace, loop lag, pool wait, Task·큐 수로 자원이 붙잡힌 위치를 찾는다.

수정 후 정상 기능, 과부하 거절, timeout 반환, 중단 정리, 재시작 복구를 확인한다. 관측 사실과 가설을 구분하고 왜 다시 쌓이지 않는지 증거를 남긴다.

## 확인 문제와 해설

1. timeout 타이머가 있으면 블로킹 함수도 제시간에 멈추는가? **해설:** 아니다. 이벤트 루프가 실행 기회를 얻어야 취소가 전달된다. 동기 SDK 자체 timeout과 실행 위치를 함께 설계한다.
2. `CancelledError`를 잡고 정상 결과를 반환하면 왜 문제인가? **해설:** 상위 TaskGroup과 timeout의 취소 계약이 깨지고 정리·종료가 지연될 수 있다. 필요한 정리 후 취소를 전파한다.
3. `asyncio.Lock`으로 문서 중복 색인이 모든 worker에서 방지되는가? **해설:** 프로세스 간에 공유되지 않는다. 저장소의 unique·원자 상태 전이·버전 조건과 외부 멱등성이 필요하다.
4. 503이 증가했지만 메모리가 안정되고 성공 RPS가 유지된다. 무조건 악화인가? **해설:** 의도된 admission 방어일 수 있다. 사용자 성공 목표와 용량을 확인하며 무한 대기로 장애를 퍼뜨리는 상황과 구별한다.
5. 실습 통과 기준은 무엇인가? **해설:** lost update를 결정적으로 재현하고 같은 루프의 lock으로 막으며, 취소 후 정리와 슬롯 재획득이 성공한다. HTTP burst와 deadline 이후 active가 기준으로 돌아오고 다음 요청이 성공해야 한다.

## 요약과 다음 장

안정성은 자원 수명과 실패 경계를 명시할 때 얻을 수 있다. 취소는 협력적이고, timeout은 실행 위치에 영향을 받으며, 다중 프로세스 공유 규칙은 저장소에서 보장한다. 과부하에서는 기다림을 무한히 늘리지 않고 제한된 용량을 명시적으로 배분한다. 다음 장은 이 원리를 높은 외부 지연과 비용이 있는 LLM 서비스에 적용한다.

## 공식 참고자료

- [Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html)
- [Python asyncio synchronization](https://docs.python.org/3.12/library/asyncio-sync.html)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Python tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html)
- [Uvicorn settings](https://uvicorn.dev/settings/)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 23장 로깅과 모니터링](../23-observability/chapter.md) · [25장 FastAPI와 LLM API →](../25-llm-api/chapter.md)
