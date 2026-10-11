---
title: "18장. 백그라운드 작업과 메시지 큐"
description: "Knowledge Hub에 대용량 문서가 업로드되면 파싱, 임베딩 생성, 색인 등록이 이어진다. 요청을 2분 동안 붙잡아 두면 프록시 timeout과 사용자 재시도가 섞이고 같은 문서가 두 번 처리될 수 있다. 빠르게 작업 ID를 반환하고 별도 worker가 수행하면 사용자 요청의 수명과 작업의 수명을 "
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 18
part: 5
---

## 학습 목표와 도입 사례

Knowledge Hub에 대용량 문서가 업로드되면 파싱, 임베딩 생성, 색인 등록이 이어진다. 요청을 2분 동안 붙잡아 두면 프록시 timeout과 사용자 재시도가 섞이고 같은 문서가 두 번 처리될 수 있다. 빠르게 작업 ID를 반환하고 별도 worker가 수행하면 사용자 요청의 수명과 작업의 수명을 나눌 수 있다. 이때 202 응답을 받았다는 사실이 실제 처리 완료를 뜻하지 않도록 API 계약을 바꾸어야 한다.

이 장에서는 프로세스 내부 작업과 내구성 큐를 구별하고, 상태 전이·재시도·멱등성을 하나의 처리 모델로 설계한다. 실습은 독립 폴더에서 Python 3.12와 FastAPI 0.121 이상을 사용한다. 먼저 외부 서비스 없는 BackgroundTasks 예제를 실행하고, 선택적으로 로컬 Redis와 Celery를 연결한다. Redis나 Celery를 설치하지 않았는데 큐 실습을 완료했다고 볼 수는 없다.

## 18.1 요청-응답 처리와 비동기 작업 분리

요청을 기다리면서 비동기 I/O를 수행하는 것과 응답 이후에도 계속 수행하는 작업은 다르다. 전자는 응답을 만들기 위한 작업이고 후자는 독립적인 업무 단위다. 문서 색인의 결과가 즉시 필요하지 않으면 POST에서 작업을 등록하고 `Location` 헤더에 상태 조회 주소를 반환한다. 클라이언트는 상태를 주기적으로 조회하거나 SSE로 변화 알림을 받는다.

작업 등록 API는 무엇을 보장하는지 정해야 한다. 메모리에만 올린 뒤 202를 반환하면 서버 재시작으로 작업이 사라질 수 있다. DB에 작업을 저장했지만 브로커 전송이 실패하면 영원히 queued로 남을 수 있다. 응답 전에 브로커로만 보낸 뒤 DB 저장이 실패하면 조회할 수 없는 작업이 실행된다. 이런 두 쓰기 문제에는 DB 트랜잭션으로 작업과 outbox를 함께 저장하고 별도 발행자가 outbox를 보내는 패턴이 유용하다.

## 18.2 FastAPI BackgroundTasks

