---
title: "25장. FastAPI와 LLM API"
description: "이 장을 마치면 모델 호출을 HTTP 요청 하나로만 보지 않고 대기 시간, 비용, 취소, 사용량 정산이 연결된 작업으로 설계할 수 있다. 공급자가 바뀌어도 API 계약을 유지하는 어댑터를 만들고, 일반 응답과 스트리밍의 실패 처리 차이를 설명하는 것이 목표다. 실습은 비용이 없는 모의 모델을 사용한다. "
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 25
part: 7
---

## 학습 목표와 도입 사례

이 장을 마치면 모델 호출을 HTTP 요청 하나로만 보지 않고 대기 시간, 비용, 취소, 사용량 정산이 연결된 작업으로 설계할 수 있다. 공급자가 바뀌어도 API 계약을 유지하는 어댑터를 만들고, 일반 응답과 스트리밍의 실패 처리 차이를 설명하는 것이 목표다. 실습은 비용이 없는 모의 모델을 사용한다. 실제 공급자의 가격이나 처리 속도를 추정하지 않는다.

Knowledge Hub에 “이 문서를 요약해 줘” 기능을 추가했다고 생각해 보자. 개발 환경에서는 한 명이 질문하므로 문제없다. 운영에서는 사용자가 새로고침하고, 프록시가 연결을 닫고, 모델 공급자가 429를 반환한다. 서버가 이를 모두 새 요청으로 처리하면 같은 질문이 여러 번 과금된다. `async def`는 기다리는 동안 다른 요청을 실행하게 해 줄 뿐, 중복 비용과 사용자별 예산을 해결하지 않는다. AI 백엔드의 역할은 모델을 호출하는 일과 호출이 서비스의 약속을 지키게 만드는 일을 함께 수행하는 것이다.

## 25.1 AI 서비스 백엔드의 특징

일반 CRUD는 DB 트랜잭션이 끝나면 결과를 비교적 명확하게 확정할 수 있다. 생성 요청은 입력 길이, 출력 길이, 모델의 혼잡도, 도구 호출에 따라 수행 시간이 달라진다. 출력은 비결정적일 수 있고 생성이 성공해도 사실성이 충분하지 않을 수 있다. 따라서 HTTP 성공률과 답변 품질은 서로 다른 지표다. 모델 응답이 JSON이라는 이유로 업무 규칙까지 검증되었다고 판단하면 안 된다.

세 종류의 경계를 분리한다. 인증과 문서 권한은 백엔드가 결정한다. 프롬프트는 모델에게 작업을 설명하는 입력이다. 생성 결과는 다시 검증해야 하는 외부 데이터다. “관리자만 실행해”라는 시스템 문장은 접근 제어 구현이 아니다. 생성된 URL, SQL, 도구 이름을 실행하기 전에 서버가 별도 규칙으로 검사한다. 문서 안의 명령문도 신뢰할 수 없는 데이터로 취급한다.

서비스 목표를 처음부터 둘로 나누면 운영 판단이 쉬워진다. 예를 들어 작업 접수 p95 목표와 답변 완료 p95 목표를 따로 둔다. 전자는 API와 DB의 책임이고 후자는 모델, 검색, 도구를 포함한다. 모델이 느릴 때 접수를 계속 받을 수 있다고 해서 무한히 받을 수는 없다. 대기열 길이와 예상 완료 시간을 보여 주고, 용량이 없으면 빠르게 거절한다. 수치는 실제 부하 실험으로 정하며 이 장의 예제 제한은 교육용이다.

## 25.2 LLM API 호출 구조

HTTP 계층은 `question`, `request_id`, 출력 제한 같은 서비스 계약을 받는다. 서비스 계층은 인증된 사용자, 허용 문서, 예산을 결합한다. 공급자 어댑터는 이를 공급자 요청으로 바꾸고 응답을 `text`, `usage`, `finish_reason`, `provider_request_id` 같은 내부 형식으로 정규화한다. API 라우터에 공급자 SDK의 객체를 그대로 반환하면 공급자가 필드를 바꿀 때 서비스 전체가 함께 바뀐다.

어댑터는 단순히 함수 이름을 통일하는 계층이 아니다. 공급자마다 토큰 계산, 스트림 이벤트, 종료 이유, 사용량 제공 시점이 다르다. 내부의 `usage=None`은 사용량이 0이라는 뜻이 아니라 아직 확인하지 못했다는 뜻이어야 한다. 정확한 사용량을 얻지 못했을 때는 임시 추정과 최종 정산을 구분한다. 원문 프롬프트를 로그에 저장하지 않아도 요청 ID와 공급자 요청 ID로 장애를 추적할 수 있다.

