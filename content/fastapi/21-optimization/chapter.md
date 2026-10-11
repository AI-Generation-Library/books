---
title: "21장. FastAPI 성능 최적화"
description: "Knowledge Hub의 지연을 줄이려고 JSON 라이브러리를 바꿨지만 p95가 거의 그대로다. 전체 지연 대부분이 DB 풀 대기였기 때문이다. 성능 개선은 빠르다고 알려진 기능을 모두 도입하는 작업이 아니다. 측정한 병목에 직접 영향을 주는 변경을 작게 적용하고 정확성과 자원 사용을 함께 확인하는 작"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 21
part: 6
---

## 학습 목표와 도입 사례

Knowledge Hub의 지연을 줄이려고 JSON 라이브러리를 바꿨지만 p95가 거의 그대로다. 전체 지연 대부분이 DB 풀 대기였기 때문이다. 성능 개선은 빠르다고 알려진 기능을 모두 도입하는 작업이 아니다. 측정한 병목에 직접 영향을 주는 변경을 작게 적용하고 정확성과 자원 사용을 함께 확인하는 작업이다.

이 장은 20장에서 수집한 latency 분포, loop lag, pool wait를 근거로 최적화 우선순위를 정한다. 실습 기준은 Python 3.12, FastAPI 0.121 이상, Pydantic 2이며 예제는 독립 폴더에서 실행한다. 빠른 수치를 보여 주기 위한 업무 규칙 제거는 허용하지 않는다. 이 장의 시간·연결 수는 설명과 실습 입력이며 실제 성능 개선율을 보증하지 않는다.

## 21.1 이벤트 루프 블로킹 제거

이벤트 루프를 막는 함수는 다른 요청이 실행될 기회를 빼앗는다. 동기 HTTP 요청, 파일 처리, `time.sleep()`, 긴 JSON 파싱, 큰 순수 Python 반복문을 조사한다. async 라우트 안에서 동기 helper를 직접 호출하면 helper도 그 스레드에서 바로 실행된다. FastAPI가 일반 `def` 경로를 별도 실행하는 규칙을 helper 호출에까지 적용한다고 생각하면 안 된다.

I/O 때문에 기다리는 동기 라이브러리는 `asyncio.to_thread()`로 넘길 수 있다. 이것은 GIL 아래의 순수 Python CPU 계산을 자동으로 여러 코어에서 병렬화하는 기법이 아니다. CPU 작업에는 프로세스 풀, 외부 worker, 더 효율적인 알고리즘을 고려한다. 오프로딩 후에도 작업 수를 제한해야 한다. 스레드 수가 제한되어 있어도 제출된 대기 작업이 늘면 메모리와 지연은 증가할 수 있다.

## 21.2 동기 라이브러리와 비동기 라이브러리 선택

비동기 라이브러리로 바꾸면 대기 중 이벤트 루프를 양보할 수 있지만 다른 비용이 사라지는 것은 아니다. 호출이 정말 async I/O인지, 내부에서 sync SDK를 감싸는지, 연결 풀과 cancellation을 지원하는지 확인한다. 문서의 API 이름보다 실제 동작과 자원 정리 계약을 검토한다.

이미 안정적으로 사용 중인 동기 SDK를 즉시 전면 교체하는 대신 경계에서 제한된 스레드 오프로딩을 할 수도 있다. 단, 코루틴 취소가 스레드 자체를 종료시키지는 않는다. SDK에 자체 timeout을 넣고 사용자가 떠난 뒤에도 실행 중인 호출이 몇 개 남는지 측정한다. 프로세스 메모리를 공유하는 SDK의 thread safety도 확인한다. 비동기 전환의 성공 기준은 동일한 업무 결과와 낮아진 loop lag, 관리 가능한 자원 사용이다.

## 21.3 Connection Pool 튜닝

HTTP와 DB 풀은 각각 상대 자원의 용량을 반영해야 한다. 한 요청이 연결을 보유하는 시간이 길면 같은 풀 크기로 처리할 수 있는 수가 줄어든다. 풀을 늘리기 전에 불필요한 보유 시간을 줄인다. DB 트랜잭션을 열어 둔 채 외부 생성 API를 기다리면 생성 지연이 DB 연결 점유로 전이된다. 필요한 자료를 읽고 transaction을 끝낸 뒤 외부 호출을 수행할 수 있는 업무인지 검토한다.

