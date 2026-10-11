---
title: "14장. 예외 처리와 오류 응답"
description: "예외를 HTTP 응답으로 번역하는 경계를 정하고, 요청 검증 오류와 서버 오류를 구분한다. 일관된 Problem Details 응답을 만들며 DB rollback과 로깅의 책임을 연결한다. 실습에서는 도메인 충돌, 없는 문서, 잘못된 입력, 예상하지 못한 오류를 재현한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 14
part: 4
---

## 학습 목표

예외를 HTTP 응답으로 번역하는 경계를 정하고, 요청 검증 오류와 서버 오류를 구분한다. 일관된 Problem Details 응답을 만들며 DB rollback과 로깅의 책임을 연결한다. 실습에서는 도메인 충돌, 없는 문서, 잘못된 입력, 예상하지 못한 오류를 재현한다.

문서 API가 어떤 경우에는 `{"detail":"없음"}`, 어떤 경우에는 `{"error":"failed"}`, 어떤 경우에는 Python traceback을 반환한다면 클라이언트는 실패의 원인을 안정적으로 처리하기 어렵다. 오류 응답도 성공 응답과 같은 API 계약이다. 오류를 모두 200으로 보내거나 모든 예외를 400으로 바꾸면 모니터링과 재시도 판단까지 잘못된다.

## 14.1 HTTPException의 동작 원리

`HTTPException`은 라우트가 의도한 HTTP 실패를 나타내는 예외다. `return HTTPException(...)`이 아니라 `raise HTTPException(...)`으로 흐름을 중단한다. 호출 스택을 빠져나온 예외는 프레임워크의 핸들러가 응답으로 바꾼다. 일반 반환값과 오류를 명확히 구분하므로 이후 정상 처리 코드가 실행되지 않는다.