공급자 중립 프로토콜에는 최소한 `complete`와 `stream`을 분리한다. `complete`는 확정 결과를 반환하고 `stream`은 delta, usage, completed 또는 failed 이벤트를 보낸다. 어댑터가 공급자의 중간 청크를 서비스 이벤트로 번역해야 한다. TCP 청크 하나가 토큰 하나이거나 JSON 객체 하나라고 가정하면 응답이 큰 날 갑자기 파싱이 깨진다. 프로토콜 프레이밍과 문자열 인코딩을 먼저 복원한 뒤 이벤트를 해석한다.

## 25.3 비동기 LLM 요청 처리

비동기 HTTP 클라이언트는 대기 중 이벤트 루프를 다른 Task에 양보한다. 모델 계산 자체는 외부 서버에서 일어난다. FastAPI 프로세스를 늘려도 공급자의 생성 속도가 빨라지지 않는다. 한 프로세스에 재사용 가능한 HTTP 클라이언트를 lifespan으로 만들고 종료 때 닫으면 연결 재사용을 적용할 수 있다. 요청마다 클라이언트를 생성하는 구조는 TLS와 연결 설정 비용을 반복한다.

동시성 제한은 클라이언트 풀과 별개다. 풀은 연결 자원을 제한하지만 “이 사용자에게 지금 세 건까지 허용”이라는 업무 규칙을 알지 못한다. 모델별 세마포어와 사용자별 접수 제한을 별도로 둔다. 세마포어 대기에도 deadline을 적용한다. 기다리는 요청이 수천 개 쌓인 상태에서 공급자 호출만 10초로 제한하면 전체 지연은 이미 수분이 된다.

CPU 작업도 분리해야 한다. 긴 텍스트 파싱, 로컬 토크나이저, PDF 렌더링을 `async def` 안에서 직접 호출하면 이벤트 루프를 점유한다. 작은 작업은 시간과 입력 크기를 측정하고, 큰 파싱은 워커에서 수행한다. 동기 함수에 `await`를 붙일 수 없다는 이유로 코드 전체를 `def`로 바꾸는 것은 요청 스레드 풀의 병목으로 옮기는 것일 수 있다. 사용하는 라이브러리의 실행 모델을 확인하고 자원을 명시적으로 제한한다.

## 25.4 요청 타임아웃과 재시도

