---
title: "06장. Python asyncio와 이벤트 루프"
description: "코루틴 객체·Task·Future를 구분하고, await가 언제 실행 기회를 넘기는지 설명한다. 구조화된 동시 실행과 취소를 사용하고, I/O 대기와 CPU 작업을 서로 다른 전략으로 처리한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 6
part: 2
---

> PART 2. FastAPI 내부 동작 원리 · 핵심 장

## 학습 목표와 도입 사례

코루틴 객체·Task·Future를 구분하고, await가 언제 실행 기회를 넘기는지 설명한다. 구조화된 동시 실행과 취소를 사용하고, I/O 대기와 CPU 작업을 서로 다른 전략으로 처리한다.

문서 검색 API가 검색 DB와 사용자 설정 API를 각각 기다린다고 생각해 보자. 두 결과가 서로 독립적이면 기다리는 시간을 겹칠 수 있다. 하지만 둘을 동시에 실행한다고 CPU가 두 개 생기는 것은 아니다. 비동기 설계의 핵심은 “누가 기다리며, 기다리는 동안 누가 실행할 수 있는가”다.

## 6.1 동기, 비동기, 병렬 처리의 차이

동기 호출은 작업이 끝날 때까지 호출 흐름이 결과를 기다리는 모델이다. 비동기 호출은 작업의 진행과 대기를 분리해 다른 작업을 실행할 기회를 제공한다. 동시성은 여러 작업이 같은 기간에 진행되는 성질이고 병렬성은 같은 순간에 여러 실행 자원이 실제 계산하는 성질이다.

한 사람이 물을 올리고 끓는 동안 채소를 손질하는 것은 동시 진행에 가깝다. 두 사람이 각각 손질하는 것은 병렬 작업이다. 이 비유에서 물이 끓기를 기다리는 시간은 I/O 대기이고 손질 시간은 CPU 계산이라고 생각할 수 있다. 다만 실제 서버에서는 제한된 연결 풀과 외부 한도가 추가된다.

작업 A와 B가 각각 네트워크를 200ms 기다린다고 가정하자. 순차 실행은 대략 400ms, 독립적인 동시 실행은 대략 200ms에 추가 비용을 더한 시간이 될 수 있다. 가정에 따른 설명이지 실제 성능 보장이 아니다. 외부 API가 한 번에 한 요청만 받거나 CPU 작업이 크면 결과가 달라진다.

## 6.2 이벤트 루프의 동작 원리

이벤트 루프는 실행 가능한 작업, 타이머, I/O 완료를 관리한다. 한 스레드에서 돌아가는 일반적인 asyncio 루프는 준비된 Task를 실행하고, 그 Task가 대기 상태가 되면 다른 준비된 일을 수행한다. OS의 I/O 준비 통지와 비동기 드라이버가 이 대기를 연결한다.

```text
준비된 Task 실행
  → I/O가 아직 안 끝났음
  → Task 대기 등록
  → 다른 Task 실행
  → I/O 완료 통지
  → 기다리던 Task를 실행 가능 상태로 전환
  → 이후 실행 기회에 이어서 진행
```

루프는 일반 Python 코드의 긴 계산을 임의로 잘라서 교대 실행하는 선점 스케줄러가 아니다. Task가 실행 기회를 반환하지 않으면 같은 루프의 다른 Task도 기다린다. `async def` 안에서 `time.sleep()`을 호출하면 그 잠은 루프 스레드를 막는다.

`await`가 문법에 등장했다고 언제나 실제 실행 전환이 일어나는 것도 아니다. 기다리는 객체가 이미 완료되어 있다면 바로 이어서 진행할 수 있다. 공정한 실행을 기대하며 모든 코드 줄 사이에 의미 없는 await를 넣는 대신, 실제 I/O와 작업 경계를 설계한다.

## 6.3 Coroutine과 Task의 차이

`async def` 함수를 호출하면 일반적으로 코루틴 객체가 만들어진다. 일반 동기 함수처럼 본문을 끝까지 즉시 실행한 결과가 아니다. 해당 객체를 await하거나 Task로 예약해야 실행된다. 기다리지 않은 코루틴 경고가 나오면 “함수는 호출했는데 실행 흐름에 연결하지 않았다”는 단서다.

Task는 코루틴을 이벤트 루프에서 진행시키는 실행 단위다. `asyncio.create_task()`로 예약하면 현재 루프가 실행 기회를 줄 때 진행한다. 명시적으로 생성한 Task의 소유자는 누구인지 정해야 한다. 결과·예외·취소·종료까지 관리하지 않으면 떠돌이 작업이 생긴다.

