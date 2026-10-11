---
title: "12장. Redis와 캐싱 전략"
description: "반복 조회를 캐시로 줄이는 방법과, 그 결과 오래된 값이 보일 수 있는 이유를 설명한다. Redis 비동기 클라이언트의 수명을 관리하고 Cache Aside, TTL, 요청 제한을 구현한다. 캐시를 도입한 뒤에는 응답시간뿐 아니라 적중률, 원본 조회 수, 데이터 지연까지 측정한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 12
part: 3
---

## 학습 목표

반복 조회를 캐시로 줄이는 방법과, 그 결과 오래된 값이 보일 수 있는 이유를 설명한다. Redis 비동기 클라이언트의 수명을 관리하고 Cache Aside, TTL, 요청 제한을 구현한다. 캐시를 도입한 뒤에는 응답시간뿐 아니라 적중률, 원본 조회 수, 데이터 지연까지 측정한다.

Knowledge Hub의 인기 문서 소개가 반복 조회된다고 하자. 같은 문서를 매번 DB에서 읽으면 저장소와 네트워크 비용이 반복된다. 캐시를 두면 이 비용을 줄일 수 있다. 하지만 문서 이름을 바꿨는데 화면에는 이전 이름이 보이거나, 캐시 서버가 죽었을 때 DB 요청이 한꺼번에 몰릴 수 있다. 캐시는 성능 기능이면서 새로운 실패 경로다.

## 12.1 캐시가 필요한 이유

캐시는 재사용 가능한 결과를 원본보다 싸게 가져오는 저장소다. DB 인덱스가 없는 쿼리를 캐시로 가리는 것은 근본 개선과 다르다. 먼저 느린 조회와 반복 정도를 확인한다. 재사용률이 낮은 개별 요청을 모두 캐싱하면 Redis 쓰기, 직렬화, 메모리 비용만 늘어날 수 있다.

캐시 키는 응답의 의미를 완전히 표현해야 한다. 문서 ID만 같아도 언어, 권한, 테넌트, 문서 버전에 따라 결과가 달라진다면 키에 그 조건을 넣거나 캐싱할 응답을 바꾼다. 특히 사용자별 검색 결과를 `search:검색어` 하나로 공유하면 다른 사용자의 문서가 노출될 수 있다. 캐시 적중은 인증과 권한 검사를 생략할 근거가 아니다.

캐시에 넣을 값은 연결이나 ORM 객체가 아니라 JSON 등 명시적 자료 구조다. 키에 스키마 버전 `v1`을 넣으면 배포 후 응답 형태가 달라졌을 때 이전 형식과 충돌을 줄일 수 있다. 메모리 사용량과 키 개수, 최대 결과 크기도 예산에 포함한다. Redis가 빠르다는 말이 무제한 저장을 허용하지는 않는다.

## 12.2 Redis 연동

