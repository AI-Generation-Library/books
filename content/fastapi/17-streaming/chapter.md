---
title: "17장. 실시간 통신과 스트리밍"
description: "Knowledge Hub의 AI 답변이 20초 뒤에 완성된다고 가정하자. 완성본만 반환하면 사용자는 그동안 화면이 멈췄다고 느낄 수 있다. 생성되는 문장을 조금씩 보여 주면 작업이 진행되고 있음을 알 수 있다. 그러나 스트리밍을 붙인 순간 단일 JSON 응답의 가정이 사라진다. 연결은 길어지고, 사용자가"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 17
part: 5
---

## 학습 목표와 도입 사례

Knowledge Hub의 AI 답변이 20초 뒤에 완성된다고 가정하자. 완성본만 반환하면 사용자는 그동안 화면이 멈췄다고 느낄 수 있다. 생성되는 문장을 조금씩 보여 주면 작업이 진행되고 있음을 알 수 있다. 그러나 스트리밍을 붙인 순간 단일 JSON 응답의 가정이 사라진다. 연결은 길어지고, 사용자가 중간에 나갈 수 있으며, 일부 문장을 전송한 뒤 오류가 발생한다. 이 장에서 다루는 숫자는 상황을 설명하기 위한 가정이며 벤치마크 결과가 아니다.

학습 목표는 HTTP 스트리밍, SSE, WebSocket의 역할을 구분하고 연결 종료와 느린 소비자까지 다루는 것이다. 특히 `yield`가 브라우저 화면 갱신을 보장하는지, 언제 상태 코드를 바꿀 수 있는지, 생산자와 소비자의 수명을 누가 관리하는지 답할 수 있어야 한다. 실습은 독립 폴더에서 실행한다. 다른 장의 애플리케이션에 계속 추가하는 방식이 아니다.

## 17.1 일반 HTTP 응답과 스트리밍의 차이

일반 응답은 애플리케이션이 본문을 완성한 뒤 보낸다. 큰 데이터를 메모리에 모두 올리는 비용이 있고, 첫 바이트를 보낼 때까지 전체 계산이 끝나야 한다. 스트리밍은 본문 일부를 준비한 뒤 전송하고 다음 조각을 이어 보낸다. 첫 바이트 시간과 전체 완료 시간을 별도로 개선하거나 악화시킬 수 있다. 첫 조각이 빨라도 중간에 오랫동안 끊기면 사용 경험은 좋지 않다.

애플리케이션 조각과 네트워크 조각은 일대일 관계가 아니다. 서버, TLS, TCP, 프록시, 브라우저가 데이터를 합치거나 나누어 받을 수 있다. 클라이언트는 한 번 읽은 데이터가 한 이벤트라는 가정을 하면 안 된다. `Content-Length`를 미리 계산하지 못하는 응답도 있다. 전송 방식은 HTTP 버전과 서버가 정하며, 애플리케이션에서 수동으로 chunked 헤더를 붙일 필요가 없다.

## 17.2 StreamingResponse 동작 원리