```python
# 개념 예제: 실제로 실행하려면 async main 안에 놓는다.
coroutine = fetch_document()          # 코루틴 객체
document = await coroutine           # 현재 Task가 이 결과를 기다림
task = asyncio.create_task(fetch_document())  # 별도의 Task로 예약
document = await task                 # 결과와 예외를 관찰
```

위 helper는 관계를 보여주기 위한 이름이다. 아래 실습에는 모든 함수 구현을 제공한다. FastAPI 엔드포인트 안에서 `asyncio.run()`으로 별도 루프를 만들지 않는다. 이미 서버의 비동기 실행 흐름 안에 있으므로 await를 사용한다.

## 6.4 async와 await의 실제 동작

await는 awaitable의 완료를 기다리고 결과를 얻는다. awaitable에는 코루틴, Task, Future가 있다. 이때 I/O 대기로 실행 기회를 반환하면 다른 작업을 진행할 수 있다. `return await helper()`는 내부 helper의 결과를 기다리며, 단순히 코루틴 객체를 반환하는 것과 다르다.

동기 함수와 async 함수는 함수 정의만 다를 뿐이라고 생각하기 쉽다. 그러나 호출 계약이 다르다. 동기 함수는 직접 결과를 반환하고, async 함수는 비동기 흐름에서 기다려야 하는 객체를 만든다. 일반 함수에서 async helper를 호출한 뒤 그 객체를 JSON에 넣으면 원하는 결과가 아니다.

async 코드가 어떤 I/O를 기다리는지 추적하자. `await client.get()`은 비동기 HTTP 클라이언트의 대기이고, `requests.get()`은 일반 호출이다. 이름이 비슷한 API라도 실제 실행 방식이 다르다.

## 6.5 asyncio.create_task와 gather

서로 독립적인 작업을 동시에 기다릴 때 `gather`를 사용할 수 있다. 결과는 입력 순서로 모인다. 가장 먼저 끝난 결과부터 제공하는 도구라는 뜻은 아니다. 모든 결과가 필요하지 않다면 다른 완료 순서 처리 전략을 선택한다.

중요한 차이는 실패다. 기본 `gather`에서 한 작업의 예외가 전달되어도 다른 작업을 자동으로 모두 취소한다고 가정하면 안 된다. 호출자의 수명과 남은 작업의 수명이 달라질 수 있다. `return_exceptions=True`는 실패를 결과처럼 돌려줄 뿐 성공으로 바꾸지는 않는다.

