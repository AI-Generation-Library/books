---
title: "07장. FastAPI의 동시성 처리"
description: "async 엔드포인트·동기 엔드포인트·직접 호출한 helper의 실행 위치를 구분한다. 스레드와 프로세스의 자원 비용을 계산하고, 워커 수와 하위 시스템 한도를 함께 설계한다. 과부하에서 대기를 무한히 늘리는 대신 제한과 거절을 사용한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 7
part: 2
---

> PART 2. FastAPI 내부 동작 원리 · 핵심 장

## 학습 목표와 도입 사례

async 엔드포인트·동기 엔드포인트·직접 호출한 helper의 실행 위치를 구분한다. 스레드와 프로세스의 자원 비용을 계산하고, 워커 수와 하위 시스템 한도를 함께 설계한다. 과부하에서 대기를 무한히 늘리는 대신 제한과 거절을 사용한다.

레거시 검색 라이브러리를 async 엔드포인트에서 호출했더니 다른 API까지 느려졌다고 생각해 보자. 개발자는 “FastAPI는 비동기니까 괜찮다”고 예상했다. 문제는 프레임워크 이름이 아니라 그 라이브러리가 실행되는 스레드와 기다리는 방식이다.

## 7.1 async def와 def의 실행 차이

FastAPI가 엔드포인트나 의존성으로 호출하는 일반 `def` 함수는 스레드 실행 경계를 통해 처리된다. `async def` 함수는 비동기 실행 흐름에서 기다린다. 핵심은 “FastAPI가 호출하는 함수”라는 조건이다. 이 계약은 [FastAPI 동시성 설명](https://fastapi.tiangolo.com/async/)에 명시되어 있다.

async 엔드포인트 안에서 `slow_sync_helper()`를 직접 호출하면 일반 Python 함수 호출이다. helper에 def가 붙었다고 자동으로 스레드에 옮겨지는 것이 아니다. 비동기 드라이버로 교체하거나 명시적으로 스레드 실행 API를 써야 한다.

| 코드 위치 | 기본 실행 모델 | 블로킹 I/O의 영향 |
|---|---|---|
| FastAPI가 호출하는 async 엔드포인트 | 이벤트 루프의 비동기 흐름 | 직접 블로킹하면 루프를 막음 |
| FastAPI가 호출하는 def 엔드포인트 | 외부 스레드 실행 경계 | 스레드를 점유함 |
| async 엔드포인트가 직접 부른 def helper | 호출한 루프 스레드 | 직접 블로킹하면 루프를 막음 |
| `await asyncio.to_thread(helper)` | asyncio 스레드 실행 경계 | 별도 스레드를 점유함 |

작은 메모리 연산을 처리하는 helper까지 모두 스레드로 보내면 전환 비용과 설계 복잡성만 늘 수 있다. 함수의 이름과 문법보다 실제로 얼마나 오래 무엇을 기다리는지 판단한다.

## 7.2 스레드 풀과 이벤트 루프

스레드 풀은 사용할 수 있는 스레드 실행 용량을 제한한다. 동기 DB나 파일 작업을 루프 밖으로 보내도 스레드 수가 무한한 것은 아니다. 긴 동기 작업이 풀을 점유하면 새로운 동기 엔드포인트나 의존성도 기다린다.

Starlette의 동기 작업 경계는 AnyIO 기반이며, [공식 스레드 풀 문서](https://www.starlette.io/threadpool/)에는 기본 limiter 40 tokens가 설명되어 있다. 이 숫자는 특정 실행 규약의 기본값이다. HTTP 동시 요청 최대 40이라는 의미가 아니고 전체 서비스 용량 보장도 아니다. 사용하는 버전·설정의 실제 값을 확인한다.

`asyncio.to_thread`의 실행 용량과 AnyIO의 limiter를 같은 설정 하나로 취급하지 않는다. 둘 다 스레드를 사용하지만 코드 경로와 설정이 다를 수 있다. 스레드 수를 늘리면 동시 DB 호출과 메모리 비용도 늘어난다. 원래 느린 시스템에 더 많은 요청을 보내는 것이 해결인지 먼저 판단한다.

## 7.3 요청별 Task 생성과 실행

일반적인 Uvicorn HTTP 처리에서 각 요청의 ASGI 실행은 비동기 작업으로 관리된다. 연결·응답·배경 작업의 구체적 관리 방식은 서버 버전에 영향을 받는다. 중요한 점은 요청들이 같은 이벤트 루프의 실행 시간을 나누며, 하나의 요청 안에서 추가 Task를 만들 수도 있다는 사실이다.

한 요청에서 검색, 설정, 근거 조회를 동시에 수행하면 외부 호출 수는 요청 수보다 많다. 동시 HTTP 요청이 100개이고 각각 세 호출을 생성한다는 가정에서는 하위 API에 300개 작업이 몰릴 수 있다. 웹 요청 수만 제한하면 하위 시스템의 실제 부하를 놓칠 수 있다.

## 7.4 다수 동시 요청의 처리 과정

요청 A가 비동기 DB 응답을 기다릴 때 요청 B의 입력 검증과 함수 실행이 진행될 수 있다. 요청 B도 대기하면 C가 실행된다. DB 응답이 도착한 A는 실행 가능한 상태가 되지만, 현재 실행 중인 코드가 루프를 놓아야 이어질 수 있다.

```text
A: 함수 시작 ─ DB 대기 ────────────────── 결과 처리
B:             함수 시작 ─ HTTP 대기 ───── 결과 처리
C:                          짧은 조회 ─ 응답
```

반대로 A가 큰 CPU 연산을 계속하면 B와 C는 준비되어 있어도 늦어진다. 따라서 긴 지연을 조사할 때 함수 자체 시간과 실행 기회를 기다린 시간을 구분해야 한다. 이벤트 루프 지연 측정이 유용한 이유다.

## 7.5 스레드와 프로세스의 차이

스레드는 같은 프로세스의 메모리를 공유한다. 공유 데이터 접근에는 경쟁 조건을 고려해야 한다. 프로세스는 기본적으로 독립된 주소 공간을 갖고 프로세스 사이 데이터 전달에는 직렬화나 IPC가 필요하다. 한 프로세스의 전역 dict는 다른 워커의 dict와 같지 않다.

공유 메모리가 편하다는 이유만으로 요청별 DB 세션을 공유하면 안 된다. 세션은 트랜잭션과 ORM 상태를 갖는 작업 단위다. 다른 Task나 스레드에서 동시에 사용하는 문제는 연결 풀을 공유하는 문제와 다르다.

프로세스 경계는 CPU 작업을 분리하는 데 도움이 되지만 인자·결과 직렬화와 메모리 비용이 있다. 큰 문서 전체를 작업마다 복사하는 방식은 병목을 다른 곳으로 옮길 수 있다. 파일이나 객체 저장소의 참조를 전달하는 설계를 검토한다.

## 7.6 Uvicorn Worker와 멀티프로세싱

`--workers 2`는 서버 프로세스를 여러 개 두는 구성이다. 각 워커의 이벤트 루프와 메모리·연결 풀은 독립적이다. 요청 라우팅을 통해 전체 처리 기회가 늘 수 있지만, 같은 사용자 요청이 같은 워커로 간다는 보장은 기본 설계에 넣지 않는다.

워커 수를 늘리면 DB 연결 예산도 커진다. 워커 네 개가 각각 최대 15개 연결을 사용한다는 가정에서는 애플리케이션 한 인스턴스가 최대 60개 연결을 요구할 수 있다. 인스턴스까지 늘리면 다시 곱해진다. 서버 CPU 수 공식만 보고 워커를 정하지 않는다.

리로드와 멀티워커는 다른 목적이며 Uvicorn에서 함께 사용하는 옵션이 아니다. 컨테이너 환경에서는 여러 워커를 한 컨테이너에 둘지, 한 워커 컨테이너를 여러 개 둘지 운영 방식과 종료·관찰 비용을 기준으로 정한다.

## 7.7 GIL과 Python 병렬 처리의 제약

이 책의 기본 기준인 GIL 있는 CPython에서는 여러 스레드가 순수 Python 바이트코드를 실행하는 방식에 제약이 있다. 따라서 CPU 연산을 스레드로 옮긴 것만으로 CPU 코어를 모두 사용할 것이라고 기대하지 않는다. I/O 대기와 GIL을 해제하는 네이티브 연산은 다른 결과를 보일 수 있다.

Python 버전과 빌드에 따라 free-threaded 실행 선택지가 존재할 수 있지만 이 책의 기본 실습 전제가 아니다. 실제 도입 시 패키지 지원과 스레드 안전성, 측정 결과를 검토한다. GIL이라는 이름 하나로 모든 Python 배포판과 라이브러리의 동작을 단정하지 않는다.

## 7.8 동시성 제한과 백프레셔

동시성 제한은 동시에 진행하는 작업 수를 줄이는 제어다. 백프레셔는 소비자가 처리할 수 없는 속도로 작업이 들어올 때 생산자에 대기·거절·속도 조절을 전달하는 제어다. 실행 수만 제한하고 대기 Task를 무한히 쌓으면 메모리와 deadline 문제는 남는다.

따라서 세 가지를 함께 정한다. 실행 중인 작업 수, 기다릴 수 있는 작업 수, 기다릴 수 있는 시간이다. 일부 요청은 `429` 또는 `503`으로 거절하고 재시도 조건을 알려주는 편이 모두를 길게 기다리게 하는 것보다 안정적일 수 있다. 어떤 코드를 쓸지는 사용자 한도인지 서비스 용량 고갈인지에 따라 결정한다.

`asyncio.Semaphore`는 프로세스 안의 한도를 제공한다. 워커 네 개에 한도 4를 두면 서비스 전체 한도가 4가 아니라 최대 16으로 달라질 수 있다. 외부 모델 API의 계정 한도는 Redis 같은 공유 조정이나 중앙 작업 큐로 별도 관리한다.

## 7.9 동기 코드와 비동기 코드 혼용 시 주의점

블로킹 I/O는 명시적으로 루프 밖에 두고, 비동기 라이브러리는 await 흐름에 둔다. 동기 DB 세션을 한 스레드에서 만들고 다른 스레드로 넘기는 식의 우연한 수명 관리는 피한다. 사용하는 라이브러리의 스레드 안전 계약을 확인한다.

asyncio.Lock을 잡은 채 동기 함수를 오래 실행하면 루프가 막히고 락의 효과도 기대와 달라진다. 반대로 threading.Lock을 루프에서 경합하면 루프 스레드가 대기 상태에 막힐 수 있다. 락은 공유 자원과 실행 모델에 맞춰 선택하고, 보호하는 범위를 줄인다.

## 기본 실습: 네 가지 실행 경로 비교

**완전 실행 예제.** FastAPI·Uvicorn 환경에서 `main.py`를 다음으로 만든다. `/blocking`은 잘못된 코드를 관찰하는 로컬 실험용 경로다.

```python
import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

def legacy_io():
    time.sleep(0.1)
    return {"mode": "legacy", "pid": os.getpid()}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.gate = asyncio.Semaphore(4)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/async")
async def async_io():
    await asyncio.sleep(0.1)
    return {"mode": "async", "pid": os.getpid()}

@app.get("/sync")
def sync_io():
    return legacy_io()

@app.get("/blocking")
async def blocking_io():
    return legacy_io()  # 루프 스레드를 직접 막는다.

@app.get("/threaded")
async def threaded_io():
    return await asyncio.to_thread(legacy_io)

@app.get("/limited")
async def limited_io(request: Request):
    gate = request.app.state.gate
    try:
        async with asyncio.timeout(0.02):
            await gate.acquire()
    except TimeoutError:
        raise HTTPException(status_code=503, detail="capacity_exhausted",
                            headers={"Retry-After": "1"})
    try:
        await asyncio.sleep(0.1)
        return {"mode": "limited"}
    finally:
        gate.release()
```

`python -m uvicorn main:app --workers 1`로 실행한다. HTTPX를 설치하고 `load.py`를 만든다.

```python
import asyncio
from collections import Counter
from time import perf_counter

import httpx

async def probe(client: httpx.AsyncClient, path: str):
    started = perf_counter()
    responses = await asyncio.gather(*[client.get(path) for _ in range(12)])
    print(path, round(perf_counter() - started, 3),
          dict(Counter(response.status_code for response in responses)))

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        for path in ("/async", "/sync", "/blocking", "/threaded", "/limited"):
            await probe(client, path)

if __name__ == "__main__":
    asyncio.run(main())
```

`python load.py`를 실행하면 blocking이 다른 경로보다 기다림을 겹치기 어려운 방향으로 나타난다. 제한 경로는 일정 수만 성공하고 일부 요청을 거절할 수 있다. 정확한 성공 수와 시간은 요청 도착 분포에 따라 달라진다. 실제 네트워크 없이 ASGITransport로 시험해도 실행 모델을 관찰할 수 있지만 서버 연결 한도까지 검증한 것은 아니다.

이 코드는 대기 시간을 제한하지만 순간 생성된 대기 Task의 총수를 엄격히 제한하지는 않는다. 운영에서는 서버 admission limit과 bounded queue를 추가한다. 이것이 교육용 Semaphore 예제와 완전한 과부하 제어의 차이다.

## CPU 작업 분리의 실행 구조

다음은 **별도 파일의 완전 실행 예제**다. CPU 작업 함수는 모듈 최상위에 두어 프로세스에서 가져올 수 있게 하고 프로세스 풀은 lifespan에서 만든다. `cpu_app.py`로 저장한다.

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Query, Request

def compute_checksum(size: int) -> int:
    return sum(value * value for value in range(size))

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = ProcessPoolExecutor(max_workers=2)
    app.state.pool = pool
    try:
        yield
    finally:
        await asyncio.to_thread(pool.shutdown, wait=True, cancel_futures=True)

app = FastAPI(lifespan=lifespan)

@app.get("/checksum")
async def checksum(request: Request, size: Annotated[int, Query(ge=1, le=1_000_000)]):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(request.app.state.pool, compute_checksum, size)
    return {"checksum": result}
```

`python -m uvicorn cpu_app:app`로 실행한다. 이 예제는 CPU 분리 경계만 보여주며 무한 작업 접수를 막는 큐 한도와 내구성을 제공하지 않는다. 서버 워커가 둘이면 각 워커의 프로세스 풀도 별도로 생긴다. 실행 중인 프로세스 작업을 클라이언트 취소가 즉시 중단한다는 보장도 없다. 장시간 작업에는 18장의 큐 설계가 적합하다.

## 실무 적용과 성능·주의사항

서비스의 동시성 예산을 표로 만들자. HTTP admission, 동기 스레드, DB 연결, 외부 API 연결, 모델 계정 한도를 적고 인스턴스·워커 수를 곱한다. 한 부분의 한도를 늘리면 다른 부분에서 병목이 생길 수 있다. API 처리량은 가장 좁은 공유 자원과 요청별 점유 시간의 영향을 받는다.

단순 응답 경로로 워커 효과를 확인한 뒤 실제 경로에서도 부하를 측정한다. 빠른 데모 경로만으로 DB와 모델이 연결된 서비스의 처리량을 보장하지 않는다. 리로드·디버거·접속 로그 설정 등 측정 조건도 고정한다.

메모리 캐시는 워커별이고 asyncio 락도 워커별이다. 사용자별 호출 제한, 작업 상태, 대화 기록을 전역 변수에 두면 인스턴스 확장 시 일관성이 깨진다. 공유 저장소의 원자 연산과 영속성을 검토한다.

## 확인 문제와 해설

1. async 경로에서 직접 부른 def helper는 어디서 실행되는가?
2. 워커 세 개, 프로세스별 DB 최대 연결 10개, 인스턴스 두 개라는 가정의 연결 예산은?
3. Semaphore 4만 두면 메모리 과부하를 완전히 막을 수 있는가?
4. 실습: blocking 요청 중 가벼운 async 경로를 요청해 지연이 함께 늘어나는지 관찰하라.

**해설.** 1번은 호출한 루프 스레드다. 2번은 최대 60개에 다른 서비스·관리용 연결을 별도로 고려한다. 3번은 아니다. 대기 작업과 대기 시간, 워커별 한도 범위를 함께 제한해야 한다. 4번은 두 경로의 타임라인을 기록하고 블로킹 제거 후 비교한다. 같은 컴퓨터에서 부하 생성이 CPU를 독점하지 않도록 한다.

## 요약과 다음 장

동시성의 판단 단위는 함수가 실행되는 곳과 점유하는 자원이다. 스레드·프로세스·비동기 대기를 혼합할 때 한도와 수명을 함께 설계해야 한다. 다음 장은 이러한 리소스를 요청에 제공하고 정리하는 의존성과 미들웨어를 다룬다.

## 공식 참고자료

- [FastAPI async/await](https://fastapi.tiangolo.com/async/)
- [Starlette 스레드 풀](https://www.starlette.io/threadpool/)
- [Uvicorn 워커·제한 설정](https://www.uvicorn.org/settings/)
- [Python asyncio 스레드 실행](https://docs.python.org/3.12/library/asyncio-task.html#running-in-threads)
- [Python ProcessPoolExecutor](https://docs.python.org/3.12/library/concurrent.futures.html#processpoolexecutor)
- [Python threading](https://docs.python.org/3.12/library/threading.html)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 06장 Python asyncio와 이벤트 루프](../06-asyncio-event-loop/chapter.md) · [08장 의존성 주입과 미들웨어 →](../08-dependencies-middleware/chapter.md)