pool size, overflow, acquire timeout, 연결 수명을 함께 조정한다. worker 수와 배포 교체 중 중복 인스턴스까지 전체 연결 예산에 넣는다. 연결을 늘리면 상대 시스템이 더 많은 동시 일을 수행해야 하므로 query latency가 증가할 수 있다. 실제 DB의 최대 연결과 처리 능력은 같은 숫자가 아니다. 한 번의 실험에서는 풀 크기만 바꾸고 query와 입력을 유지하면 효과를 해석하기 쉽다.

## 21.4 DB 쿼리 최적화

쿼리 최적화의 출발점은 실행한 SQL과 그 횟수다. 문서 목록 20개를 읽은 뒤 작성자를 각각 읽으면 N+1이 발생할 수 있다. 관계를 필요한 범위에서 eager load하거나 필요한 필드만 JOIN해 조회한다. JOIN 결과가 중복되어 본문 크기가 커지는 문제도 있으므로 쿼리 횟수만 줄이는 데 집중하지 않는다.

인덱스는 조회 조건과 정렬을 함께 고려한다. 실제 데이터 분포와 실행 계획을 보고 효율을 확인한다. 필터와 정렬에 맞지 않는 인덱스를 여러 개 추가하면 쓰기 비용과 공간만 늘 수 있다. 큰 offset pagination 대신 안정적인 정렬 키를 사용하는 keyset pagination을 고려한다. 최신 데이터가 계속 추가되는 서비스에서는 페이지 경계의 일관성도 함께 설계한다. SQLAlchemy ORM 편의 기능을 사용하는 동안에도 실제 SQL은 확인해야 한다.

## 21.5 응답 직렬화 비용 분석

응답에는 DB 객체를 읽는 시간, 모델 검증, Python 객체 생성, JSON 인코딩, 네트워크 전송이 포함된다. ORM 객체를 바로 직렬화하면서 lazy load가 일어나면 직렬화 단계가 추가 DB 요청을 유발한다. 응답 DTO를 명시적으로 구성하고 관계를 미리 읽으면 어떤 자료를 전송하는지 알기 쉽다.

대형 응답에는 필요한 필드만 포함하고 페이지 크기를 제한하는 것이 먼저다. 10MB 응답을 빠른 인코더로 만드는 것보다 사용자가 필요로 하는 50KB를 반환하는 편이 효과가 클 수 있다. 단, 응답 모델을 제거해서 내부 필드까지 노출하는 개선은 성능 최적화가 아니다. 검증과 필터링이 어느 계층에 남아 있는지 확인한다. datetime, Decimal, UUID 같은 타입의 인코딩 계약도 유지한다.

## 21.6 JSON 처리 최적화

표준 JSON, Pydantic의 직렬화 경로, 추가 JSON 라이브러리는 지원 타입과 출력 정책이 다르다. 샘플 자료형과 크기, 모델 구성에 따라 비용도 다르므로 한 라이브러리가 언제나 빠르다고 단정하지 않는다. 이중 인코딩을 먼저 찾는다. 이미 JSON 문자열인데 다시 JSONResponse로 감싸면 문자열 자체가 JSON으로 인코딩되어 계약이 바뀐다.

직접 bytes를 반환하는 경우 Content-Type을 맞추고 모델 검증이 어디서 이루어지는지 설명한다. 큰 응답을 스트리밍하면 peak memory를 줄일 수 있지만 클라이언트 파싱과 중간 오류 계약이 달라진다. gzip도 전송량을 줄이는 대신 CPU를 소비하고 스트림 buffering에 영향을 줄 수 있다. 작은 응답에서 압축 이득이 없을 수 있으므로 payload 분포와 실제 네트워크 조건을 고려한다.

## 최소 실습: 블로킹 위치를 옮겨 보기

다음 `main.py`는 **완전 실행 예제**다. 두 경로의 업무 결과는 같지만 대기 방식이 다르다. 결함 경로는 로컬에서만 사용한다. good 경로의 semaphore는 실행뿐 아니라 대기 작업의 전체 수까지 제한하지 않으므로 운영에서는 admission 제어도 추가한다.

```python
import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request


def legacy_lookup() -> dict:
    time.sleep(0.2)
    return {"document": "Knowledge Hub"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.legacy_slots = asyncio.Semaphore(4)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/bad")
async def bad():
    return legacy_lookup()


@app.get("/good")
async def good(request: Request):
    async with request.app.state.legacy_slots:
        return await asyncio.to_thread(legacy_lookup)


@app.get("/ping")
async def ping():
    return {"ok": True}
```

