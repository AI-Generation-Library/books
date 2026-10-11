---
title: "19장. FastAPI 테스트 전략"
description: "Knowledge Hub의 문서 등록 API가 정상 입력에서 201을 반환했다고 기능이 완성된 것은 아니다. 권한 없는 사용자가 남의 문서를 조회하는 경우, DB commit 직전 오류가 난 경우, 두 요청이 같은 제목을 동시에 등록한 경우도 계약의 일부다. 테스트는 함수가 실행됐는지 확인하는 기록이 아"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 19
part: 5
---

## 학습 목표와 도입 사례

Knowledge Hub의 문서 등록 API가 정상 입력에서 201을 반환했다고 기능이 완성된 것은 아니다. 권한 없는 사용자가 남의 문서를 조회하는 경우, DB commit 직전 오류가 난 경우, 두 요청이 같은 제목을 동시에 등록한 경우도 계약의 일부다. 테스트는 함수가 실행됐는지 확인하는 기록이 아니라 업무 규칙이 변하지 않았음을 보여 주는 실행 가능한 증거다.

이 장에서는 HTTP 계층과 비즈니스 계층의 테스트 경계를 정하고, sync·async 클라이언트의 lifespan 차이를 익힌다. 외부 호출을 mock으로 대체하되 실제 DB와 네트워크에서만 보이는 실패를 별도 통합 테스트로 남긴다. 실습은 Python 3.12, FastAPI 0.121 이상, Pydantic 2에서 독립적으로 실행하며 이전 장의 main.py를 수정하지 않는다.

## 19.1 단위 테스트와 통합 테스트

단위 테스트는 좁은 규칙을 빠르게 검증한다. 예를 들어 문서 제목 정규화, 접근 권한 결정, 재시도 가능한 오류 분류는 HTTP 서버가 없어도 테스트할 수 있다. 통합 테스트는 경계를 함께 통과한다. JSON 요청이 모델을 거쳐 service와 repository를 호출하고 정해진 응답으로 변환되는지 확인한다. 모든 것을 mock하면 실제 타입이나 SQL 제약이 틀려도 통과할 수 있다.

테스트 수보다 실패했을 때 무엇을 알 수 있는지가 중요하다. endpoint 응답 테스트가 실패하면 라우팅·검증·업무 규칙 중 어디가 문제인지 넓게 의심해야 한다. 작은 규칙 테스트가 함께 있으면 원인을 좁힐 수 있다. 반대로 구현의 사소한 내부 호출 순서를 과도하게 assert하면 리팩터링마다 실패한다. 사용자에게 중요한 출력과 부수 효과, 금지된 효과를 중심으로 검증한다.

## 19.2 pytest 기본 사용법

pytest는 `test_` 접두사의 파일과 함수를 발견하고 일반 `assert`로 실패를 설명한다. fixture는 테스트에 필요한 객체와 자원을 준비하고 정리한다. 기본 fixture 범위가 좁으면 서로 다른 테스트가 상태를 공유하지 않는다. DB 연결이나 앱의 lifespan은 fixture의 `yield` 앞뒤에서 열고 닫을 수 있다.

매개변수화는 여러 입력을 하나의 규칙으로 검증할 때 유용하다. 빈 문자열, 너무 긴 문자열, 허용하지 않은 enum을 각각 별도 코드를 복사해 테스트할 필요가 없다. 시간에 의존하는 테스트에서는 실제로 오래 자는 대신 시계 인터페이스나 결정적인 이벤트를 사용한다. 네트워크 재시도도 예측 가능한 모의 응답 시퀀스로 검증하면 빠르고 재현 가능하다.

## 19.3 FastAPI TestClient