타임아웃은 실패 원인을 표현하는 도구다. 연결 실패, 응답 데이터를 기다리는 시간, 연결 풀 대기, 작업 전체 시간은 다르다. HTTPX는 connect/read/write/pool 제한을 나누며, read 제한은 전체 생성 deadline과 동일하지 않다. 바이트가 조금씩 도착하면 read 제한을 지키면서도 전체 요청은 오래 지속될 수 있다. [HTTPX timeout 공식 문서](https://www.python-httpx.org/advanced/timeouts/)

전체 시간에는 인증 이후의 예산 예약, 대기열 대기, 검색, 모델 호출, 검증 시간을 포함한다. 절대 deadline을 계산해 아래 계층에 남은 시간을 전달하면 각 계층이 10초씩 소비하는 문제를 줄일 수 있다. 남은 시간이 너무 짧으면 새 재시도를 시작하지 않는다. 취소를 잡을 때는 자원을 정리하고 `CancelledError`를 다시 올린다. 요청 취소를 정상 답변으로 바꾸면 사용자가 떠난 뒤에도 모델 호출이 계속될 수 있다.

재시도 여부는 상태 코드만으로 결정하지 않는다. 연결 전 실패는 모델이 요청을 받지 않았을 가능성이 높다. 읽기 타임아웃은 모델이 생성했고 서버만 결과를 잃었을 수도 있다. 500도 수행 전 실패인지 수행 후 응답 실패인지 알 수 없을 수 있다. 공급자가 멱등성 키나 작업 조회를 제공하면 사용한다. 그렇지 않으면 무조건 재호출하지 말고 `outcome_unknown`을 기록해 정산과 복구 정책으로 넘긴다.

일시 오류를 다시 시도할 때는 최대 횟수, 전체 시간, 최대 비용을 함께 제한한다. 지수 백오프에 jitter를 더해 모든 요청이 동시에 돌아오는 것을 막고, `Retry-After`를 해석하되 deadline을 넘지 않게 한다. 입력 검증 실패와 인증 실패는 재시도하지 않는다. 스트림에서 이미 텍스트를 보냈다면 처음부터 다시 생성한 내용을 이어 붙여서는 안 된다. 새 attempt ID를 공개하거나 작업을 실패 상태로 종료하는 편이 계약을 명확히 한다.

## 25.5 토큰 사용량 관리

토큰은 글자 수와 같지 않다. 한국어, 코드, 공백, 이미지 입력에 따라 계산 방식이 달라진다. 공급자 모델과 토크나이저 버전에 맞는 측정이 필요하다. 접수 단계에서는 예상 입력과 최대 출력으로 상한을 예약하고, 최종 공급자 사용량으로 정산한다. 실제 금액 계산은 통화, 모델 가격 버전, 입력/출력/캐시 가격을 기록한 원장에 남긴다. 소수 금액은 정수 최소 단위나 Decimal로 계산한다.

예약은 동시 요청에 대해 원자적이어야 한다. 두 요청이 각각 잔여 예산을 읽고 “충분하다”고 판단하면 동시에 예산을 초과할 수 있다. `used + reserved + new_reservation <= quota` 조건을 UPDATE에 넣거나 사용자 예산 행을 트랜잭션에서 잠근다. 성공하면 예약을 해제하며 실제 사용량을 더하고, 수행 전 확정 실패는 예약을 돌려준다. 결과 불명 상태는 전액 환불하지 않고 공급자 확인 또는 보수적 정산 정책을 적용한다.

일별 제한만으로 갑작스러운 남용을 막기 어렵다. 분당 요청 수, 분당 예상 토큰, 동시 실행 수, 일별 비용을 함께 관리한다. 사용자에게 “일일 한도 초과”와 “현재 동시 작업 초과”를 구분해 알려 주면 재시도 폭주를 줄일 수 있다. 토큰 원장의 unique 키는 `(job_id, attempt_id, usage_kind)`처럼 중복 정산을 막도록 설계한다. 과금 이벤트가 두 번 도착하더라도 사용량을 두 번 더하지 않는다.

## 25.6 LLM 응답 스트리밍

스트리밍은 첫 글자가 나타나는 시간을 줄이지만 전체 생성 비용을 반드시 줄이지는 않는다. API는 `text/event-stream`으로 delta와 완료 이벤트를 전송할 수 있다. FastAPI의 `StreamingResponse`는 iterator 또는 async generator로 응답을 생성한다. 이 장은 공통 버전 범위에서 사용할 수 있는 이 방식으로 SSE를 직접 구성한다. [FastAPI 응답 공식 문서](https://fastapi.tiangolo.com/advanced/custom-response/)

응답 헤더를 보내기 전에 인증, 권한, 입력 검증, 예산 확보를 마친다. 스트림이 시작된 뒤에는 200을 502로 바꿀 수 없다. 대신 `event: error`와 안전한 오류 코드, attempt ID를 전송한다. 완료 이벤트에는 최종 상태와 확인된 사용량 여부를 포함한다. 클라이언트는 연결 종료와 성공 완료를 구분해야 한다. `done`을 못 받았다면 일부 글자를 받았더라도 완성 답변으로 저장하지 않는다.

클라이언트가 끊겼을 때 정책을 결정한다. 짧은 즉시 질의는 공급자 스트림을 닫고 취소할 수 있다. 사용자가 다시 접속할 장기 작업은 작업을 계속 실행하고 SSE만 구독 해제한다. 둘을 혼합하면 재접속 때 재실행과 기존 실행이 함께 존재한다. 내구성 작업은 27장, 영속 이벤트 재생은 29장에서 다룬다. 이벤트 ID는 문자열이든 숫자든 작업의 순서를 재현할 수 있어야 하며, 사용자 권한을 매 재생 경로에서도 확인한다.

## 최소 실습: 공급자 없는 생성 어댑터

아래는 **완전 실행 예제** `main.py`다. 모델 생성과 스트림의 차이를 확인하기 위한 로컬 실습으로 인증과 사용자 원장은 포함하지 않는다. 인터넷에 노출하는 운영 서버로 사용하지 않는다. 동시 호출 두 건과 3초 전체 deadline을 적용하며, 스트림 오류는 이벤트로 표현한다.

```python
import asyncio
import json
from dataclasses import dataclass
from typing import Protocol

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


@dataclass
class Result:
    text: str
    mock_units: int


class Model(Protocol):
    async def complete(self, prompt: str, limit: int) -> Result: ...


class MockModel:
    async def complete(self, prompt: str, limit: int) -> Result:
        await asyncio.sleep(0.05)
        text = ("모의 요약: " + prompt)[:limit]
        return Result(text, len(prompt) + len(text))

    async def stream(self, prompt: str, limit: int):
        result = await self.complete(prompt, limit)
        for start in range(0, len(result.text), 8):
            await asyncio.sleep(0.02)
            yield {"kind": "delta", "text": result.text[start:start + 8]}
        yield {"kind": "done", "mock_units": result.mock_units}


class Input(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    max_chars: int = Field(default=200, ge=10, le=500)


app = FastAPI()
model = MockModel()
slots = asyncio.Semaphore(2)


@app.post("/complete")
async def complete(body: Input):
    try:
        async with asyncio.timeout(3):
            async with slots:
                result = await model.complete(body.prompt, body.max_chars)
                return {"text": result.text, "mock_units": result.mock_units}
    except TimeoutError:
        raise HTTPException(504, "generation_deadline") from None


@app.post("/stream")
async def stream(body: Input):
    async def events():
        try:
            async with asyncio.timeout(3):
                async with slots:
                    async for item in model.stream(body.prompt, body.max_chars):
                        kind = item.pop("kind")
                        data = json.dumps(item, ensure_ascii=False)
                        yield f"event: {kind}\ndata: {data}\n\n"
        except TimeoutError:
            yield 'event: error\ndata: {"code":"generation_deadline"}\n\n'
        # CancelledError is deliberately not swallowed.
    return StreamingResponse(events(), media_type="text/event-stream")
```

설치 및 실행 명령은 **로컬 실습 명령**이다. 장별 실습은 독립 디렉터리에서 실행하며 이전 장의 `main.py`에 덧붙이지 않는다.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install "fastapi>=0.121,<1" "uvicorn>=0.30,<1"
.\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
curl.exe -N -X POST http://127.0.0.1:8000/stream -H "Content-Type: application/json" -d '{"prompt":"FastAPI의 역할","max_chars":80}'
```

PowerShell 버전에 따라 `curl.exe`의 JSON 인용 전달이 달라질 수 있다. 실패하면 `/docs`에서 POST를 실행하거나 UTF-8 `request.json`을 만들고 `--data-binary @request.json`을 사용한다. 기대 결과는 여러 delta 이벤트와 마지막 done 이벤트다. mock_units는 문자 수 기반 지표이며 유료 모델 토큰 수가 아니다. 공급자 호출을 수행하지 않았으므로 실제 가격·성능 검증 결과도 아니다.

이 실습에서 세마포어 대기가 스트림 헤더 이후에 일어난다는 점을 살펴보자. 용량 부족을 HTTP 429로 전달하려면 접수 단계에서 슬롯을 확보하거나 내구성 작업으로 접수해야 한다. 동시성 학습을 위해 구성한 간단한 예제이지만 실제 API 계약에서는 이 선택이 사용자 경험과 오류 처리 방법을 결정한다.

## 25.7 사용자별 호출량 제한

사용자 식별은 검증한 토큰에서 얻는다. 클라이언트가 보낸 `user_id`를 사용량 원장의 소유자로 믿으면 다른 사람에게 비용을 떠넘길 수 있다. 여러 인스턴스에서 메모리 딕셔너리로 제한하면 인스턴스 수만큼 허용량이 늘어난다. Redis 원자 연산을 빠른 접수 제한에 쓰고, 최종 비용 원장은 트랜잭션을 지원하는 저장소에 둔다. Redis 장애 때 무제한 허용할지 제한적으로 허용할지 제품의 비용 위험에 맞춰 결정한다.

요청 제한은 정상 사용자에게도 설명 가능해야 한다. API 키 교체, NAT 주소 공유, 배치 처리 때문에 IP만으로 모든 정책을 결정하기 어렵다. 계정별·조직별 예산을 중심으로 두고 IP는 보조 남용 신호로 활용한다. 관리자가 쿼터를 늘리더라도 이미 예약된 비용이 사라지지 않게 한다. 취소와 환불은 사용량 행을 삭제하는 대신 보정 이벤트를 남겨 회계를 재현한다.

## 25.8 LLM API 비용 및 지연시간 측정

측정 시작점을 명확히 적는다. 접수부터 슬롯 확보까지 queue_wait, 공급자 전송부터 첫 delta까지 TTFT, 첫 delta부터 완료까지 generation, 전체를 end_to_end로 나눈다. TTFT가 늘었는데 API CPU가 낮다면 먼저 공급자 혼잡과 대기열을 확인한다. 서버 CPU만 보고 워커를 늘리면 공급자 제한을 더 빨리 소진할 수 있다.

예를 들어 “요청당 입력 2,000토큰, 최대 출력 500토큰, 재시도율 5%”는 용량 계산 가정이지 측정값이 아니다. 실제 입력·출력 분포, 재시도별 사용량, 캐시 적중, 중도 취소를 기록해야 비용 예측이 맞는다. 평균 비용과 총 비용을 함께 보고, 비용이 큰 상위 요청을 개인정보 없이 분석한다. 모델 이름이나 사용자 ID를 메트릭 label로 무제한 넣으면 cardinality가 폭발하므로 제한된 모델 등급과 결과 유형으로 집계한다.

실무에서는 프롬프트 템플릿 버전, 모델 버전, 출력 제한, 검색 설정을 변경 기록에 포함한다. 같은 코드라도 컨텍스트가 늘어나면 지연과 비용이 함께 늘어난다. 기능 출시 기준에 답변 품질, 비용 상한, 실패 복구를 포함하면 “작동한다”와 “운영할 수 있다”를 구분할 수 있다.

## 성능과 함정

모든 요청을 `gather`로 동시에 보내는 코드는 모델 제한을 검증하기보다 폭주를 만든다. 스트림 전체를 리스트로 모은 뒤 반환하면 사용자에게 보이는 스트리밍 이점이 사라진다. 요청 취소를 잡아 `pass`하면 취소가 상위 계층에 전달되지 않는다. 무조건 세 번 재시도하면 한 요청의 최대 비용이 세 배가 된다. 각 정책을 독립 옵션으로 넣기보다 deadline과 예산이라는 공통 경계 아래에서 조합한다.

생성 텍스트를 HTML로 출력하는 프런트엔드는 escaping을 적용하고, Markdown 렌더러도 위험한 HTML과 링크 스킴을 제한한다. 모델 출력은 안전한 문자열이라는 보장이 없다. 문서 내용과 모델 응답 전체를 access log에 넣으면 운영 장애 분석 과정이 개인정보 유출 경로가 될 수 있다. 필요한 식별자와 길이, 결과 코드 중심으로 남긴다.

## 확인 문제와 해설

1. read timeout이 5초인데 생성이 1분 지속될 수 있는 이유는 무엇인가? **해설:** 주기적으로 데이터가 도착하면 개별 읽기 대기가 제한을 넘지 않을 수 있다. 별도의 전체 deadline이 필요하다.
2. 클라이언트 연결이 끊기면 예약한 비용을 전부 돌려주어도 되는가? **해설:** 공급자가 이미 처리했을 수 있다. 수행 여부와 최종 사용량을 확인하고 결과 불명 상태를 별도로 정산한다.
3. delta 10개를 보낸 뒤 공급자가 실패하면 HTTP 502를 반환할 수 있는가? **해설:** 이미 헤더를 보냈으므로 불가능하다. 스트림 오류 이벤트와 완료되지 않은 상태를 표현해야 한다.
4. 모의 모델을 실제 공급자로 바꾸는 과제의 합격 기준은 무엇인가? **해설:** 어댑터 외 라우터 계약 유지, 전체 deadline, 중복 요청 정책, 스트림 종료/오류 구분, 확인되지 않은 usage 표현이 필요하다. 외부 호출 없이 mock transport로 이 경계를 테스트할 수 있다.

## 요약과 다음 장

LLM API의 중심은 비동기 함수보다 실행 경계다. 인증한 사용자에게 예산을 예약하고, 제한된 동시성으로 공급자에 접근하며, 생성 결과와 사용량을 확정하는 구조를 만든다. 다음 장에서는 허용된 문서만 검색해 생성에 전달하는 RAG를 설계한다. 생성이 잘 되어도 잘못된 문서를 가져오면 서비스는 잘못된 답을 자신 있게 제공한다.

## 공식 참고자료

- [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/): 개별 네트워크 대기 제한.
- [FastAPI custom responses](https://fastapi.tiangolo.com/advanced/custom-response/): 공통 버전에서 사용 가능한 스트리밍 응답.
- [Python 3.12 asyncio Task](https://docs.python.org/3.12/library/asyncio-task.html): timeout, 취소, Task 수명 관리.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 24장 운영 장애와 고급 동시성](../24-incidents-concurrency/chapter.md) · [26장 RAG 서비스 백엔드 구축 →](../26-rag/chapter.md)