**설치와 실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1" "httpx>=0.28,<1"
python -m uvicorn main:app --port 8021 --workers 1
```

다음 `probe.py`는 **완전 실행 예제**다. 네트워크 연결의 스케줄링 때문에 정확한 수치는 환경에 따라 달라진다. 단일 worker 설정을 유지하고 여러 번 반복해 경향을 관찰한다.

```python
import asyncio
import time
import httpx


async def measure(path: str):
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8021", timeout=3) as client:
        await client.get("/ping")
        pending = asyncio.create_task(client.get(path))
        await asyncio.sleep(0.03)
        started = time.perf_counter()
        response = await client.get("/ping")
        elapsed = time.perf_counter() - started
        result = await pending
        assert response.status_code == result.status_code == 200
        assert result.json() == {"document": "Knowledge Hub"}
        print(path, "ping_ms", round(elapsed * 1000, 2))


async def main():
    for path in ["/bad", "/good"]:
        for _ in range(3):
            await measure(path)


asyncio.run(main())
```

`python probe.py`를 실행한다. bad 처리 중 ping이 지연되고 good 처리 중에는 상대적으로 빨리 응답하는 경향을 기대한다. 시간 차이를 특정 배수로 고정하지 않는다. 실제 서비스에서는 legacy SDK 자체 timeout과 측정한 부하 아래의 스레드 대기를 기록한다. 단일 요청의 완료 시간은 두 경로 모두 약 0.2초라는 가정에 가깝지만 동시 요청에 미치는 영향은 다르다.

## 21.7 캐시와 중복 요청 최적화

캐시는 읽기 비용을 줄이지만 권한과 최신성 계약을 포함해야 한다. 문서 ID만 캐시 키로 삼으면 사용자별 열람 가능 필드가 섞일 수 있다. 조직, 문서 버전, 질의 설정을 키에 넣거나 권한 검증 이후의 안전한 자료만 공유 캐시한다. TTL을 짧게 설정했다고 모든 정합성 문제가 사라지는 것은 아니다.

동일 키가 만료되어 요청이 동시에 몰리면 모든 요청이 DB나 상위 API로 간다. single-flight로 한 작업을 공유하거나 TTL jitter, stale-while-revalidate를 적용할 수 있다. 공유 Task의 한 소비자가 취소될 때 전체 작업을 취소할지 정책을 정한다. 캐시 hit ratio만 보고 성공을 판단하지 않는다. miss latency와 새로고침 실패, 잘못된 권한 자료가 반환되지 않는지도 검증한다.

## 21.8 Worker 수와 프로세스 구성

worker는 각자의 이벤트 루프와 메모리, 연결 풀을 가진 프로세스다. 한 프로세스의 CPU 병목을 여러 코어로 분산할 수 있지만 DB와 외부 API 용량이 함께 늘어나는 것은 아니다. 메모리 캐시는 worker별로 중복되고 in-memory lock도 공유되지 않는다. 큰 모델을 로드하는 서버에서는 worker 수가 메모리 예산에 직접 영향을 준다.

“CPU 개수의 두 배” 같은 수식을 시작점 없이 그대로 적용하지 않는다. CPU quota, 업무 특성, 메모리, 외부 연결 예산을 고려해 작은 범위에서 실험한다. 오케스트레이터가 컨테이너 복제 수를 관리한다면 컨테이너 안 worker 하나와 바깥 replica 수의 조합이 운영을 단순하게 할 수 있다. 단일 호스트 운영에서는 여러 worker와 프로세스 감독이 적합할 수 있다. 선택 근거를 배포 문서에 남긴다.

## 21.9 메모리 사용량 및 GC 분석

메모리 증가에는 정상 캐시, 일시적인 peak, 참조가 남는 누수, 네이티브 라이브러리 할당이 섞인다. RSS만 보고 Python 객체 누수라고 단정할 수 없다. `tracemalloc`은 Python 메모리 할당의 위치를 추적하는 도구이며 모든 네이티브 메모리를 설명하지는 않는다. [Python tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html)

아래 `memory_probe.py`는 **완전 실행 개념 실험**이다. 바이트 객체를 일부러 보관해 두 snapshot 차이를 확인한다. 실제 서비스 누수 원인을 재현했다고 주장하지 않는다.

```python
import tracemalloc

tracemalloc.start(10)
before = tracemalloc.take_snapshot()
retained = [bytearray(4096) for _ in range(1000)]
after = tracemalloc.take_snapshot()
for item in after.compare_to(before, "lineno")[:3]:
    print(item)