`TestClient`는 동기 테스트 함수에서 ASGI 앱에 요청을 보낼 수 있게 한다. 실제 TCP 포트는 사용하지 않는다. lifespan을 실행하려면 `with TestClient(app) as client:` 형태의 context manager를 사용한다. 객체를 만드는 것만으로 startup과 shutdown이 실행된다고 가정하면 앱 상태 초기화 테스트가 빠진다. [Starlette TestClient](https://starlette.dev/testclient/)

기본 설정은 애플리케이션 내부 예외를 테스트에 다시 던질 수 있다. 500 응답 자체를 검증하려는 테스트에서는 `raise_server_exceptions=False`를 사용한다. 두 모드를 무작정 섞지 않는다. 프로그래밍 결함을 빠르게 찾는 테스트와 외부에 노출되는 오류 응답 계약을 확인하는 테스트의 목적이 다르기 때문이다. 스트리밍이나 BackgroundTasks의 실행 방식도 실제 네트워크 클라이언트와 관찰 시점이 다를 수 있다.

## 19.4 httpx AsyncClient 기반 비동기 테스트

비동기 DB 조회까지 테스트 함수에서 직접 await하려면 `AsyncClient`와 `ASGITransport`를 사용한다. transport는 앱의 ASGI 호출을 연결하지만 lifespan을 자동으로 시작하지 않는다. 공식 문서도 lifecycle 관리와 transport를 분리한다. [HTTPX Transports](https://www.python-httpx.org/advanced/transports/)

작은 테스트에서는 `async with app.router.lifespan_context(app):`로 앱에 정의된 lifespan을 명시적으로 실행할 수 있다. 큰 프로젝트에서는 ASGI lifespan 관리 도구를 fixture에 넣어 시작·종료 프로토콜을 검증한다. TestClient가 다른 스레드의 이벤트 루프에서 실행되는 방식과 async 테스트의 현재 루프에서 실행되는 방식을 구별한다. 한 루프에서 만들어진 비동기 DB 엔진이나 락을 다른 루프에서 재사용하면 테스트 순서에 따라 실패할 수 있다.

## 19.5 Depends 의존성 오버라이드

`app.dependency_overrides`의 key는 경로 문자열이 아니라 실제 의존성 함수 객체다. 인증을 교체하면 토큰 검증 없이 특정 사용자로 요청할 수 있고, repository를 교체하면 DB 없이 HTTP 계약을 검증할 수 있다. 그러나 오버라이드는 테스트가 끝날 때 반드시 제거한다. 전역 앱을 공유하면서 한 테스트의 관리자 사용자가 다음 테스트에 남으면 인가 결함을 감출 수 있다.

오버라이드는 API의 모든 보안 테스트를 대체하지 않는다. 인증 의존성을 가짜 사용자로 바꾼 테스트는 인증 뒤의 동작만 검증한다. 만료 토큰, 잘못된 issuer, audience, algorithm, 누락된 Authorization은 실제 인증 의존성을 사용하는 별도 테스트로 확인해야 한다. fixture 이름에 `authenticated_client`, `anonymous_client`처럼 경계를 표현하면 테스트를 읽는 사람이 검증 범위를 알 수 있다.

## 최소 실습: 독립 앱과 여섯 가지 계약

아래 `main.py`는 **완전 실행 예제**다. 실제 JWT 인증 대신 교육용 헤더 인증을 사용한다. 이것을 운영 인증 방식으로 채택하지 않는다. 사전 데이터를 lifespan에 만들므로 lifecycle 차이가 테스트에 드러난다.

```python
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.documents = {1: {"title": "asyncio", "owner": "alice"}}
    yield
    app.state.documents.clear()


app = FastAPI(lifespan=lifespan)


def current_user(x_user: Annotated[str | None, Header()] = None) -> str:
    if x_user is None:
        raise HTTPException(401, "사용자 필요")
    return x_user


class DocumentInput(BaseModel):
    title: str = Field(min_length=1, max_length=80)


@app.get("/documents/{document_id}")
async def read(document_id: int, request: Request, user: Annotated[str, Depends(current_user)]):
    item = request.app.state.documents.get(document_id)
    if item is None:
        raise HTTPException(404, "문서 없음")
    if item["owner"] != user:
        raise HTTPException(403, "권한 없음")
    return {"id": document_id, "title": item["title"]}


@app.post("/documents", status_code=201)
async def create(data: DocumentInput, request: Request, user: Annotated[str, Depends(current_user)]):
    # 이 메모리 예제에서는 await 없이 한 번에 갱신한다.
    document_id = max(request.app.state.documents, default=0) + 1
    request.app.state.documents[document_id] = {"title": data.title, "owner": user}
    return {"id": document_id, "title": data.title}
```

같은 폴더의 `test_main.py`는 **완전 실행 예제**다. AnyIO의 백엔드를 asyncio로 제한하여 설치하지 않은 Trio에서 중복 실행되지 않게 한다.

```python
import asyncio
import httpx
import pytest
from fastapi.testclient import TestClient

from main import app, current_user


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    with TestClient(app) as instance:
        yield instance


def test_read(client):
    response = client.get("/documents/1", headers={"x-user": "alice"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "asyncio"}
    assert "owner" not in response.json()


@pytest.mark.parametrize("headers, code", [({}, 401), ({"x-user": "bob"}, 403)])
def test_access(client, headers, code):
    assert client.get("/documents/1", headers=headers).status_code == code


def test_invalid_input(client):
    response = client.post("/documents", headers={"x-user": "alice"}, json={"title": ""})
    assert response.status_code == 422
    assert len(app.state.documents) == 1


def test_override(client):
    app.dependency_overrides[current_user] = lambda: "alice"
    try:
        assert client.get("/documents/1").status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_concurrent_creation():
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            results = await asyncio.gather(*[
                client.post("/documents", headers={"x-user": "alice"}, json={"title": f"doc-{i}"})
                for i in range(8)
            ])
            assert all(result.status_code == 201 for result in results)
            assert len({result.json()["id"] for result in results}) == 8
```

**설치·실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "httpx>=0.28,<1" "pytest>=8,<10" "anyio>=4,<5"
python -m pytest -q
```

매개변수화된 access 두 사례를 포함해 테스트 여섯 개가 통과해야 한다. 이 테스트는 TCP, TLS, DB, 다중 worker를 검증하지 않는다. 메모리 ID 생성이 async 단일 루프에서 await 없이 동작하는 성질만 검증한다. 해당 코드를 DB에서 `max(id)+1` 방식으로 구현하면 같은 결과를 기대할 수 없다. DB 고유 제약과 시퀀스를 사용해야 한다.

## 19.6 DB 테스트와 트랜잭션 격리

DB 테스트는 별도 테스트 데이터베이스에서 수행한다. 운영 DB URL을 그대로 사용하는 환경변수를 피하고 테스트 실행 전 DB 이름과 접속 대상을 검증한다. 테스트마다 트랜잭션을 열어 rollback하는 방식은 빠르지만 앱 코드가 commit하거나 다른 연결에서 읽는 상황을 고려해야 한다. 외부 트랜잭션과 savepoint 전략을 쓰더라도 SQLAlchemy와 DB의 지원 범위를 확인한다.

SQLite로 통과한 테스트가 PostgreSQL의 lock·격리 수준·JSON·인덱스 동작을 검증하지는 않는다. 빠른 기능 테스트와 운영 DB 종류의 통합 테스트를 분리한다. 병렬 테스트는 같은 세션을 공유하지 않고, worker별 DB 또는 스키마를 사용한다. `AsyncSession` 하나를 `gather()`의 여러 작업에 넘겨서 테스트를 빠르게 만드는 것은 안전한 격리가 아니다. 실제 unique 충돌은 두 개의 독립 세션으로 재현한다.

## 19.7 외부 API Mock 처리

HTTPX의 `MockTransport`로 응답 상태, 본문, 지연, 예외를 제어할 수 있다. 요청의 method·path·멱등 키가 올바른지도 검사한다. 모의 응답은 정상 JSON뿐 아니라 429, 503, malformed JSON, 계약에 없는 필드까지 포함한다. `ReadTimeout`을 직접 일으키는 mock은 timeout 분류를 검증할 수 있으나 실제 소켓에서 deadline이 작동하는지까지 증명하지는 않는다.

잘못된 위치를 patch하면 실제 인터넷 호출이 나갈 수 있다. import가 사용되는 모듈의 참조를 교체하거나 명시적 클라이언트 의존성으로 전달한다. 테스트 환경에서는 외부 네트워크가 필요 없도록 기본값을 모의 전송으로 설정하는 것이 좋다. 공급자의 응답 형식 변화는 계약 테스트 또는 정기적인 별도 검증으로 확인하고, 테스트에 실 API 키를 저장하지 않는다.

## 19.8 인증 및 예외 테스트

인증은 누구인지, 인가는 무엇을 할 수 있는지 검증한다. 정상 토큰, 만료, 서명 오류, 금지 알고리즘, 잘못된 issuer·audience, 다른 소유자의 문서를 각각 테스트한다. 응답에 비밀번호 해시와 내부 오류 상세가 없는지도 확인한다. 관리자 테스트만 통과하면 일반 사용자 권한 경계가 비어 있을 수 있다.

예외 테스트는 상태 코드와 오류 코드, 필요한 헤더를 검증한다. traceback 문자열 전체를 비교하면 Python이나 라이브러리 버전 변화에 취약하다. DB 오류 후 다음 요청이 정상 작동하는지도 중요하다. rollback이 빠져 세션이 실패 상태에 남는 결함은 첫 요청의 500만 확인하면 놓칠 수 있다. 로그에 민감한 본문이 없는지 검증할 때도 모든 로그 문장을 고정하는 방식보다 금지된 값을 검사한다.

## 19.9 동시성 테스트와 Race Condition 재현

race는 운 좋게 여러 번 통과했다고 없다고 결론 낼 수 없다. 두 요청이 읽기 단계를 모두 통과한 뒤 쓰도록 barrier나 `asyncio.Event`를 사용하면 충돌 창을 의도적으로 만든다. 테스트용 service가 count를 읽고 이벤트를 기다린 뒤 증가하게 하면 lost update를 재현할 수 있다. 최종 값만 확인하지 말고 처리된 요청 수와 실패 계약도 확인한다.

단일 프로세스 테스트에서 `asyncio.Lock`을 넣고 통과했다고 다중 worker에서도 안전하다고 주장하지 않는다. 프로세스마다 락이 따로 있다. 업무 규칙은 DB unique 제약, 원자 update, version 조건 등 공유 저장소에서 보장하는 것이 기본이다. 과부하 테스트는 전체 성공 수만 확인하지 않고 admission 거절, 대기 시간, 종료 후 남은 Task도 점검한다.

## 19.10 테스트 자동화와 CI 구축

CI는 깨끗한 환경에서 잠금된 의존성을 설치하고 검증을 반복한다. Python 버전과 DB 종류, migration 경로를 명시한다. 로컬 가상환경에 우연히 설치된 패키지가 없으면 테스트가 실패하는 것이 정상이다. 실제 프로젝트에서는 pip의 hash 잠금 파일이나 uv lock을 사용하고 검증된 조합을 commit한다.

아래는 `.github/workflows/test.yaml`에 넣는 **설정 예제**다. `requirements-test.txt`에는 앞의 설치 패키지를 검토 후 고정해 둔다. 태그는 예제용 고정 major 태그이며 최신 버전이라는 뜻이 아니다. 배포 권한을 부여하지 않는 테스트 job이며 운영 CI에서는 action을 검토한 commit SHA에 고정한다.

```yaml
name: test
on: [push, pull_request]
permissions:
  contents: read
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: python -m pip install -r requirements-test.txt
      - run: python -m pytest -q
```

통합 DB job에는 DB 준비 완료 확인과 migration 실행을 추가한다. 테스트마다 서비스를 다시 띄우기보다 session fixture로 기반을 준비하되 데이터는 분리한다. 실패 로그, junit 결과, 필요한 최소 재현 자료를 artifact로 남기면 CI에서만 발생하는 오류를 찾기 쉽다. 테스트가 통과했다고 성능과 보안 전체가 검증된 것은 아니므로 검증 범위를 명시한다.

## 확인 문제와 해설

1. `TestClient(app)` 생성만으로 lifespan을 검증할 수 있는가? **해설:** context manager를 사용해야 시작과 종료가 실행된다. 초기 app.state와 종료 시 정리를 assert한다.
2. AsyncClient와 ASGITransport는 lifespan을 자동 실행하는가? **해설:** 아니다. lifespan context 또는 별도 manager가 필요하다. 예제에서 context를 제거해 초기 데이터 접근이 실패하는지 확인한다.
3. 인증을 override한 테스트가 JWT 검증도 입증하는가? **해설:** 인증 뒤의 계약만 검증한다. 실제 토큰 검증 테스트를 추가하고 두 목적을 구분한다.
4. 동시 요청 여덟 개가 모두 통과하면 race가 없는가? **해설:** 보장되지 않는다. barrier로 충돌 지점을 만들고 운영 DB와 여러 프로세스에서도 핵심 제약을 검증한다.

## 요약과 다음 장

좋은 테스트는 경계를 드러내고 상태를 정리하며 실패를 결정적으로 재현한다. TestClient와 ASGITransport의 lifespan 차이, 인증 오버라이드의 범위, 실제 DB가 필요한 규칙을 구별한다. 다음 장은 같은 재현 원칙을 성능 측정에 적용한다.

## 공식 참고자료

- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [Starlette TestClient](https://starlette.dev/testclient/)
- [HTTPX Transports](https://www.python-httpx.org/advanced/transports/)
- [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [GitHub Actions Python CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 18장 백그라운드 작업과 메시지 큐](../18-background-jobs/chapter.md) · [20장 FastAPI 성능 측정 →](../20-performance-measurement/chapter.md)