`detail`은 사용자에게 전달할 수 있는 내용이며 내부 예외의 전체 문자열을 그대로 넣는 공간이 아니다. 인증 실패에서는 `WWW-Authenticate`, 요청 제한에서는 `Retry-After` 같은 헤더가 의미를 갖는다. 사용자 정의 핸들러로 응답을 바꿀 때도 필요한 헤더를 보존한다. 기본 처리와 핸들러 재정의는 [FastAPI 오류 안내](https://fastapi.tiangolo.com/tutorial/handling-errors/)를 참고한다.

엔드포인트 안에서 raise했더라도 서비스 전체가 중단되는 것은 아니다. 해당 요청 흐름이 실패하고 다른 요청은 계속 처리된다. 반면 import 시점의 잘못된 설정이나 lifespan의 초기화 실패는 앱 시작 자체를 막을 수 있다. 요청 오류와 서버 준비 오류를 같은 전역 핸들러로 다 해결하려 하지 않는다.

## 14.2 사용자 정의 예외 클래스

도메인 예외는 업무 의미를 표현한다. `DocumentNotFound`, `DocumentConflict`, `QuotaExceeded` 같은 이름은 실패한 규칙을 드러낸다. 서비스가 HTTP 404라는 숫자를 알고 있을 필요는 없다. HTTP 진입점은 404로, 큐 작업은 재처리 불가 상태로, CLI는 오류 메시지와 종료 코드로 번역할 수 있다.

예외에 담을 필드는 최소화한다. 내부 추적용 문서 ID나 오류 코드는 유용하지만 전체 요청 본문, 비밀번호, access token을 넣으면 로깅 과정에서 유출될 수 있다. public 메시지와 내부 원인은 분리한다. `raise DomainError(...) from error`는 원인의 연결을 보존하지만 이를 클라이언트에 그대로 출력할 필요는 없다.

예외의 종류를 지나치게 세분화하면 핸들러가 많아지고 클라이언트가 안정적으로 처리하기 어렵다. 사용자의 조치나 서버 정책이 달라지는 실패를 중심으로 나눈다. “중복 문서”는 입력 변경이 필요하고 “DB 연결 없음”은 입력을 바꿔도 해결되지 않는다. 같은 실패라는 이유로 같은 400에 묶지 않는다.

## 14.3 전역 Exception Handler

핸들러는 예외 타입에 따라 응답을 만든다. 예상한 도메인 예외에는 업무 오류 코드와 안전한 메시지를, 일반 예외에는 내부 원인을 숨긴 500을 반환한다. 예상 오류까지 매번 traceback으로 기록하면 운영 로그에 잡음이 커진다. 예상하지 못한 오류를 분류하고 추적할 수 있는 식별자를 남긴다.

FastAPI의 `HTTPException`은 Starlette 예외를 기반으로 한다. 라우팅의 404와 405까지 같은 계약으로 처리하려면 Starlette의 HTTPException 타입에 핸들러를 등록하는 방법을 사용할 수 있다. `RequestValidationError`는 별도 타입이므로 별도 처리한다. 등록만으로 OpenAPI에 모든 오류 스키마가 자동 반영되는 것은 아니어서 운영 API에서는 `responses` 선언도 맞춘다.

미들웨어의 오류와 이미 전송이 시작된 응답의 오류도 구분한다. 스트림을 시작한 뒤 발생한 예외를 일반 JSON 500으로 바꾸면 이미 보낸 상태와 데이터는 되돌릴 수 없다. 스트림은 이벤트 수준 오류와 연결 종료 정책을 별도로 설계해야 한다. BackgroundTasks가 실패해도 전송 완료된 성공 응답을 새 오류로 바꿀 수 없다.

## 14.4 요청 검증 오류 처리

잘못된 JSON, 누락 필드, 잘못된 자료형은 비즈니스 서비스에 들어오기 전에 거절된다. FastAPI의 요청 검증 오류는 일반적으로 422로 반환된다. 팀에서 400을 선택할 수도 있지만 기본값을 바꾸는 것보다 명세, 테스트, 클라이언트 해석을 일관되게 하는 것이 중요하다.

`exc.errors()`에는 위치, 오류 유형, 메시지 외에 실제 입력이나 검증 컨텍스트가 포함될 수 있다. 전체 자료를 그대로 로그나 응답에 복사하면 비밀번호 같은 값이 노출될 수 있다. 실습은 입력과 컨텍스트를 버리고 필드 위치와 오류 코드만 공개한다. 메시지를 직접 만드는 validator 역시 원래 입력값을 문자열에 삽입하지 않도록 한다.

응답 모델 검증 실패는 요청 검증 실패와 다르다. 클라이언트 입력이 아니라 서버가 자기 응답 계약을 어긴 것이므로 보통 내부 오류로 처리한다. 모든 Pydantic ValidationError를 422로 바꾸면 서버 버그를 사용자의 잘못으로 보고하게 된다. 오류가 어느 경계에서 발생했는지 구분한다.

## 14.5 표준 오류 응답 형식 설계: 실행 실습

Problem Details는 HTTP API 오류를 표현하는 공통 자료 구조다. `type`, `title`, `status`, `detail`, `instance`에 확장 필드를 더할 수 있다. 이 실습은 `about:blank` 유형과 `code`, `request_id`, `errors` 확장을 사용한다. 기본 필드의 의미와 확장 원칙은 [RFC 9457](https://datatracker.ietf.org/doc/html/rfc9457)을 참고한다.

새 디렉터리에 `errors_lab.py`를 저장하고 실행한다. 메모리 데이터만 사용하므로 서버 재시작 때 문서는 사라진다.

```powershell
python -m pip install "fastapi>=0.121,<1" "uvicorn[standard]"
python -m uvicorn errors_lab:app --reload
```

완전 실행 예제, `errors_lab.py`:

```python
import logging
from http import HTTPStatus
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("hub.errors")
app = FastAPI(title="Knowledge Hub Error Lab")
documents: dict[int, str] = {1: "오류 설계"}

class DocumentNotFound(Exception):
    pass

class DocumentConflict(Exception):
    pass

class CreateDocument(BaseModel):
    title: str = Field(min_length=1, max_length=200)

def problem_response(
    request: Request, status: int, title: str, detail: str,
    code: str, errors: list[dict] | None = None,
    headers: dict[str, str] | None = None,
):
    request_id = getattr(request.state, "request_id", uuid4().hex)
    content = {
        "type": "about:blank", "title": title, "status": status,
        "detail": detail, "instance": f"urn:request:{request_id}",
        "code": code, "request_id": request_id,
    }
    if errors is not None:
        content["errors"] = errors
    safe_headers = dict(headers or {})
    safe_headers["X-Request-ID"] = request_id
    return JSONResponse(
        content, status_code=status, headers=safe_headers,
        media_type="application/problem+json",
    )

@app.middleware("http")
async def request_identity(request: Request, call_next):
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.exception_handler(DocumentNotFound)
async def not_found(request: Request, error: DocumentNotFound):
    return problem_response(
        request, 404, "Not Found", "문서가 없습니다", "document_not_found"
    )

@app.exception_handler(DocumentConflict)
async def conflict(request: Request, error: DocumentConflict):
    return problem_response(
        request, 409, "Conflict", "이미 등록한 제목입니다", "document_conflict"
    )

@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, error: RequestValidationError):
    fields = [{
        "field": ".".join(str(part) for part in item["loc"]),
        "code": item["type"],
    } for item in error.errors()]
    return problem_response(
        request, 422, "Unprocessable Content", "입력 형식을 확인하세요",
        "invalid_request", errors=fields,
    )

@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, error: StarletteHTTPException):
    # 내부 detail을 무조건 공개하지 않는 최소 정책이다.
    title = HTTPStatus(error.status_code).phrase
    return problem_response(
        request, error.status_code,
        title,
        "요청을 처리할 수 없습니다", "http_error", headers=error.headers,
    )

@app.exception_handler(Exception)
async def internal_error(request: Request, error: Exception):
    log.error("unexpected_error", extra={
        "request_id": getattr(request.state, "request_id", "unknown"),
        "error_class": type(error).__name__,
    })
    return problem_response(
        request, 500, "Internal Server Error", "잠시 후 다시 시도하세요",
        "internal_error",
    )

@app.get("/documents/{document_id}")
async def read_document(document_id: int):
    if document_id not in documents:
        raise DocumentNotFound()
    return {"id": document_id, "title": documents[document_id]}

@app.post("/documents", status_code=201)
async def create_document(body: CreateDocument):
    title = body.title.strip()
    if not title:
        raise StarletteHTTPException(422)
    if title in documents.values():
        raise DocumentConflict()
    document_id = max(documents, default=0) + 1
    documents[document_id] = title
    return {"id": document_id, "title": title}

@app.get("/lab/failure")
async def failure():
    raise RuntimeError("storage component unavailable")
```

`GET /documents/99`는 404이며 `code`는 `document_not_found`다. `POST /documents`에 `{}`를 보내면 422와 `body.title` 위치가 나온다. 제목 `오류 설계`를 등록하면 409다. `/lab/failure`는 500이며 응답에 RuntimeError 메시지와 traceback이 포함되지 않는다. `Content-Type`은 `application/problem+json`이고 헤더와 본문의 request ID가 일치해야 한다.

실습의 등록 함수에는 await가 없어 단일 이벤트 루프의 실행 구간에서 사전 접근이 연속으로 이루어진다. 이것은 DB 경쟁 방지 수단이 아니다. 실제 저장은 유일 제약과 트랜잭션으로 보호한다. `/lab/failure`는 검증 전용으로 배포에서 제거한다. 일반 예외 핸들러를 등록하더라도 테스트 클라이언트의 기본 설정은 서버 예외를 다시 올릴 수 있으므로 500 응답을 검사할 때 `raise_server_exceptions=False`를 사용한다.

`about:blank`의 title은 실제 상태의 통상 명칭을 사용한다. 실습은 HTTPStatus에서 명칭을 가져오며 운영에서는 각 업무 오류의 고유 type URI도 정의할 수 있다. 클라이언트 분기는 번역될 수 있는 자연어 메시지가 아니라 안정적인 code를 기준으로 한다.

## 14.6 DB 오류와 외부 API 오류 처리

DB IntegrityError에는 중복뿐 아니라 외래 키나 NOT NULL 실패도 들어간다. 모든 무결성 오류를 409 “중복”으로 표현하면 데이터 설계 버그를 감춘다. 기대한 제약 이름과 드라이버 오류 코드를 확인해 업무 충돌만 번역하고 나머지는 안전한 내부 오류로 기록한다. Pool timeout은 입력 오류가 아니므로 400으로 처리하지 않는다.

외부 API도 HTTP 오류와 연결 오류, timeout, 잘못된 응답을 구분한다. 외부 시스템의 401은 사용자가 이 서버에 로그인하지 않았다는 뜻이 아닐 수 있다. 서버의 공급자 키 오류라면 내부 운영 문제다. 외부 오류 본문에는 계정 정보나 요청 입력이 포함될 수 있어 그대로 전달하지 않는다.

재시도 여부는 상태 코드만으로 결정하지 않는다. 읽기 요청의 일시적 네트워크 실패는 제한된 재시도를 검토할 수 있지만 결제나 문서 생성은 이미 성공했는지 모호할 수 있다. 멱등성 키, 총 deadline, 최대 횟수를 함께 둔다. 사용자가 입력을 바꿔야 하는 422를 자동 재시도하면 같은 오류가 반복된다.

HTTP 계약의 예로 일시 사용 불가에는 503, 상류 응답이 잘못된 경우에는 502, 상류 timeout에는 504를 고려한다. 무조건 한 상태에 대응시키기보다 이 서버의 역할과 클라이언트가 해야 할 행동에 맞춘다. 내부 메트릭에는 공급자 timeout, DB pool wait 같은 실제 원인 코드도 기록한다.

## 14.7 오류 로깅과 민감정보 보호

로그는 문제를 재현할 수 있는 최소 맥락을 남긴다. request ID, 내부 오류 종류, 서비스·버전, 안전한 자원 식별자, 처리 단계가 도움이 된다. Authorization 헤더, 쿠키, 비밀번호, 전체 문서, 전체 SQL 파라미터를 기본 수집 대상으로 삼지 않는다. 마스킹은 응답 작성 때뿐 아니라 로그와 추적 수집 전에 적용한다.

실습은 오류 클래스와 request ID만 남겨 정보 노출을 줄인다. 실제 운영에서 traceback이 필요하면 접근을 제한한 저장소에 기록하고 예외 문자열과 로컬 변수에 비밀값이 포함되는지를 점검한다. stack trace를 남긴다는 이유로 사용자에게 동일 정보를 반환하지 않는다. 로그 보호의 기준은 [OWASP 로깅 안내](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)를 참고한다.

사용자가 준 request ID를 아무 검증 없이 로그 문자열에 붙이면 로그 주입이나 상관관계 혼동이 생길 수 있다. 실습은 서버가 생성한 UUID만 사용한다. 외부 추적 ID를 수용해야 하면 허용 문자와 길이를 검증하고 내부 ID와 구분한다. request ID는 인증 증거가 아니라 추적용 값이다.

예상한 404가 폭증하면 정상 사용자 탐색 실패인지 공격인지 별도 분석할 수 있다. 예상 오류를 모두 숨기거나 반대로 모든 실패를 긴 traceback으로 기록하지 않고 오류율, 코드별 횟수, 안전한 표본 로그를 함께 사용한다.

## 14.8 예외 처리와 트랜잭션 롤백

전역 오류 핸들러는 응답의 책임을 가지며 모든 DB 세션을 자동으로 되돌리는 도구가 아니다. 세션의 소유자가 트랜잭션 경계에서 rollback해야 한다. `async with session.begin()` 안에서 오류가 밖으로 전파되면 rollback 후 예외가 핸들러로 이동한다. 핸들러는 정리된 실패를 HTTP로 표현한다.

문제를 숨기는 전형적인 코드는 DB 오류를 잡고 로그만 쓴 뒤 성공 값을 반환하는 것이다. 이미 세션이 실패 상태인데 다음 조회를 시도할 수도 있다. 업무 실패를 성공으로 바꾸지 말고 필요한 rollback을 수행한 뒤 명시적 예외를 올린다. 외부 이메일과 같은 부작용은 DB rollback으로 취소되지 않는다는 점도 유지한다.

오류 번역을 서비스에서 하는 경우에는 트랜잭션 블록 바깥에서 처리하는 편이 간단하다. 예를 들어 IntegrityError가 begin 블록을 빠져나와 rollback을 완료한 뒤 `DocumentConflict`로 바꾼다. 사용자의 요청 취소와 서버 종료를 나타내는 취소 예외를 일반 실패로 삼아 무한 재시도하지 않는다.

## 확인 문제와 해설

1. 모든 오류를 200과 error 필드로 반환하면 무엇이 어려워지는가? **해설:** HTTP 클라이언트, 프록시, 모니터링의 실패 판단이 흐려지고 재시도 정책이 잘못 적용될 수 있다.
2. 요청 검증과 응답 검증 오류를 모두 422로 바꾸어도 되는가? **해설:** 응답 계약 실패는 서버 버그다. 경계와 책임을 구분해 내부 오류로 처리한다.
3. 전역 핸들러가 DB rollback을 자동 수행하는가? **해설:** 아니다. 세션과 트랜잭션 소유자가 정리한 뒤 핸들러가 응답을 만든다.
4. 실습 과제: 404, 409, 422, 500을 호출하고 공통 필드를 검사하라. **평가 기준:** 실제 HTTP 상태와 body.status가 같고 request ID가 있으며 입력값과 traceback이 노출되지 않는다. 인증 핸들러를 추가한다면 WWW-Authenticate를 보존한다.

## 요약과 다음 장

예외는 내부 실패의 의미를 표현하고 핸들러는 공개 오류 계약을 만든다. 검증 오류의 입력값과 내부 예외를 무분별하게 공개하지 않고 rollback 책임은 자원 소유자에게 둔다. 다음 장에서는 HTTPS, 브라우저 보안, 업로드, 프록시까지 API 전체의 경계를 보호한다.

## 공식 참고자료

- [FastAPI — Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/): HTTPException과 핸들러 등록.
- [RFC 9457 — Problem Details](https://datatracker.ietf.org/doc/html/rfc9457): 표준 오류 필드와 확장.
- [OWASP — Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html): 로그의 민감정보와 접근 보호.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 13장 인증과 인가](../13-authentication/chapter.md) · [15장 API 보안 →](../15-api-security/chapter.md)