retained.clear()
print("traced current/peak", tracemalloc.get_traced_memory())
tracemalloc.stop()
```

GC를 끄면 빨라진다는 조언을 측정 없이 적용하지 않는다. 참조 cycle이 있는 객체의 수명과 peak memory가 달라질 수 있다. 무한 로그 큐, 완료된 Task 보관 집합, 스트림별 버퍼, 사용자별 캐시를 먼저 확인한다. 부하 종료 후 자료를 회수했는데도 RSS가 즉시 줄지 않을 수 있으므로 객체 수와 tracemalloc 현재 사용량을 함께 관찰한다.

## 21.10 최적화 전후 성능 검증

최적화는 한 가설씩 적용한다. 기준 commit에서 동일 데이터와 부하를 실행하고 변경 commit에서 반복한다. warm-up 구간과 측정 구간을 구분하고, 결과 크기·캐시 상태·네트워크 위치를 고정한다. 개선된 p95와 함께 오류율, 성공 RPS, CPU, 메모리, DB 부하를 기록한다.

간단한 성능 회귀 기준도 절대 시간 하나보다 조건과 허용 편차를 포함해야 한다. 공유 CI runner는 잡음이 크므로 미세한 차이를 매번 실패로 만들면 테스트를 신뢰하기 어렵다. 기능 정확성은 결정적인 단위·통합 테스트로 확인하고, 의미 있는 성능 변화는 안정된 환경에서 비교한다. 최적화 후 timeout과 취소 경로가 여전히 정리되는지도 검증한다. 더 빠른 성공 경로와 더 위험한 실패 경로를 교환하지 않는다.

## 실무 적용: 개선의 우선순위

Knowledge Hub에서는 loop lag가 높으면 블로킹 제거, query 수가 많으면 N+1과 결과 크기, pool wait가 크면 수명과 전체 연결 예산을 먼저 본다. 네트워크 시간 대부분이 상위 LLM에서 발생한다면 JSON 인코더 교체가 사용자의 완료 시간을 크게 줄이지 못한다. 첫 token과 전체 완료 시간을 구분해 스트리밍 경험을 개선하거나 요청 재사용과 캐시 가능성을 검토한다.

변경이 큰 아키텍처 개선은 되돌릴 경계를 남긴다. 새로운 비동기 드라이버를 적용할 때 일부 트래픽에서 비교할 수 있도록 client interface를 분리한다. 캐시를 도입할 때 저장 계약을 바꾸기보다 조회 결과 캐시부터 검증한다. 개선 보고서에는 성공한 변화뿐 아니라 조건과 제한도 남겨 다음 운영자가 같은 문제를 다시 풀지 않게 한다.

## 확인 문제와 해설

1. `to_thread()`를 사용하면 CPU 연산이 자동으로 여러 코어에서 빨라지는가? **해설:** 일반적인 GIL 아래의 순수 Python 계산은 그렇지 않다. I/O 대기 오프로딩과 CPU 병렬화는 구별한다.
2. DB 풀을 두 배로 늘리면 처리량도 두 배가 되는가? **해설:** 상대 DB의 처리 능력과 lock 경합에 따라 달라진다. pool wait와 query latency를 동시에 측정한다.
3. 응답 모델을 제거해 직렬화가 빨라졌다. 성공적인 최적화인가? **해설:** 자료 필터링과 검증 계약이 유지되는지 확인해야 한다. 민감 필드가 노출되면 개선으로 인정할 수 없다.
4. 실습 평가 기준은 무엇인가? **해설:** 두 경로가 동일 결과를 내고, 단일 worker에서 ping 지연 경향이 달라짐을 기록한다. 실제 시간과 환경을 남기며 특정 개선 배수를 주장하지 않는다.

## 요약과 다음 장

측정된 병목의 원인을 줄이는 것이 최적화다. 블로킹, 연결 보유, 불필요한 SQL, 큰 응답, 무한 캐시부터 조사하고 자원 예산을 유지한다. 다음 장은 이 실행 구조를 Docker와 프록시, 종료·교체 전략에 담아 운영한다.

## 공식 참고자료

- [Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Pydantic serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [Python tracemalloc](https://docs.python.org/3.12/library/tracemalloc.html)
- [Uvicorn settings](https://uvicorn.dev/settings/)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 20장 FastAPI 성능 측정](../20-performance-measurement/chapter.md) · [22장 Docker와 배포 아키텍처 →](../22-docker-deployment/chapter.md)
