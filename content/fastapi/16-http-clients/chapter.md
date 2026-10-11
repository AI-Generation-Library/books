---
title: "16장. HTTP 클라이언트와 외부 API 연동"
description: "Knowledge Hub의 문서 검색은 내부 데이터베이스만 조회하지 않는다. 조직 디렉터리에서 작성자 정보를 가져오고, 별도 색인 서비스에서 검색 결과를 받아 하나의 응답으로 조합한다. 검색 서버가 빨라도 디렉터리가 멈추면 전체 응답이 늦어진다. 외부 요청을 단순한 함수 호출로 생각하면 이 장애가 보이지"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 16
part: 5
---

## 학습 목표와 도입 사례

Knowledge Hub의 문서 검색은 내부 데이터베이스만 조회하지 않는다. 조직 디렉터리에서 작성자 정보를 가져오고, 별도 색인 서비스에서 검색 결과를 받아 하나의 응답으로 조합한다. 검색 서버가 빨라도 디렉터리가 멈추면 전체 응답이 늦어진다. 외부 요청을 단순한 함수 호출로 생각하면 이 장애가 보이지 않는다. 네트워크 호출은 연결, 대기, 전송, 검증, 실패라는 여러 단계로 이루어진 자원 사용 계약이다.

이 장의 목표는 비동기 HTTP 요청을 작성하는 데서 끝나지 않는다. 클라이언트의 수명을 정하고, 요청의 시간 예산과 동시성 한도를 계산하고, 재시도로 피해를 키우지 않는 정책을 설계한다. 실습은 다른 장의 파일을 이어 붙이지 않는 독립 예제이며 Python 3.12, FastAPI 0.121 이상 1 미만, Pydantic 2를 기준으로 한다. 외부 서비스는 로컬 모의 전송 계층으로 대체하므로 API 키나 인터넷 연결이 필요 없다.

## 16.1 HTTP 클라이언트의 역할

서버 입장에서 받은 HTTP 요청과 서버가 다른 서비스로 보내는 HTTP 요청은 다른 연결이다. 앞쪽 연결이 종료되어도 뒤쪽 호출이 자동으로 끝나는 것은 아니다. 따라서 호출을 시작한 코드가 시간 제한과 취소, 응답 닫기를 책임져야 한다. 클라이언트는 URL 조합, TLS 검증, 헤더와 쿠키, 연결 재사용, 응답 읽기를 담당한다. 비즈니스 서비스는 이 상세 기능을 감싸서 `검색한다`, `사용자를 조회한다`라는 도메인 계약을 제공하는 편이 좋다.

계약에는 성공 자료형뿐 아니라 실패 의미도 있어야 한다. 작성자 정보가 없으면 검색 전체를 실패시킬 것인가, 이름을 알 수 없음으로 표시할 것인가? 결제 승인과 선택적인 프로필 사진 조회는 같은 실패 정책을 사용할 수 없다. 선택적 의존성의 실패를 처리할 때도 응답에 누락 여부를 표시해야 한다. 조용히 빈 배열을 반환하면 사용자는 검색 결과가 정말 없는 것인지 검색 서비스가 죽은 것인지 알 수 없다.

## 16.2 requests와 httpx 비교

`requests`는 동기 API를 제공하며 기존 Python 생태계에서 널리 사용한다. `httpx`는 동기 `Client`와 비동기 `AsyncClient`를 제공한다. 선택 기준은 이름의 인기도가 아니라 호출하는 실행 환경이다. 동기 배치 스크립트에는 동기 클라이언트가 단순하다. 여러 네트워크 대기를 겹쳐야 하는 `async def` 경로에는 비동기 클라이언트가 자연스럽다.

`async def` 안에서 `requests.get()`을 직접 호출하면 이벤트 루프 스레드가 네트워크 응답을 기다린다. 함수에 `async`가 붙었다는 이유로 내부 호출이 바뀌지 않는다. 동기 SDK만 있으면 제한된 스레드 풀로 넘기고, 해당 SDK의 자체 timeout도 설정한다. 스레드 작업을 기다리는 코루틴이 취소되어도 실행 중인 스레드의 네트워크 동작을 강제로 멈추는 것은 아니다. 이 차이는 장애 시 쌓이는 작업 수에 영향을 준다.

## 16.3 AsyncClient를 이용한 비동기 요청