Python에서는 `redis.asyncio`를 사용할 수 있다. 앱 lifespan에서 클라이언트를 만들고 종료 때 `aclose()`로 정리한다. 요청마다 연결 풀을 새로 만들면 연결 재사용의 장점을 잃는다. `socket_connect_timeout`은 연결 단계, `socket_timeout`은 명령 응답 대기에 관련된 제한이므로 값을 서버 요청 deadline과 맞춘다. 클라이언트 사용법은 [Redis의 redis-py 안내](https://redis.io/docs/latest/develop/clients/redis-py/)를 확인한다.

캐시 장애 시 기본 조회는 원본으로 우회할 수 있다. 하지만 요청 제한이나 중복 결제 보호처럼 정책을 강제하는 Redis 용도는 우회하면 보호가 사라진다. 읽기 캐시의 fail open과 비용 제한의 fail closed를 같은 정책으로 처리하지 않는다. 또한 Redis를 인터넷에 공개하지 않고 접근 인증, TLS, 네트워크 경계를 운영 환경에서 구성한다.

## 12.3 Cache Aside 패턴: 완전 실행 실습

Cache Aside는 먼저 캐시를 읽고, 없으면 원본을 읽어 캐시를 채우는 방식이다. 원본의 진실은 DB에 있고 캐시는 없어져도 다시 만들 수 있다. 아래 실습은 공개 문서만 다루고 DB 대신 메모리 저장소를 사용한다. 단일 프로세스 데모이므로 다중 워커의 원본 저장소가 일치하지 않는다.

로컬 Redis가 준비되어 있다고 가정한다. Docker가 있다면 별도 터미널에서 `docker run --rm -p 127.0.0.1:6379:6379 redis:7`로 실습 인스턴스를 실행할 수 있다. 이 명령은 로컬용 예시이며 이 원고 작성 과정에서 서버를 실행하거나 외부 서비스를 호출하지 않았다.

```powershell
python -m pip install "fastapi>=0.121,<1" "uvicorn[standard]" "redis>=5,<8"
python -m uvicorn cache_lab:app --reload
```

완전 실행 예제, `cache_lab.py`:

```python
import asyncio
import json
import logging
import os
import random
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException, Path, Request, Response
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger("hub.cache")

class DocumentInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = Redis.from_url(
        os.getenv("HUB_REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=0.3,
        socket_timeout=0.3,
    )
    app.state.documents = {1: {"id": 1, "title": "공개 문서"}}
    app.state.store_lock = asyncio.Lock()
    app.state.fill_locks = [asyncio.Lock() for _ in range(32)]
    app.state.origin_reads = 0
    try:
        yield
    finally:
        await app.state.redis.aclose()

app = FastAPI(title="Knowledge Hub Cache Lab", lifespan=lifespan)
DocumentId = Annotated[int, Path(ge=1)]

def cache_key(document_id: int) -> str:
    return f"hub:v1:public-document:{document_id}"

async def cached_read(request: Request, document_id: int):
    try:
        raw = await request.app.state.redis.get(cache_key(document_id))
        if raw is not None:
            value = json.loads(raw)
            if (
                isinstance(value, dict)
                and value.get("id") == document_id
                and isinstance(value.get("title"), str)
            ):
                return value
    except (RedisError, ValueError):
        log.warning("cache_read_unavailable")
    return None

@app.get("/documents/{document_id}")
async def read_document(
    document_id: DocumentId, request: Request, response: Response
):
    value = await cached_read(request, document_id)
    if value is not None:
        response.headers["X-Cache"] = "HIT"
        return value
    lock = request.app.state.fill_locks[document_id % 32]
    async with lock:
        value = await cached_read(request, document_id)
        if value is not None:
            response.headers["X-Cache"] = "HIT"
            return value
        async with request.app.state.store_lock:
            row = request.app.state.documents.get(document_id)
            value = dict(row) if row is not None else None
            request.app.state.origin_reads += 1
        if value is None:
            raise HTTPException(404, "문서가 없습니다")
        try:
            await request.app.state.redis.set(
                cache_key(document_id),
                json.dumps(value, ensure_ascii=False),
                ex=45 + random.randrange(15),
            )
        except RedisError:
            log.warning("cache_write_unavailable")
        response.headers["X-Cache"] = "MISS"
        return value

@app.put("/documents/{document_id}")
async def replace_document(
    document_id: DocumentId, body: DocumentInput, request: Request
):
    title = body.title.strip()
    if not title:
        raise HTTPException(422, "공백 제목은 허용하지 않습니다")
    value = {"id": document_id, "title": title}
    async with request.app.state.store_lock:
        request.app.state.documents[document_id] = value
    try:
        await request.app.state.redis.delete(cache_key(document_id))
    except RedisError:
        log.warning("cache_invalidation_unavailable")
    return value

@app.get("/lab/metrics")
async def lab_metrics(request: Request):
    return {"origin_reads": request.app.state.origin_reads}
```

첫 `GET /documents/1`은 `X-Cache: MISS`, 이후 TTL 내 조회는 `HIT`가 기대 결과다. Redis가 비어 있지 않으면 첫 조회부터 HIT일 수 있으므로 해당 실습 키만 삭제하거나 새 DB 번호를 사용한다. `/lab/metrics`의 원본 조회 수가 캐시 적중 시 증가하지 않는지 확인한다. 메트릭 API와 공개 수정 API는 실습용이며 운영에서는 인증과 권한, 별도 모니터링 경계를 둔다.

캐시 오류 시 원본으로 우회하므로 Redis가 없더라도 읽기가 200일 수 있다. 로그와 X-Cache를 함께 보고 “연동이 성공해서 200인지”, “장애 우회로 200인지”를 구분한다. 우회가 반복될 때 DB가 감당할 유입량까지 함께 설계해야 한다.

## 12.4 TTL과 캐시 무효화

TTL은 오래된 데이터가 얼마나 오래 살아 있을 수 있는지 제한하고 메모리를 회수한다. 실습은 45~59초의 지터를 준다. 모든 키가 정확히 60초에 만료되면 동시에 재조회되는 상황이 생기므로 만료 시점을 분산한다. 이 범위는 설명을 위한 정책 예시이며 업무에서 허용하는 데이터 지연에 맞게 정한다.

TTL이 짧으면 적중률이 낮아지고 원본 부하가 늘어난다. 길면 효율은 올라갈 수 있지만 변경 반영이 느려진다. 사용자의 권한과 같은 보안 상태는 긴 TTL로 캐싱하면 권한 회수가 늦어질 수 있다. 최신성 요구가 강한 값은 원본 조회나 버전 검증을 우선한다.

수정 뒤 캐시 키를 삭제하는 무효화는 일반적인 시작점이다. 여기서 순서가 중요하다. DB commit 전 삭제하면 다른 읽기가 이전 DB 값을 다시 캐시에 넣을 수 있다. 원본 변경이 확정된 다음 삭제하되, 삭제 실패에 대한 재시도나 outbox 기반 전달을 준비한다. 실습은 장애 시 TTL로 수렴하는 느슨한 정책이며 즉시 최신성을 보장하지 않는다.

## 12.5 동시 요청과 캐시 스탬피드

스탬피드는 같은 인기 키가 비었을 때 많은 요청이 동시에 원본을 읽는 현상이다. 실습에서는 32개의 프로세스 내부 락을 사용해 같은 문서의 채우기를 묶고 락 획득 뒤 캐시를 한 번 더 읽는다. 첫 작업이 값을 채웠다면 뒤 작업은 원본을 읽을 필요가 없다.

문서 ID마다 락을 영원히 저장하면 키가 늘면서 메모리가 커질 수 있다. 고정 개수 락은 메모리를 제한하지만 서로 다른 문서도 같은 락에 걸릴 수 있다는 대가가 있다. 이 실습의 방식은 프로세스 내부 중복만 줄인다. 다중 워커나 여러 서버에서는 각 프로세스가 동시에 원본을 읽을 수 있다.

분산 채우기 락을 적용하면 소유자 토큰과 만료, 안전한 해제가 필요하다. 임의 `DEL`로 락을 해제하면 만료 후 새 소유자가 얻은 락까지 지울 수 있다. 락 만료 동안 작업이 끝나지 않는 문제도 고려한다. 캐시 채우기의 중복을 조금 허용하는 정책과, 중요한 업무의 분산 락은 동일한 보장으로 다루지 않는다. 인기 데이터에는 만료 전에 갱신하거나 오래된 값을 잠시 제공하며 새 값을 만드는 전략도 선택지다.

## 12.6 Redis를 이용한 요청 제한

고정 시간 창 제한은 특정 창에서 요청 수를 세는 방식이다. `INCR`와 `EXPIRE`를 별도 네트워크 호출로 실행하면 증가 후 장애가 나서 만료가 없는 키가 남을 수 있다. Lua 스크립트로 이 두 동작을 묶을 수 있다. 아래 실습은 10초에 3번을 허용하고 그 뒤에는 허용 여부를 false로 반환한다.

독립 실행 예제, `rate_limit_lab.py`:

```python
import asyncio
import os
import time
from redis.asyncio import Redis

SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""

async def main():
    redis = Redis.from_url(
        os.getenv("HUB_REDIS_URL", "redis://localhost:6379/0"),
        socket_connect_timeout=0.5, socket_timeout=0.5,
    )
    try:
        window = 10
        bucket = int(time.time()) // window
        key = f"hub:limit:demo-user:{bucket}"
        for _ in range(5):
            count = int(await redis.eval(SCRIPT, 1, key, window + 2))
            print({"count": count, "allowed": count <= 3})
    finally:
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

`python rate_limit_lab.py`를 한 창 안에서 실행하면 첫 세 요청은 허용되고 뒤 두 요청은 거절된다. 같은 창에서 다시 실행하면 이전 횟수가 남으므로 결과가 달라진다. 애플리케이션에서는 거절을 429로 매핑하고 다음 허용 시점을 설명하는 `Retry-After`를 전달한다. Redis 장애 시 LLM 비용 보호는 503으로 제한하는 등의 명시적 정책을 정한다.

고정 창의 경계에서는 이전 창의 끝과 다음 창의 시작에 허용량 두 배가 몰릴 수 있다. 더 부드러운 제한이 필요하면 토큰 버킷이나 슬라이딩 창을 사용한다. 사용자 ID, API Key, IP, 전체 시스템 한도를 각각 목적에 맞게 조합한다. 위 시간 버킷은 앱 시계를 사용하므로 다중 서버의 시간 동기화도 전제다. 인증 전에는 공격자가 보낸 임의 사용자 이름을 신뢰하지 않고, 프록시 IP 역시 신뢰 정책을 거친다.

## 12.7 데이터 정합성과 캐시 갱신

원본 저장 후 캐시 삭제만으로 모든 경쟁이 사라지지는 않는다. 다음 순서를 생각해 보자. A가 이전 문서를 읽는다. B가 문서를 수정하고 commit한 뒤 캐시를 삭제한다. A가 이전 값을 캐시에 넣는다. 결과적으로 삭제가 성공했는데도 이전 값이 다시 캐시에 남는다. 실습에도 이 가능성이 있으며 TTL이 끝나야 수렴할 수 있다.

더 강한 최신성이 필요하면 문서 버전을 포함한 키, 원본 변경 이벤트, 버전 비교 후 캐시 저장 같은 정책을 검토한다. 단순 지연 후 재삭제는 흔한 경합을 줄일 수 있지만 모든 타이밍에서 보장되는 정합성 해법은 아니다. DB와 Redis를 하나의 로컬 트랜잭션으로 commit할 수 있다고 가정하지 않는다.

응답 전체를 캐싱할지 원본 객체 일부를 캐싱할지도 중요하다. 공개 문서 본문은 공유 캐시에서 가져오고 사용자 권한은 원본 정책으로 검사할 수 있다. 그러나 이미 권한을 반영한 검색 결과를 공유 키에 저장하면 위험하다. 캐시 키와 값의 보안 의미를 코드 리뷰에 포함한다. 삭제한 사용자의 데이터를 키만 잊어버린 채 메모리에서 계속 보관하는 문제도 데이터 보존 정책에 포함한다.

## 12.8 캐시 도입 전후 성능 측정

캐시가 빠르다는 결론은 같은 시나리오를 비교해 얻는다. 차가운 캐시, 따뜻한 캐시, Redis 장애, 동시에 만료되는 인기 키를 따로 측정한다. 동일한 문서 분포와 요청률에서 p50, p95, p99, 오류율, 원본 조회 수, Redis 명령 지연을 기록한다. 실습의 origin_reads는 간단한 관찰값이고 운영 메트릭 시스템을 대신하지 않는다.

예를 들어 적중률 90%라는 가정에서는 전체 조회 중 대략 10%가 원본 조회로 남는다. 하지만 원본이 비싸거나 만료가 몰리면 순간 부하는 훨씬 높을 수 있다. 평균 적중률 하나로 필요한 DB 용량을 정하지 않는다. 캐시 JSON 크기와 직렬화 비용, 네트워크 이동, 키 수에 따른 메모리도 측정한다.

가장 중요한 성능 실험은 장애 우회다. Redis를 일시 중단했을 때 원본 조회가 늘고 전체 API가 어디에서 제한되는지 확인한다. 무제한 우회로 DB까지 무너지면 캐시가 장애 범위를 키운 것이다. 보호용 동시성 제한, 짧은 timeout, 일부 응답의 일시 거절을 포함해 복구 가능한 정책을 설계한다.

## 확인 문제와 해설

1. TTL이 있으면 수정 직후 최신값이 보장되는가? **해설:** 아니다. TTL은 최대 보존 시간을 제한하고 정합성 경쟁 자체를 없애지 않는다.
2. 캐시 적중 시 권한 검사를 생략해도 되는가? **해설:** 안 된다. 키와 값이 사용자별 권한을 정확히 표현하거나 별도 권한 검사를 통과해야 한다.
3. asyncio.Lock이 여러 워커의 스탬피드를 막는가? **해설:** 같은 프로세스 안에서만 작동한다. 분산 정책 또는 일정 중복 허용이 필요하다.
4. 실습 과제: 20개 동시 조회, 제목 수정, Redis 장애를 순서대로 실행하라. **평가 기준:** 각 단계의 X-Cache와 원본 조회 수를 기록하고, 오래된 값이 들어가는 경쟁 순서를 설명하며, 측정하지 않은 숫자를 결과라고 제시하지 않는다.

## 요약과 다음 장

캐시는 반복 읽기를 줄이지만 최신성, 메모리, 장애 우회의 대가를 갖는다. Cache Aside와 TTL부터 시작하고 권한을 반영한 키, 무효화 실패, 스탬피드를 함께 설계한다. 다음 장에서는 사용자 신원을 확인하고 문서 작업의 권한을 결정하는 인증과 인가를 구현한다.

## 공식 참고자료

- [Redis — redis-py Guide](https://redis.io/docs/latest/develop/clients/redis-py/): Python 클라이언트 연결과 명령.
- [Redis — EXPIRE](https://redis.io/docs/latest/commands/expire/): 만료 명령의 의미.
- [Redis — EVAL](https://redis.io/docs/latest/commands/eval/): Lua 실행과 키 전달.
- [Redis — Distributed Locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/): 분산 락의 전제와 주의점.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 11장 비동기 데이터베이스 처리](../11-async-database/chapter.md) · [13장 인증과 인가 →](../13-authentication/chapter.md)