Python 3.11부터 제공되는 `TaskGroup`은 관련 작업의 수명을 하나의 블록으로 관리할 수 있다. 하위 작업의 일반 예외가 발생하면 다른 작업을 취소하고 정리한다. 여러 실패는 ExceptionGroup으로 표현될 수 있다. 선택 기준은 짧은 문법보다 실패 시 나머지 작업을 어떻게 할지다. [asyncio Task 문서](https://docs.python.org/3.12/library/asyncio-task.html)에서 두 도구의 계약을 확인한다.

외부 시스템을 1,000개 호출해야 한다고 1,000개의 Task를 무조건 만드는 것은 좋은 설계가 아니다. 동시 실행 수, 대기 작업 수, 총 deadline을 제한해야 한다. Semaphore는 실행 중인 수를 제한해도 생성된 Task의 개수까지 자동으로 제한하지 않는다. 7장과 16장에서 구체화한다.

## 6.6 Future와 비동기 작업 완료 처리

Future는 아직 완료되지 않은 결과를 나타내는 객체다. 저수준 콜백 기반 코드가 완료 시 결과나 예외를 설정하고, 기다리는 Task가 그 결과를 받도록 연결할 수 있다. 일반 애플리케이션에서 모든 I/O를 직접 Future로 구현할 필요는 없다. 고수준 비동기 라이브러리를 사용하는 편이 안전하다.

**완전 실행 예제.** 표준 라이브러리만 사용한다. `future_lab.py`에 저장한다.

```python
import asyncio

async def main():
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def complete():
        if not future.done():
            future.set_result("준비 완료")

    timer = loop.call_later(0.05, complete)
    try:
        print(await future)
    finally:
        timer.cancel()

if __name__ == "__main__":
    asyncio.run(main())
```

`python future_lab.py`로 실행하면 잠시 후 준비 완료가 출력된다. 콜백이 Future를 완료시켜 기다리던 흐름이 이어진다. `done()` 확인은 이미 취소되거나 완료된 Future에 결과를 다시 설정하는 일을 피한다. 다른 스레드에서 루프와 상호작용하려면 스레드 안전한 예약 API가 필요하며 Future를 임의 스레드에서 직접 바꾸지 않는다.

## 6.7 JavaScript 이벤트 루프와 비교

JavaScript의 Promise와 Python의 awaitable은 완료되지 않은 작업을 기다린다는 점에서 연결해 생각할 수 있다. 그러나 세부 실행 순서가 같지는 않다. 일반적인 JavaScript async 함수는 호출되면 첫 대기 지점까지 본문을 진행한다. Python async 함수 호출은 보통 코루틴 객체를 만들고 예약이나 await 전에는 본문을 진행하지 않는다.

Node.js의 이벤트 루프, 마이크로태스크 큐와 Python asyncio의 Task 예약 정책을 일대일 대응시키지 않는다. Python에 JavaScript의 특정 Promise 순서를 기대하면 로그 순서를 잘못 예측할 수 있다. 각 런타임에서 직접 작은 프로그램으로 확인한다. JavaScript async 함수의 호출 계약은 [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)에서 확인할 수 있다.

두 환경에 공통으로 유용한 습관은 대기를 블로킹 계산으로 바꾸지 않고, 실행한 비동기 작업의 예외를 관찰하고, 한도 없이 작업을 쌓지 않는 것이다. Node 경험자가 Python으로 넘어올 때는 라이브러리가 실제 비동기 드라이버인지 먼저 확인한다.

## 6.8 비동기 I/O와 CPU-bound 작업

HTTP 호출과 비동기 DB 조회는 I/O 대기가 큰 작업이다. 대기 동안 루프가 다른 요청을 처리할 수 있다. 텍스트를 거대한 정규식으로 파싱하거나 이미지를 인코딩하거나 Python 코드로 벡터를 계산하는 작업은 CPU 시간을 사용한다. async 함수로 감싸도 계산 자체가 빨라지거나 병렬화되지는 않는다.

블로킹 I/O만 제공하는 기존 라이브러리에는 `asyncio.to_thread()`가 연결 수단이 될 수 있다. 하지만 스레드에는 개수·메모리·취소 한계가 있다. 기다리는 Task를 취소해도 실행 중인 동기 함수가 자동으로 안전하게 중단되지는 않는다. 대량 CPU 작업은 별도 프로세스나 작업 큐를 검토한다.

일반적인 GIL 있는 CPython에서 순수 Python CPU 계산은 스레드 수를 늘린다고 기대한 병렬 실행이 보장되지 않는다. 네이티브 라이브러리가 GIL을 해제하는지에 따라서도 결과가 다르다. “Python 스레드는 언제나 쓸모없다”와 “스레드면 언제나 CPU 병렬화된다” 모두 틀린 판단이다.

## 6.9 블로킹 코드가 서버에 미치는 영향

서버의 이벤트 루프는 요청 처리 외에 타임아웃, 소켓 수신, 스트림 전송, 건강 검사와 연결된다. 루프를 1초 막으면 특정 엔드포인트만 1초 느려지는 것으로 끝나지 않을 수 있다. 다른 Task가 대기에서 깨어날 기회도 늦어진다.

이 지연은 외부 API가 느린 것과 다르게 관찰된다. 외부 I/O 대기 중에는 루프가 가벼운 요청을 처리할 수 있지만, 루프 자체가 막히면 관계없는 요청도 함께 늦어진다. CPU 사용률, 이벤트 루프 지연, 의존성별 타이밍을 함께 보면 원인을 좁힐 수 있다.

## 기본 실습: 순차·동시 실행과 취소

**완전 실행 예제.** 표준 라이브러리만 사용한다. 다음을 `asyncio_lab.py`로 저장한다.

```python
import asyncio
from time import perf_counter

async def simulated_io(name: str, delay: float = 0.1) -> str:
    await asyncio.sleep(delay)
    return name

async def sequential():
    return [await simulated_io(name) for name in ("검색", "설정", "권한")]

async def concurrent():
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(simulated_io(name)) for name in ("검색", "설정", "권한")]
    return [task.result() for task in tasks]

async def cancellable(entered: asyncio.Event):
    try:
        entered.set()
        await asyncio.sleep(60)
    finally:
        print("자원 정리")

async def main():
    for operation in (sequential, concurrent):
        started = perf_counter()
        print(operation.__name__, await operation(), round(perf_counter() - started, 3))

    try:
        async with asyncio.timeout(0.02):
            await simulated_io("시간 초과", 0.1)
    except TimeoutError:
        print("deadline 초과")

    entered = asyncio.Event()
    task = asyncio.create_task(cancellable(entered))
    await entered.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("취소 결과 확인")

if __name__ == "__main__":
    asyncio.run(main())
```

`python asyncio_lab.py`로 실행한다. 순차 실행은 약 0.3초, 동시 실행은 약 0.1초라는 방향을 예상할 수 있지만 정확한 시간은 환경에 따라 달라진다. 이어서 deadline 초과, 자원 정리, 취소 결과 확인을 관찰한다. 취소 요청 후 Task를 await해 종료와 예외를 확인했다는 점이 중요하다.

실험의 `asyncio.sleep`은 네트워크 요청이 아니라 비동기 대기를 모의한 것이다. 성능 결과를 실제 DB나 모델 API의 처리량으로 확대 해석하지 않는다.

## 실무 적용: 관련 작업과 독립 작업의 경계

문서 검색 결과와 사용자 설정 둘 다 있어야 답변을 만들 수 있다면 관련 작업으로 묶어 실패 시 정리한다. 로그 업로드처럼 응답과 수명이 다른 작업은 durable queue에 넘길지, 실패해도 되는 프로세스 내부 작업인지 결정한다. `create_task`를 호출하고 잊는 것으로 이 결정을 대신하지 않는다.

외부 요청에는 요청별 timeout과 전체 deadline이 모두 필요하다. 세 번 재시도할 때 매번 5초 timeout을 쓰면 총 15초 이상 걸릴 수 있다. 전체 요청의 남은 시간에서 하위 작업의 예산을 계산한다. 오류가 난 뒤 이미 실행한 부수효과는 취소로 되돌아가지 않으므로 멱등성도 설계해야 한다.

## 성능 및 주의사항

취소는 협력적으로 전달된다. `CancelledError`는 일반 예외와 상속 관계가 다르므로 무조건 성공 응답으로 바꾸려 하지 않는다. 작업 내부에서는 finally로 정리하고, 취소를 잡았다면 특별한 이유가 없는 한 다시 전파한다. 위 실습의 호출자는 이미 취소된 하위 Task의 결과를 관찰하는 위치이므로 취소를 확인하는 처리가 있다.

락을 잡은 채 느린 네트워크 호출을 기다리면 다른 요청이 그 락 앞에 줄을 선다. 공유 데이터 보호와 외부 I/O 수명은 최소 범위로 나눈다. 한 프로세스의 asyncio.Lock은 다른 워커의 데이터를 보호하지 못한다.

## 확인 문제와 해설

1. async 함수를 호출만 하고 await하지 않으면 무엇이 만들어지는가?
2. 모든 await가 반드시 다른 Task를 실행시키는가?
3. gather의 한 작업이 실패하면 남은 작업이 자동으로 모두 취소되는가?
4. 실습: simulated_io 안의 await sleep을 time.sleep으로 바꾸고 concurrent 시간이 어떻게 달라지는지 설명하라.

**해설.** 1번은 코루틴 객체다. 2번은 아니다. 이미 완료된 awaitable은 바로 이어질 수 있다. 3번은 기본 gather에서 그렇게 가정하면 안 된다. 4번은 루프 스레드가 각 sleep 동안 막혀 대기가 겹치지 못하는 방향으로 바뀐다. 변경한 코드는 의도적으로 잘못된 실험이며 서버 코드에 사용하지 않는다.

## 요약과 다음 장

asyncio는 기다리는 시간을 겹치는 실행 모델이다. Task의 소유자와 실패·취소·정리 정책이 있어야 동시성이 안정성을 해치지 않는다. 다음 장은 이 모델이 FastAPI의 엔드포인트와 스레드·워커에서 어떻게 적용되는지 실험한다.

## 공식 참고자료

- [Python 3.12 코루틴과 Task](https://docs.python.org/3.12/library/asyncio-task.html)
- [Python 이벤트 루프](https://docs.python.org/3.12/library/asyncio-eventloop.html)
- [Python Future](https://docs.python.org/3.12/library/asyncio-future.html)
- [Python asyncio 동기화 기본 요소](https://docs.python.org/3.12/library/asyncio-sync.html)
- [JavaScript async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 05장 ASGI와 Uvicorn의 내부 구조](../05-asgi-uvicorn/chapter.md) · [07장 FastAPI의 동시성 처리 →](../07-concurrency/chapter.md)