`await client.get()`은 응답이 도착할 때까지 현재 코루틴을 대기시킨다. 그 사이 이벤트 루프는 다른 작업을 진행한다. JSON 파싱과 모델 검증은 별개 단계이며 CPU를 사용한다. 큰 응답에서는 네트워크 시간만 짧다고 전체 요청이 빠른 것은 아니다. 먼저 상태 코드를 검증하고, 예상 콘텐츠 형식과 크기를 점검한 다음 필요한 필드만 검증한다.

클라이언트 생성은 보통 lifespan에서 한 번 수행하고 shutdown에서 닫는다. 요청마다 클라이언트를 만드는 구현은 연결을 재사용할 기회를 잃는다. 반대로 모듈 import 시점에 무조건 생성하면 테스트나 여러 이벤트 루프에서 수명이 꼬일 수 있다. 애플리케이션의 시작과 종료라는 명시적 경계를 쓰면 소유자를 알 수 있다. 공유 클라이언트의 기본 헤더를 요청별 토큰으로 변경하지 말고 호출의 `headers` 인수로 전달한다.

## 16.4 Connection Pooling과 Keep-Alive

연결 풀은 사용할 수 있는 연결을 보관하고, 요청이 필요할 때 빌려 주는 관리 계층이다. Keep-Alive는 요청이 끝난 연결을 다음 요청에도 사용할 수 있게 한다. HTTPX의 클라이언트는 연결을 재사용한다. [HTTPX Clients](https://www.python-httpx.org/advanced/clients/)

풀이 커지면 무조건 빠르다는 결론은 위험하다. 연결 100개를 가진 worker 네 개는 최대 수백 개의 외부 연결을 만들 수 있다. 상대 서버의 연결 한도와 API 할당량, 내부 파일 디스크립터 한도를 함께 고려해야 한다. 사용하지 않는 연결을 유지하는 개수와 동시에 사용할 연결의 최대 개수도 다르다. 풀에서 기다리는 시간은 네트워크 통신 시간이 아니라 로컬 자원 대기 시간이다. 두 시간을 따로 기록해야 증설 대상이 드러난다.

## 16.5 Timeout과 Retry 전략

HTTPX는 connect, read, write, pool timeout을 구분한다. read timeout은 전체 응답 완료 시간보다 다음 데이터 조각을 기다리는 시간에 가깝다. 따라서 작은 조각을 계속 보내는 상대에게 전체 작업 시간을 제한하려면 `asyncio.timeout()` 같은 별도 deadline도 필요하다. [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)

재시도는 실패를 없애는 기능이 아니라 추가 부하를 발생시키는 결정이다. GET 조회를 연결 실패 후 한 번 다시 시도하는 것은 비교적 안전하지만, POST 생성의 응답을 받지 못한 경우 서버가 이미 생성했을 수 있다. 멱등 키나 결과 조회 계약이 없으면 중복 생성이 발생한다. 지수 backoff와 무작위 jitter를 쓰고, `Retry-After`를 존중하되 남은 deadline보다 오래 기다리지 않는다. 사용자의 요청마다 세 번, 서비스 중간 계층마다 세 번 재시도하면 말단 서비스에는 최대 아홉 번의 호출이 갈 수 있다.

## 16.6 외부 API 오류와 예외 처리

전송 실패, 외부의 비정상 HTTP 응답, 스키마 불일치는 서로 다른 문제다. DNS 또는 TLS 실패는 연결 장애이고, 429는 상대의 제한이며, 200 응답에 필요한 필드가 없으면 계약 위반이다. `raise_for_status()`를 호출하지 않으면 500 응답의 JSON도 성공 자료처럼 처리할 수 있다. 예외를 내부 오류 분류로 변환하고 호출 대상, 시도 횟수, 소요 시간을 기록한다. 토큰, 전체 응답 본문, 개인 정보는 로그에 남기지 않는다.

대외 응답에서 외부의 상태 코드를 무조건 복사하지 않는다. 외부의 401은 최종 사용자가 아니라 서버의 자격 증명 문제일 수도 있다. 잘못된 사용자 입력은 자체 4xx, 일시적인 상위 서비스 문제는 502 또는 503, 시간 초과는 504처럼 우리 계약에 맞게 매핑한다. 예외 핸들러에서 내부 URL이나 TLS 상세 오류가 사용자에게 노출되지 않도록 한다.

## 16.7 asyncio.gather를 이용한 병렬 요청

독립적인 두 호출을 차례로 기다리면 대기 시간이 합쳐진다. 함께 시작하면 전체 시간은 느린 호출의 시간에 가까워질 수 있다. 이는 CPU 연산을 두 코어에서 병렬 실행하는 것과 다른 효과다. `gather()`의 결과는 완료 순서가 아니라 입력 순서로 반환된다. 일부 결과를 허용할 때는 각 호출의 오류를 명시적으로 결과 객체로 바꾼다.

기본 `gather()`는 한 작업의 예외를 호출자에게 전달하지만 나머지 작업을 일괄 취소하는 구조적 실패 정책을 제공하지 않는다. 전체 작업이 함께 성공해야 하는 경우 `TaskGroup`으로 묶으면 하나가 실패할 때 동료 작업을 취소하고 종료를 기다릴 수 있다. 이미 발생한 외부 부수 효과를 취소로 되돌릴 수는 없다. 읽기 조합과 쓰기 트랜잭션 조합의 설계를 구별해야 한다.

## 16.8 동시 요청 제한과 Semaphore

`Semaphore(8)`은 한 프로세스에서 제한 구간을 동시에 실행하는 작업을 여덟 개로 제한한다. 전체 클러스터의 호출량이나 초당 호출량을 제한하지는 않는다. worker가 네 개라면 같은 대상에 최대 32개가 실행될 수 있다. 초당 할당량은 별도 rate limiter로 관리한다. 세마포어 앞에서 기다리는 작업이 무한히 쌓이면 메모리 사용량과 사용자 지연이 늘므로 입장 대기에도 timeout을 적용한다.

제한을 어디에 놓는지도 중요하다. 재시도 대기 시간 동안 슬롯을 붙잡으면 다른 정상 호출이 들어오지 못한다. 보통 개별 네트워크 시도에 슬롯을 쓰고 backoff 때 반환한다. 반대로 논리 작업 전체의 자원량을 제한하려는 목적이라면 전체 구간을 감쌀 수 있다. 정책 목적을 이름과 메트릭에 드러내면 운영자가 숫자를 조정할 근거가 생긴다.

## 최소 실습: 실패를 포함한 검색 조합 API

아래는 **완전 실행 예제**다. 새 폴더에 `main.py`로 저장한다. 모의 전송은 실제 DNS, TCP, TLS를 통과하지 않으므로 연결 풀 성능을 검증하는 실습은 아니다. 대신 요청 조합과 예외 계약을 재현한다.

```python
import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, ValidationError


class SearchResult(BaseModel):
    documents: list[str]


async def upstream(request: httpx.Request) -> httpx.Response:
    await asyncio.sleep(0.03)
    if request.url.params.get("q") == "fail":
        return httpx.Response(503, json={"error": "unavailable"})
    if request.url.path == "/search":
        return httpx.Response(200, json={"documents": ["asyncio 입문"]})
    return httpx.Response(200, json={"name": "Knowledge Hub"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.slots = asyncio.Semaphore(8)
    async with httpx.AsyncClient(
        base_url="https://upstream.invalid",
        transport=httpx.MockTransport(upstream),
        timeout=httpx.Timeout(1.0, connect=0.5, pool=0.1),
        limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
    ) as client:
        app.state.http = client
        yield


app = FastAPI(lifespan=lifespan)


async def fetch(request: Request, path: str, q: str):
    for attempt in range(2):
        async with request.app.state.slots:
            response = await request.app.state.http.get(path, params={"q": q})
        if response.status_code == 503 and attempt == 0:
            await asyncio.sleep(0.02)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("unreachable")


@app.get("/search")
async def search(request: Request, q: str = Query(min_length=1, max_length=100)):
    try:
        async with asyncio.timeout(0.5):
            async with asyncio.TaskGroup() as group:
                results = group.create_task(fetch(request, "/search", q))
                owner = group.create_task(fetch(request, "/owner", q))
        validated = SearchResult.model_validate(results.result())
        return {**validated.model_dump(), "owner": owner.result()["name"]}
    except TimeoutError:
        raise HTTPException(504, "상위 서비스 시간 초과") from None
    except ExceptionGroup:
        # 이 실습의 그룹 작업은 두 상위 조회뿐이다.
        raise HTTPException(502, "상위 서비스 조회 실패") from None
    except (ValidationError, KeyError, ValueError):
        raise HTTPException(502, "상위 서비스 응답 형식 오류") from None
```

**실행 명령**은 다음과 같다. 활성화된 가상환경에서 수행한다.

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "httpx>=0.28,<1" "uvicorn>=0.30,<1"
python -m uvicorn main:app --port 8016
```

다른 터미널에서 `curl.exe "http://127.0.0.1:8016/search?q=python"`을 실행하면 문서 배열과 owner가 나온다. `curl.exe -i "http://127.0.0.1:8016/search?q=fail"`은 한 번의 재시도 후 502를 반환한다. 고정된 짧은 backoff는 재현용이다. 운영에서는 jitter와 남은 시간 계산을 추가하고 오류를 더 세분화한다. `ExceptionGroup` 전체를 상위 실패로 바꾸는 정책도 이 작은 예제에만 적합하다. 큰 서비스에서 프로그래밍 오류까지 동일하게 삼키면 결함 탐지가 어려워진다.

## 16.9 Circuit Breaker와 장애 격리

차단기는 계속 실패하는 대상에 대한 호출을 일정 시간 중단한다. closed에서는 호출을 허용하고, 실패율이 기준을 넘으면 open으로 바뀌며, 이후 half-open에서 제한된 시험 호출을 허용한다. 이는 timeout이나 재시도를 대체하지 않는다. 느린 실패를 반복해서 기다리는 동안 내부 작업과 연결이 모두 소비되는 것을 막는 추가 경계다.

Knowledge Hub에서 디렉터리 장애가 검색 색인 호출 슬롯까지 소모하면 하나의 장애가 전체 기능으로 퍼진다. 대상을 기준으로 서로 다른 풀과 슬롯을 부여하는 bulkhead 설계가 도움이 된다. 차단기를 프로세스 메모리에 두면 worker마다 상태가 다르다. 이것이 꼭 오류는 아니지만 전체 정책을 요구한다면 공유 상태 또는 게이트웨이 계층이 필요하다. 장애가 회복됐다고 모든 인스턴스가 동시에 시험 호출을 보내지 않게 한다.

실무에서는 외부 호출의 지연 분포, timeout 비율, 재시도 수, 풀 대기, 거절 수를 함께 본다. 재시도를 추가한 후 성공률이 조금 올랐더라도 p99와 상대 부하가 크게 나빠졌으면 개선이라고 할 수 없다. 이 판단은 다음 장의 장기 연결과 20장의 측정에서도 이어진다.

## 확인 문제와 해설

1. read timeout이 1초이면 응답 전체가 반드시 1초 안에 끝나는가? **해설:** 아니다. 조각 사이 대기 제한과 전체 deadline을 구분해야 한다. 일정 간격으로 작은 조각을 보내는 서버로 반례를 만들 수 있다.
2. 한 worker의 세마포어가 10이고 worker가 4개이면 전체 동시 호출 한도는 얼마인가? **해설:** 동일 설정이라면 최대 40개에 가까워진다. 별도 인스턴스와 재시도 계층도 계산에 넣는다. 초당 제한과는 다른 값이다.
3. POST를 전송한 뒤 read timeout이 발생했다. 바로 재전송해도 되는가? **해설:** 이미 처리되었을 가능성이 있다. 멱등 키로 중복 효과를 막거나 작업 ID로 결과를 조회한다. 연결 실패와 처리 후 응답 분실은 같은 의미가 아니다.
4. 실습의 모의 전송으로 Keep-Alive 개선을 입증할 수 있는가? **해설:** 실제 연결이 없으므로 입증할 수 없다. 로컬 HTTP 서버를 따로 띄우고 연결 생성 횟수와 latency를 측정해야 한다. 오류 응답, 정상 응답, 종료 시 클라이언트 닫힘을 확인하면 이 실습은 통과다.

## 요약과 다음 장

외부 API 연동의 핵심은 호출 문법보다 시간, 동시성, 실패 의미와 자원 수명이다. 공유 클라이언트는 lifespan으로 관리하고, 전체 deadline과 개별 I/O timeout을 조합한다. 독립 조회는 동시에 실행할 수 있지만 제한 없는 fan-out과 재시도는 장애를 증폭한다. 다음 장에서는 같은 경계를 스트리밍과 WebSocket 연결에 적용한다.

## 공식 참고자료

- [HTTPX Async Support](https://www.python-httpx.org/async/) — 비동기 클라이언트와 스트림 수명.
- [HTTPX Clients](https://www.python-httpx.org/advanced/clients/) — 연결 재사용과 클라이언트 설정.
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/) — timeout 종류.
- [Python 3.12 asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html) — TaskGroup과 timeout의 API 계약.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 15장 API 보안](../15-api-security/chapter.md) · [17장 실시간 통신과 스트리밍 →](../17-streaming/chapter.md)