`BackgroundTasks`는 응답 이후 같은 애플리케이션 프로세스에서 함수를 실행한다. 짧은 알림이나 비핵심 후처리에 적합하다. 여러 프로세스로 작업을 분산하는 메시지 큐와는 다른 기능이다. FastAPI 공식 문서도 큰 작업의 별도 도구 사용을 설명한다. [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

함수는 sync 또는 async일 수 있다. sync 함수는 프레임워크의 스레드 풀에서 실행할 수 있지만, async 함수 내부의 블로킹 코드는 이벤트 루프를 막는다. 메일 발송이나 SDK 호출을 넣을 때는 자체 timeout을 설정해야 한다. 배경 작업이 실패해도 이미 보낸 HTTP 응답을 변경할 수 없다. 따라서 실패 로그와 별도 상태를 남겨야 하며, 사용자에게 성공했다고 표현하는 범위를 제한한다.

## 18.3 asyncio.create_task의 활용과 제약

`asyncio.create_task()`는 코루틴을 현재 이벤트 루프의 Task로 예약한다. 반환된 Task의 참조와 예외를 관리하지 않으면 실패를 놓치거나 종료 시 미완료 작업을 남길 수 있다. lifespan에서 Task 집합을 소유하고 종료 시 취소 후 기다리는 구조를 사용한다. 아무 곳에서나 fire-and-forget으로 만들고 나중에 worker가 책임진다고 생각하면 실제 소유자가 없다.

Task는 프로세스 메모리에 있는 실행 상태다. 서버 재시작으로 사라지며, 다른 worker에 넘겨지지 않는다. 작업 중간에 프로세스가 죽었을 때 재실행해야 한다면 실행 요청과 진행 상태를 외부에 저장해야 한다. `create_task`는 작업 큐의 대안이 아니라 주기적 상태 측정, 캐시 갱신처럼 프로세스 수명에 묶인 작은 작업을 관리하는 도구로 생각하면 역할이 명확해진다.

## 최소 실습 A: 응답과 후처리의 경계

다음은 `main.py`로 저장하는 **완전 실행 예제**다. 처리 결과는 메모리에 있으므로 내구성과 다중 worker 지원을 제공하지 않는다. BackgroundTasks의 수명을 확인하는 것이 목적이다.

```python
import asyncio
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI()
jobs: dict[str, dict] = {}


class Document(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


async def index(job_id: str, text: str):
    jobs[job_id] = {"state": "running"}
    try:
        await asyncio.sleep(0.2)
        jobs[job_id] = {"state": "succeeded", "words": len(text.split())}
    except Exception:
        jobs[job_id] = {"state": "failed", "code": "INDEX_FAILED"}
        raise


@app.post("/jobs", status_code=202)
async def submit(data: Document, background: BackgroundTasks, response: Response):
    job_id = str(uuid4())
    jobs[job_id] = {"state": "queued"}
    background.add_task(index, job_id, data.text)
    response.headers["Location"] = f"/jobs/{job_id}"
    return {"job_id": job_id, "state": "queued"}


@app.get("/jobs/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "작업 없음")
    return {"job_id": job_id, **jobs[job_id]}
```

**설치·실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1"
python -m uvicorn main:app --port 8018
```

Swagger UI `http://127.0.0.1:8018/docs`에서 `POST /jobs`에 `{"text":"Knowledge Hub document"}`를 보낸다. 202와 job_id를 받은 뒤 GET으로 조회하면 queued 또는 running을 거쳐 succeeded와 words가 나온다. 서버를 재시작하면 조회가 404가 된다. 이 소실이 실습의 핵심 관찰이다. TestClient는 응답의 배경 작업 완료까지 기다릴 수 있으므로 HTTP 네트워크로 관찰하는 지연과 다를 수 있다.

## 18.4 작업 큐가 필요한 상황

작업 큐는 API 서버와 worker 사이에 실행 요청을 보관한다. worker 처리량보다 등록량이 높으면 적체가 생기지만 API 서버가 모든 계산을 직접 수행하지 않아도 된다. 이 완충 효과는 무한하지 않다. 큐 최대 길이, 입력 파일 크기, 사용자별 대기 작업 수를 제한하지 않으면 저장 공간과 처리 지연이 계속 늘어난다.

내구성 요구, 처리 시간, CPU 또는 GPU 자원, 재처리 요구가 큐 선택 기준이다. 중요한 문서 색인은 서버 재시작 후에도 남아야 하므로 영속 저장과 복구가 필요하다. 단순 조회를 무조건 큐로 바꾸면 응답 모델이 복잡해지고 지연이 커질 수 있다. HTTP는 즉시 결과가 필요한 요청, 큐는 독립 작업이라는 기준을 먼저 정한다.

## 18.5 Celery와 Redis

Celery는 작업 등록, worker 실행, 재시도 등 분산 작업 실행 기능을 제공한다. Redis는 broker 또는 결과 backend로 사용할 수 있지만 각각의 역할과 데이터 보존 설정이 다르다. broker가 메시지를 받았다고 업무 데이터가 영구 보존됐다고 결론 내리면 안 된다. Redis persistence, failover, visibility timeout, 메시지 acknowledgement 정책을 함께 검토한다. Celery는 멱등 작업에서 late acknowledgement를 고려할 수 있다고 설명한다. [Celery Tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html)

다음은 로컬 Docker의 Linux 컨테이너에 Redis와 worker를 실행하는 **완전 실행 예제**다. Celery의 native Windows worker 실행을 전제로 하지 않는다. API는 Windows에서 실행해도 된다. 가상환경에 `celery[redis]>=5.4,<6`을 설치하고 `tasks.py`를 만든다.

```python
import os
from celery import Celery

celery = Celery(
    "knowledge_hub",
    broker=os.getenv("BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("RESULT_URL", "redis://127.0.0.1:6379/1"),
)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    worker_prefetch_multiplier=1,
)


@celery.task(name="hub.count_words")
def count_words(text: str) -> dict:
    # 순수 계산이라 같은 입력을 다시 실행해도 외부 부수 효과가 없다.
    return {"words": len(text.split())}
```

새 파일 `queue_api.py`의 **완전 실행 예제**다. 동기 `def` 경로에서 broker 호출을 수행하므로 이벤트 루프를 직접 막지 않는다. broker 연결 timeout 및 API 입장 제한은 운영 단계에서 추가해야 한다.

```python
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from tasks import celery, count_words

app = FastAPI()


class Input(BaseModel):
    text: str = Field(min_length=1, max_length=10000)


@app.post("/jobs", status_code=202)
def submit(data: Input, response: Response):
    try:
        job = count_words.delay(data.text)
    except Exception:
        raise HTTPException(503, "작업 등록 불가") from None
    response.headers["Location"] = f"/jobs/{job.id}"
    return {"job_id": job.id}


@app.get("/jobs/{job_id}")
def status(job_id: str):
    job = celery.AsyncResult(job_id)
    result = job.result if job.successful() else None
    return {"job_id": job_id, "state": job.state, "result": result}
```

**실행용 파일**, `Dockerfile.worker`를 만든다. 아래 버전 범위와 이미지 태그는 교육용이며 최신 또는 보안 검증된 잠금 파일이라고 주장하지 않는다.

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "celery[redis]>=5.4,<6"
COPY tasks.py .
CMD ["celery", "-A", "tasks", "worker", "--loglevel=INFO", "--concurrency=2"]
```

같은 폴더에 `compose.yaml`을 저장하는 **실행용 설정**이다.

```yaml
services:
  redis:
    image: redis:7.4-alpine
    ports: ["127.0.0.1:6379:6379"]
    command: ["redis-server", "--appendonly", "yes"]
    volumes: ["queue-data:/data"]
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      BROKER_URL: redis://redis:6379/0
      RESULT_URL: redis://redis:6379/1
    depends_on: [redis]
volumes:
  queue-data:
```

`docker compose up --build`로 로컬 서비스를 시작하고 별도 터미널에서 `python -m uvicorn queue_api:app --port 8118`을 실행한다. docs에서 등록과 조회를 반복하면 SUCCESS와 계산 결과를 확인한다. worker만 멈춘 상태에서 등록하면 결과가 대기하다 worker 재시작 후 처리된다. Redis의 AOF와 볼륨은 실습의 저장 기반이지만 모든 장애에서 데이터 손실을 막는 보증은 아니다. 이 예제의 조회는 임의 ID와 아직 실행되지 않은 ID를 PENDING으로 구분하지 못하고 사용자 소유권 검사도 없다. 실서비스에서는 등록된 작업 테이블과 인증을 추가한다.

## 18.6 작업 상태 관리

업무 상태는 보통 queued, running, succeeded, failed, cancelled로 모델링한다. 재시도 중 상태와 재시도 횟수도 표현한다. 상태 전이는 조건부 갱신으로 제한해 이미 succeeded인 작업이 오래된 worker의 실패 결과에 의해 덮이지 않게 한다. 실행 attempt ID와 lease 만료 시각을 기록하면 worker가 사라진 작업을 찾을 수 있다.

Celery 결과 backend는 조회 편의를 제공하지만 사용자에게 보여 줄 영속 이력의 유일한 저장소로 쓰기에는 만료와 보존 정책을 검토해야 한다. Knowledge Hub의 작업 테이블에는 소유자, 문서 ID, 입력 버전, 상태, 결과 참조, 시작·완료 시간, 안전한 오류 코드가 필요하다. 대용량 본문은 메시지에 넣기보다 저장소의 참조를 전달하고 접근 권한과 무결성을 검증한다.

## 18.7 Retry와 멱등성 보장

재시도 가능한 오류와 영구 오류를 구별한다. 일시적 네트워크 실패는 재시도 후보이고, 지원하지 않는 문서 형식은 입력을 바꾸기 전까지 다시 실행할 이유가 없다. 재시도에는 최대 횟수와 전체 기간이 있어야 한다. 반복 실패 작업은 격리된 실패 큐나 상태로 보내 원인을 수정한 뒤 재처리한다.

멱등성은 같은 작업이 두 번 실행되어도 효과가 중복되지 않는 성질이다. 문서 ID와 내용 버전의 조합에 unique 제약을 두고 색인 upsert를 사용하면 중복 효과를 줄일 수 있다. 완료 여부 확인 후 처리하는 두 단계만으로는 race를 막지 못한다. 확인과 상태 전이를 같은 트랜잭션 또는 원자 연산으로 묶는다. 외부 결제나 메일처럼 원자적 DB 트랜잭션 밖의 부수 효과에는 공급자의 멱등 키, 별도 발송 이력, reconciliation이 필요하다.

## 18.8 장애 복구와 작업 재처리

worker가 처리를 완료한 뒤 ack 전에 죽으면 작업이 다시 전달될 수 있다. ack가 너무 이르면 처리 도중 죽은 작업이 사라질 수 있다. 전달 정책만으로 정확히 한 번의 업무 효과를 얻는다고 주장하지 않는다. 중복 전달을 정상 시나리오로 보고 작업 효과를 멱등하게 만든다. 재전달 여부는 broker와 worker 설정, 장애 종류에 따라 달라지므로 실제 강제 종료 실험으로 확인한다.

복구 담당자는 실패 작업의 입력 버전과 마지막 checkpoint를 확인한다. 잘못 파싱된 문서를 다시 처리할 때 기존 결과를 그대로 덧붙이면 중복 임베딩이 생긴다. 새로운 결과를 임시 버전에 작성한 뒤 완성 시 포인터를 교체하는 방식이 안전하다. 취소 요청도 이미 실행된 외부 효과를 되돌리지 못하므로 협력적 취소와 별도 보상 작업을 구분한다.

## 18.9 대용량 작업 처리 아키텍처

파싱, 임베딩, 색인은 자원 특성이 다르다. CPU 파싱 worker와 네트워크 임베딩 worker를 분리하면 큰 파일 하나가 작은 작업을 모두 막는 현상을 줄일 수 있다. 작업 크기를 제한된 chunk로 쪼개고 chunk별 완료를 기록한다. 너무 잘게 쪼개면 broker 오버헤드와 상태 관리 비용이 증가한다.

실무에서는 큐 길이보다 가장 오래 기다린 작업의 나이도 중요하다. 짧은 작업을 계속 처리해 평균이 좋아 보여도 큰 작업이 굶을 수 있다. 사용자별 공정성, 우선순위, 최대 등록량, 재시도 트래픽을 함께 설계한다. 큐는 과부하를 보관할 뿐 처리 능력을 무한히 만들지 않는다. 예상 완료 시간이 서비스 약속을 넘으면 등록 단계에서 거절하거나 낮은 우선순위 처리를 명시해야 한다.

## 확인 문제와 해설

1. BackgroundTasks에서 처리하면 서버 재시작 후 이어서 실행되는가? **해설:** 프로세스 내부 작업이므로 보장되지 않는다. 실습 A에서 재시작 후 상태가 사라지는 것으로 확인한다.
2. 작업 ID가 있으면 멱등한가? **해설:** 아니다. 같은 ID를 여러 번 실행할 수 있다. 원자적 상태 전이와 중복 효과 방지 저장 모델이 필요하다.
3. 결과 backend의 PENDING은 반드시 등록된 작업인가? **해설:** 이 최소 예제에서는 임의 ID도 그렇게 보일 수 있다. 별도 등록 테이블로 존재와 소유권을 확인해야 한다.
4. ack 이후 worker가 죽는 상황을 어떻게 검증하는가? **해설:** 처리 시작, 효과 기록, ack 경계에 장애를 주입하고 중복·소실을 기록한다. 중복 처리 후 최종 색인 개수가 늘지 않으면 멱등 설계 검증을 통과한다.

## 요약과 다음 장

응답 후 실행, 비동기 실행, 내구성 실행은 서로 다른 성질이다. 큐를 도입할 때 상태 저장, 등록의 원자성, 중복 전달, 재시도 종료 조건을 함께 설계한다. 다음 장은 이 계약을 단위 테스트와 통합 테스트, 동시성 테스트로 검증한다.

## 공식 참고자료

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html)
- [Celery Redis broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html)
- [Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 17장 실시간 통신과 스트리밍](../17-streaming/chapter.md) · [19장 FastAPI 테스트 전략 →](../19-testing/chapter.md)