`StreamingResponse`는 반복 가능한 객체에서 데이터를 얻어 ASGI의 응답 body 메시지를 순서대로 보낸다. 비동기 생성자에서 `yield`한 바이트나 문자열이 본문 조각이 된다. Starlette는 비동기 반복자와 일반 반복자를 지원한다. [Starlette Responses](https://starlette.dev/responses/)

핵심 순서는 `response.start → body 조각들 → 마지막 body`다. 상태 코드와 헤더는 시작 메시지에 들어간다. 첫 `yield` 직전까지라면 오류를 500으로 돌릴 수 있다고 생각하기 쉽지만, 응답 구현은 생성자의 첫 실행보다 먼저 시작 메시지를 보낼 수 있다. 따라서 입력 검증, 인증, 문서 존재 확인, 상위 서비스 초기 연결처럼 HTTP 오류로 표현해야 하는 작업은 `StreamingResponse`를 반환하기 전에 끝내야 한다.

일반 생성자 내부에 동기 작업을 넣는 방식과 비동기 생성자 안에 블로킹 작업을 넣는 방식은 다르다. 후자는 이벤트 루프를 막는다. `async def` 생성자 안에서 `time.sleep()`이나 동기 LLM SDK를 직접 호출하면 스트림 하나가 다른 요청도 늦춘다. CPU 중심 문서 파싱도 스트리밍이라는 이름으로 숨길 수 없다. 작업을 별도 프로세스나 큐로 옮기고 결과만 읽는 구조가 필요하다.

## 17.3 Server-Sent Events(SSE)

SSE는 서버에서 클라이언트로 이벤트를 보내는 텍스트 형식이다. 이벤트는 빈 줄로 끝나고 `data:`, `event:`, `id:` 등의 필드를 가진다. 여러 `data:` 줄도 가능하다. 이 장에서는 JSON을 한 줄 문자열로 만들어 data 필드에 넣는다. JSON의 줄바꿈은 인코더가 이스케이프하므로 사용자 입력으로 이벤트 구분자가 끼어드는 위험을 줄일 수 있다. 브라우저의 `EventSource`는 재연결과 마지막 이벤트 ID 전송을 지원한다. [HTML SSE 표준](https://html.spec.whatwg.org/multipage/server-sent-events.html)

이벤트 ID를 보내는 것만으로 재전송이 구현되지는 않는다. 서버가 ID 순서와 이벤트 보관 기간을 정의하고, `Last-Event-ID` 이후 자료를 다시 보내야 한다. 보관 기간을 넘긴 클라이언트에는 전체 상태를 다시 조회하게 하는 정책이 필요하다. 복구 가능한 진행 상황은 저장된 작업 ID를 기준으로 연결하고, 일시적인 토큰 출력은 재생 여부를 명확히 정한다. native EventSource에는 임의 Authorization 헤더를 지정하는 일반 옵션이 없으므로 같은 출처의 보안 쿠키나 fetch 기반 스트림처럼 인증 방식을 따로 설계한다. 토큰을 긴 URL에 넣으면 로그와 브라우저 기록에 남는다.

SSE에는 단방향이라는 장점이 있다. 질문 등록은 일반 POST로 하고 진행 상황은 GET SSE로 받을 수 있다. 개발자는 하나의 양방향 채널에 모든 기능을 넣을 필요가 없다. 작은 heartbeat 주석을 정기적으로 보내면 중간 장비의 idle timeout을 피하고 연결 상태를 확인하는 데 도움이 되지만, heartbeat를 보내는 것 자체가 장애 복구를 보장하지는 않는다.

## 17.4 WebSocket 통신

WebSocket은 연결을 수락한 뒤 양방향 메시지를 주고받는다. 채팅, 공동 편집, 빠른 클라이언트 명령 전송에 적합하다. 반면 일반 HTTP의 상태 코드, 캐시, 재시도 계약을 그대로 사용할 수 없다. 핸드셰이크에서 인증과 Origin 검사를 수행하고 연결 후 메시지의 타입, 크기, 권한을 다시 검사한다. 연결할 때 권한이 있다고 영원히 권한이 유지되는 것은 아니다.

FastAPI에서 `receive_text()`와 `send_text()`를 사용하고, 수신 연결 종료는 `WebSocketDisconnect`로 처리할 수 있다. [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

중요한 운영 질문은 메시지 전달을 얼마나 보장하느냐이다. 메모리 안의 소켓 집합에 broadcast한 메시지는 서버 재시작 때 사라지고 다른 worker에는 도달하지 않는다. 여러 인스턴스의 채팅에는 외부 pub/sub 또는 메시지 브로커가 필요하다. 영속 채팅 이력이 필요하면 메시지를 먼저 저장하고 서버가 부여한 메시지 ID를 전달한다. pub/sub와 영속 메시지 저장은 서로 다른 책임이다.

## 17.5 클라이언트 연결 종료 감지

HTTP 연결 종료는 ASGI receive의 disconnect 이벤트, send 실패, 응답 구현의 취소 등 여러 경로로 관측될 수 있다. 라이브러리와 ASGI 프로토콜 버전에 따라 세부 동작이 다르므로 `request.is_disconnected()` 한 번만 호출하면 모든 상황을 해결한다고 가정하지 않는다. 반복자의 중요한 대기 사이에서 확인하고 `finally`에서 자원을 반환한다. 취소 예외가 오면 일반 오류 이벤트를 새로 보내려 하지 말고 정리를 수행한 뒤 취소를 전파한다.

외부 응답을 스트리밍하는 경우 `async with client.stream(...)`의 범위가 실제 소비가 끝날 때까지 살아 있어야 한다. 라우트에서 with 블록을 나간 다음 그 응답 반복자를 반환하면 닫힌 연결을 읽게 된다. 생성자 내부에서 연결을 소유하게 하거나 닫기를 책임지는 명시적 래퍼를 만든다. 요청 범위의 DB 세션을 스트리밍 동안 유지하면 한 사용자의 긴 연결이 DB 풀을 붙잡을 수 있다. 먼저 필요한 자료를 짧은 트랜잭션으로 읽고 연결을 반환하는 편이 안전하다.

## 17.6 스트리밍 중 오류 처리

이미 상태 코드를 보낸 뒤에는 HTTP 200을 500으로 바꿀 수 없다. 미들웨어가 예외를 잡아도 이 사실은 변하지 않는다. 따라서 SSE 자체에 `error`, `done` 같은 종료 계약을 정한다. 예를 들어 `error` 이벤트에 안정적인 오류 코드와 작업 ID를 담고 연결을 끝낸다. 클라이언트는 HTTP 성공과 도메인 작업 성공을 구분해야 한다. `done` 없이 연결이 끊기면 완성된 답변으로 저장하지 않는다.

보안을 위해 오류 이벤트에는 상위 공급자의 전체 본문, 비밀 헤더, traceback을 넣지 않는다. 로그에는 요청 ID와 안전한 오류 종류를 기록한다. 이미 일부 문장이 전송된 사실도 남긴다. 이 정보가 없으면 운영자는 사용자가 아무것도 못 받은 요청과 부분 답변을 받은 요청을 같은 실패로 볼 수 있다. 오류 이벤트를 보내는 것마저 실패할 수 있으므로 정리 루틴은 전송 성공에 의존하지 않게 만든다.

## 최소 실습 A: SSE의 성공, 실패, 중단

아래는 **완전 실행 예제**다. 새 폴더의 `main.py`에 저장한다. 별도 생산자 Task와 큐를 만들지 않아 요청 생성자가 생산과 전송 수명을 함께 소유한다.

```python
import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

app = FastAPI()
log = logging.getLogger("hub.stream")


def event(kind: str, data: dict, number: int) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"id: {number}\nevent: {kind}\ndata: {payload}\n\n"


@app.get("/answers/{document_id}/events")
async def answer(document_id: int, request: Request, fail: bool = False):
    if document_id != 1:
        raise HTTPException(404, "문서를 찾을 수 없습니다")

    async def generate():
        completed = False
        try:
            for number, word in enumerate(["비동기는", "대기를", "겹칩니다"], 1):
                if await request.is_disconnected():
                    return
                await asyncio.sleep(0.3)
                if fail and number == 2:
                    raise RuntimeError("simulated upstream failure")
                yield event("token", {"text": word}, number)
            yield event("done", {"complete": True}, 4)
            completed = True
        except asyncio.CancelledError:
            log.info("stream_cancelled")
            raise
        except RuntimeError:
            log.warning("stream_failed")
            yield event("error", {"code": "GENERATION_FAILED"}, 4)
        finally:
            # 실제 SDK stream.close 또는 aclose도 이 수명에 둔다.
            log.info("stream_closed complete=%s", completed)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**설치와 실행 명령:**

```powershell
python -m pip install "fastapi>=0.121,<1" "pydantic>=2,<3" "uvicorn>=0.30,<1" "websockets>=13,<16"
python -m uvicorn main:app --port 8017 --log-level info
```

다른 터미널에서 `curl.exe -N "http://127.0.0.1:8017/answers/1/events"`를 실행한다. token 세 개와 done 하나를 순서대로 받아야 한다. `?fail=true`를 붙이면 token 하나 다음 error 이벤트가 나온다. 이때 HTTP 상태는 이미 200이다. 문서 ID를 9로 바꾸면 스트림 시작 전 404 JSON이 나온다. 정상 요청 중 Ctrl+C로 클라이언트를 끊고 서버 로그의 정리 메시지를 확인한다. 짧은 실습에서는 종료 시점과 로그 순서가 실행 환경에 따라 달라질 수 있다. 상태 코드 전송 이후의 실패와 생성자 정리가 평가 대상이다.

브라우저의 **완전 실행 예제**, `client.html`을 main.py와 같은 폴더에 만든다. HTML을 앱에서 제공하면 SSE와 같은 출처이므로 이 실습에는 추가 CORS가 필요 없다. 아래 HTML 다음의 라우트도 main.py에 추가하고 서버를 다시 실행한다.

```html
<!doctype html>
<meta charset="utf-8">
<pre id="output"></pre>
<script>
const output = document.querySelector('#output');
const stream = new EventSource('/answers/1/events');
stream.addEventListener('token', e => {
  output.textContent += JSON.parse(e.data).text + ' ';
});
stream.addEventListener('done', () => stream.close());
stream.addEventListener('error', e => {
  output.textContent += '\n연결 또는 작업 오류';
  stream.close();
});
</script>
```

`main.py`의 **기존 파일 변경 예제**다. 파일을 프로젝트의 위치로 한정하고 URL 입력을 파일 경로로 사용하지 않는다.

```python
from pathlib import Path
from fastapi.responses import FileResponse


@app.get("/", include_in_schema=False)
async def page():
    return FileResponse(Path(__file__).with_name("client.html"))
```

브라우저에서 `http://127.0.0.1:8017/`을 열면 문장 조각이 순서대로 표시된다.

이 클라이언트는 연결 오류와 도메인 error를 같은 화면에 표시하는 교육용 구현이다. 운영에서는 별도 이벤트 이름인 `generation_error` 등을 사용해 native error와 명확히 구별하고, 재연결·부분 결과·최종 상태 조회를 구현한다. 완료 시 `close()`를 호출하지 않으면 EventSource가 연결 종료 후 다시 연결할 수 있다.

## 17.7 느린 클라이언트와 백프레셔

스트림은 producer가 만든 속도와 consumer가 읽는 속도가 다를 수 있다. 전송 `await`가 늦어지면 다음 생성도 늦어지는 pull 구조는 자연스럽게 생산을 제한한다. 하지만 별도 Task가 계속 토큰을 만들고 무한 큐에 넣으면 소비자가 느린 만큼 큐가 커진다. 연결당 1MB가 쌓이고 연결이 1만 개라고 가정하면 대기 데이터만 약 10GB가 된다. 이 값은 용량 설명용 가정이며 실제 메모리에는 객체와 연결 비용도 더해진다.

유한 큐를 사용하면 가득 찼을 때 생산자를 기다리게 하거나, 오래된 상태 알림을 합치거나, 소비자를 종료할 수 있다. 답변 토큰을 임의로 버리는 것은 내용을 손상시키므로 진행률처럼 대체 가능한 이벤트와 구별한다. 연결당 byte 예산, 큐 길이, 최대 수명, 전송 대기 시간을 함께 제한한다. 프록시의 buffering이 활성화되어 있으면 서버는 순서대로 보내도 브라우저에는 한꺼번에 나타날 수 있다. 스트리밍 경로에서는 해당 프록시의 buffering과 idle timeout을 실제로 확인한다.

## 17.8 실시간 채팅 API 구현

다음은 `main.py`에 추가하는 **기존 파일 변경 예제**다. 메시지 한 개를 보내면 발신 연결에 확인 응답을 보내는 최소 채팅 채널이며 broadcast나 이력 저장을 구현했다고 주장하지 않는다. 한 연결의 전송을 단일 수신 루프가 소유하므로 동시 send 충돌을 피한다.

```python
from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/chat")
async def chat(socket: WebSocket):
    # 로컬 실습에는 인증이 없다. 운영 전에 핸드셰이크 권한을 검사한다.
    await socket.accept()
    try:
        while True:
            async with asyncio.timeout(60):
                text = await socket.receive_text()
            if len(text.encode("utf-8")) > 4096:
                await socket.close(code=1009)
                return
            await socket.send_json({"sender": "Knowledge Hub", "text": text})
    except WebSocketDisconnect:
        log.info("chat_disconnected")
    except TimeoutError:
        await socket.close(code=1000, reason="idle timeout")
    finally:
        log.info("chat_closed")
```

브라우저 개발자 도구에서 `const ws = new WebSocket('ws://127.0.0.1:8017/chat'); ws.onmessage = e => console.log(e.data); ws.onopen = () => ws.send('안녕');`을 실행하면 JSON 확인 응답을 받는다. HTTPS 사이트에서 비보안 ws 연결은 차단될 수 있으므로 로컬 HTTP 화면에서 실행한다. 실제 채팅 확장은 사용자 인증, 대화방 권한, 영속 메시지, 메시지 ID, 브로커를 차례로 추가한다. 메시지 크기는 서버 프로토콜 계층에서도 제한해 전체 수신 전의 자원 소비를 제어한다.

## 확인 문제와 해설

1. 첫 token을 전송한 뒤 DB 오류가 났다. HTTP 500으로 바꿀 수 있는가? **해설:** 시작 메시지가 이미 전송됐으므로 불가능하다. 스트림의 error 계약과 작업 상태 조회를 사용한다. 전송 전 필수 검증을 완료해야 한다.
2. `yield` 세 번이면 브라우저도 정확히 세 번 읽는가? **해설:** 아니다. 네트워크와 프록시가 합치거나 나눌 수 있다. SSE 구분자를 기준으로 파싱하고 프록시 buffering을 확인한다.
3. 이벤트 ID가 있으면 자동 재생되는가? **해설:** 클라이언트는 마지막 ID를 제공할 수 있지만 서버가 보관과 재생을 구현해야 한다. ID의 유일성, 순서, 만료 정책이 필요하다.
4. 생성 Task를 따로 만들었는데 사용자가 나갔다. 무엇을 확인하는가? **해설:** Task를 취소하고 종료를 기다리며, 상위 스트림과 큐를 닫는다. 취소를 삼키지 않고 `finally`가 실행되는지 검증한다. 계속 비용을 쓰는 상위 API가 없는지도 확인한다.
5. 실습 통과 기준은 무엇인가? **해설:** 404는 스트림 전 오류, 모의 생성 실패는 200 내부 error, 정상 완료는 done으로 구별되어야 한다. 중단 후 정리 로그가 나오며 종료된 연결의 작업이 계속 누적되지 않아야 한다.

## 요약과 다음 장

스트리밍은 응답을 잘게 나누는 기능인 동시에 수명과 실패 계약을 다시 설계하는 작업이다. SSE는 서버 알림에, WebSocket은 양방향 메시지에 적합하다. 시작 이후 상태 코드 변경은 불가능하며, 느린 소비자와 연결 종료를 정상적인 사건으로 처리해야 한다. 다음 장은 연결을 끊어도 계속 수행해야 하는 작업을 내구성 큐로 분리한다.

## 공식 참고자료

- [Starlette Responses](https://starlette.dev/responses/) — StreamingResponse API.
- [HTML SSE 표준](https://html.spec.whatwg.org/multipage/server-sent-events.html) — 이벤트 형식과 재연결.
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) — 수신, 송신, 연결 종료 API.
- [Python asyncio tasks](https://docs.python.org/3.12/library/asyncio-task.html) — 취소와 구조화된 작업 수명.
- [Nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) — 프록시 buffering과 timeout 설정.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 16장 HTTP 클라이언트와 외부 API 연동](../16-http-clients/chapter.md) · [18장 백그라운드 작업과 메시지 큐 →](../18-background-jobs/chapter.md)
