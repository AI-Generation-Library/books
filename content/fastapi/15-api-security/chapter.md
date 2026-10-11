---
title: "15장. API 보안"
description: "HTTPS, CORS, CSRF, XSS가 보호하는 경계를 구분하고 SQL과 파일 업로드를 안전하게 처리한다. API Key와 비밀값의 수명, 요청 크기, 권한, 프록시의 신뢰 범위를 설계한다. 최소 실습은 API Key로 보호한 작은 UTF-8 텍스트 업로드 API다. 인증과 입력 검증만 통과하면 안전"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 15
part: 4
---

## 학습 목표

HTTPS, CORS, CSRF, XSS가 보호하는 경계를 구분하고 SQL과 파일 업로드를 안전하게 처리한다. API Key와 비밀값의 수명, 요청 크기, 권한, 프록시의 신뢰 범위를 설계한다. 최소 실습은 API Key로 보호한 작은 UTF-8 텍스트 업로드 API다. 인증과 입력 검증만 통과하면 안전하다는 가정을 버리고 데이터가 이동하는 각 경계를 확인한다.

Knowledge Hub는 사용자가 올린 문서를 읽고 검색하며 나중에는 LLM에 전달한다. 하나의 입력이 파일시스템, 파서, DB, 브라우저, 외부 모델을 거친다. `title: str`이라는 타입 검증은 제목이 문자열임을 확인할 뿐 경로 사용, HTML 렌더링, SQL 실행을 각각 안전하게 만들지 않는다. 보안은 입력 하나를 한 번 검사하는 문제가 아니라 사용하는 위치의 규칙을 지키는 문제다.

## 15.1 HTTPS와 TLS

HTTPS는 HTTP 통신을 TLS로 보호한다. 클라이언트는 서버 인증서를 검증하고 통신 내용의 기밀성과 무결성을 얻는다. 이것은 서버 내부의 잘못된 권한 검사나 악성 파일 처리를 고치지 않는다. 토큰과 비밀번호는 HTTPS로 전송하며 운영 클라이언트에서 인증서 검증을 끄지 않는다.

배포에서는 보통 로드밸런서나 역방향 프록시가 TLS를 종료하고 내부 Uvicorn에 HTTP로 전달한다. 이때 내부 구간을 어떤 네트워크에서 보호할지 결정한다. 외부와 내부가 모두 신뢰된다고 가정하지 말고 네트워크 경계와 인증 요구를 구체화한다. 인증서 갱신 실패와 만료 감시도 운영 책임이다.

HSTS는 브라우저에 향후 HTTPS 사용을 기억하게 하는 응답 정책이다. HTTPS 구성이 안정적으로 동작하는 호스트에서 적용하며 `includeSubDomains`는 하위 도메인까지 HTTPS가 준비되어야 한다. 로컬 HTTP 실습에 운영 HSTS 정책을 무조건 복사하지 않는다. HTTPS redirect도 신뢰할 수 있는 실제 원래 요청 scheme을 알아야 올바르게 동작한다.

## 15.2 CORS의 동작 원리

Origin은 scheme, host, port의 조합이다. `http://localhost:5173`과 `http://localhost:8000`은 다른 origin이다. 브라우저는 교차 출처 JavaScript가 응답을 읽을 수 있는지 CORS 헤더로 판단한다. 특정 메서드나 헤더는 사전 OPTIONS 요청으로 허용 여부를 확인한다. FastAPI 설정은 [공식 CORS 문서](https://fastapi.tiangolo.com/tutorial/cors/)에 설명되어 있다.

CORS는 브라우저의 읽기 정책이지 서버 인증이 아니다. curl이나 다른 서버는 CORS와 무관하게 API를 호출할 수 있다. 일부 단순 요청은 먼저 서버에서 실행되고 브라우저가 응답 읽기만 막을 수 있다. 그러므로 허용 origin만 설정했다고 부작용 있는 작업을 보호했다고 생각하면 안 된다.

쿠키를 포함하는 요청에는 credential 정책과 정확한 origin 허용 목록이 필요하다. 운영 주소를 지정하고 검증하지 않은 정규식으로 광범위한 도메인을 허용하지 않는다. 개발에서 모든 origin을 열었다가 운영에도 남기는 실수를 막기 위해 설정을 환경별로 분리한다. 오류 응답에도 CORS 헤더가 필요한 경우 애플리케이션 바깥을 CORSMiddleware로 감싸는 방법을 사용한다.

## 15.3 CSRF와 XSS

CSRF는 사용자가 가진 자동 전송 자격 증명을 악용해 원하지 않은 작업을 수행시키는 공격이다. 쿠키 세션을 사용한다면 토큰 검증, Origin 검증, 적절한 SameSite 정책을 함께 검토한다. GET 요청으로 데이터 변경을 수행하지 않는다. 쿠키의 Secure와 HttpOnly는 중요한 속성이지만 CSRF를 직접 해결하는 조합은 아니다. 세부 방어 패턴은 [OWASP CSRF 안내](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)를 참고한다.

XSS는 공격자가 입력한 스크립트가 신뢰하는 페이지에서 실행되는 문제다. API가 JSON을 반환해도 프런트엔드가 문서 내용을 `innerHTML`에 넣으면 위험하다. HTML, JavaScript, URL, CSS처럼 사용되는 문맥마다 다른 출력 인코딩이 필요하다. 마크다운 렌더링에서 원시 HTML을 허용하는 정책도 확인한다.

HttpOnly 쿠키는 JavaScript가 토큰 원문을 읽는 것을 줄이지만 XSS가 로그인 사용자의 권한으로 API를 호출할 수 있는 상황까지 없애지 않는다. CSP는 스크립트 실행 범위를 줄이는 보조 방어이며 안전한 렌더링을 대신하지 않는다. API와 Swagger UI처럼 HTML 화면의 정책은 다를 수 있다.

Knowledge Hub의 검색 결과와 LLM 답변도 외부 입력에 가까운 출력이다. 답변에 들어온 링크나 HTML을 그대로 신뢰하지 않는다. 프롬프트가 문서 안에 있다고 해서 서버의 권한이 생기는 것도 아니다. 모델에 전달하는 텍스트와 서버가 승인한 실행 권한을 별도 경계로 유지한다.

## 15.4 SQL Injection 방어

값은 바인드 파라미터로 전달한다. `f"SELECT ... WHERE title='{title}'"`처럼 문자열을 조립하면 입력의 따옴표와 SQL 문법이 뒤섞인다. ORM을 쓰더라도 `text()` 안에 f-string을 넣으면 같은 문제가 생긴다. SQLAlchemy 표현식과 바인드 파라미터를 사용하면 값과 SQL 구조를 구분할 수 있다.

개념 예제, 기존 세션과 `documents` 테이블을 전제로 한 안전한 값 전달:

```python
from sqlalchemy import text

statement = text("SELECT id, title FROM documents WHERE title = :title")
parameters = {"title": "사용자가 입력한 문자열"}
# 실제 비동기 세션에서는 await session.execute(statement, parameters)
```

컬럼 이름, 테이블 이름, 정렬 방향은 일반 값 파라미터로 대체할 수 없다. 사용자가 보낸 `sort`를 곧바로 SQL 구조에 넣지 말고 허용 목록에서 실제 컬럼 객체를 선택한다. DB 계정의 최소 권한, 결과 개수 제한, 쿼리 timeout도 피해 범위를 줄인다. 입력 필터로 특정 단어를 금지하는 것보다 SQL 구조와 값을 분리하는 것이 근본 방어다.

## 15.5 Rate Limiting과 API 남용 방지

인증된 사용자도 과도한 요청을 보낼 수 있다. LLM 생성과 파일 파싱은 비용이 크므로 요청 횟수 외에 동시 실행 수, 입력 크기, 총 토큰, 저장량을 제한한다. 사용자별 제한과 전체 서비스 제한을 함께 둬야 한 사용자의 분산 요청이나 많은 계정의 합산 부하를 통제할 수 있다.

IP 제한은 익명 유입에 도움이 되지만 NAT 환경의 정상 사용자를 함께 막을 수 있고 프록시 설정이 잘못되면 모든 요청이 같은 IP로 보인다. `X-Forwarded-For`를 공격자가 마음대로 보냈는데 신뢰하면 제한을 우회할 수 있다. 인증 후에는 검증된 사용자 ID나 API Key ID로 제한한다.

제한 초과에는 429와 재시도 안내를 제공한다. 비용을 보호하는 저장소가 장애일 때 무제한 허용할지 일시 거절할지 명시한다. 12장의 Redis 예제는 카운터를 설명하는 시작점이고, 이번 업로드 실습에는 분산 rate limiter나 사용자별 저장량 제한이 포함되어 있지 않다. 운영 전환에서는 요청 수 제한과 실제 바이트·작업량 제한을 결합한다.

## 15.6 파일 업로드 보안: 완전 실행 실습

사용자가 전송한 파일 이름은 경로가 될 수 없다. `../../secret` 같은 문자열을 조합하지 않고 서버가 임의 ID를 만든다. 확장자와 Content-Type은 사용자가 보낼 수 있는 주장이라 내용 검사와 파서 정책이 별도로 필요하다. 압축 파일은 압축 크기뿐 아니라 압축 해제 후 크기, 파일 개수, 중첩 수준을 제한한다. 일반적인 방어 원칙은 [OWASP 업로드 안내](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)를 참고한다.

아래 API는 UTF-8 텍스트만 받아 최대 5MiB를 저장한다. 사용자 파일명을 무시하고 웹 공개 경로 밖의 `private_uploads`에 저장한다. 인증 수단은 공유 API Key 하나이므로 여러 사용자의 소유권 관리 예제는 아니다.

```powershell
python -m pip install "fastapi>=0.121,<1" "uvicorn[standard]" python-multipart anyio
$env:HUB_UPLOAD_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m uvicorn upload_lab:app --reload
```

완전 실행 예제, `upload_lab.py`:

```python
import asyncio
import codecs
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import uuid4
import anyio
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.security import APIKeyHeader
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

MAX_SIZE = 5 * 1024 * 1024
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

@asynccontextmanager
async def lifespan(api: FastAPI):
    key = os.environ["HUB_UPLOAD_API_KEY"]
    if len(key.encode("utf-8")) < 32:
        raise RuntimeError("충분히 긴 무작위 API Key가 필요합니다")
    api.state.api_key = key
    api.state.upload_root = Path("private_uploads").resolve()
    await asyncio.to_thread(api.state.upload_root.mkdir, parents=True, exist_ok=True)
    yield

api = FastAPI(title="Knowledge Hub Upload Lab", lifespan=lifespan)
api.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"]
)

async def require_api_key(
    request: Request,
    supplied: Annotated[str | None, Depends(api_key_header)],
):
    expected = request.app.state.api_key
    if supplied is None or not secrets.compare_digest(
        supplied.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(401, "API Key를 확인하세요")

@api.post("/documents/upload", status_code=201)
async def upload_document(
    request: Request, file: UploadFile,
    authenticated: Annotated[None, Depends(require_api_key)],
):
    file_id = uuid4().hex
    destination = request.app.state.upload_root / f"{file_id}.txt"
    decoder = codecs.getincrementaldecoder("utf-8")("strict")
    total = 0
    completed = False
    try:
        async with await anyio.open_file(destination, "xb") as output:
            while chunk := await file.read(64 * 1024):
                total += len(chunk)
                if total > MAX_SIZE:
                    raise HTTPException(413, "파일 크기 제한을 초과했습니다")
                if b"\x00" in chunk:
                    raise HTTPException(415, "텍스트 파일만 허용합니다")
                decoder.decode(chunk, final=False)
                await output.write(chunk)
            decoder.decode(b"", final=True)
            if total == 0:
                raise HTTPException(422, "빈 파일은 허용하지 않습니다")
        completed = True
        return {"file_id": file_id, "bytes": total, "status": "stored"}
    except UnicodeDecodeError as error:
        raise HTTPException(415, "UTF-8 텍스트만 허용합니다") from error
    finally:
        await file.close()
        if not completed:
            await asyncio.to_thread(destination.unlink, missing_ok=True)

class SecurityHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("X-Content-Type-Options", "nosniff")
                headers.setdefault("Referrer-Policy", "no-referrer")
                headers.setdefault("X-Frame-Options", "DENY")
                headers.setdefault("Cache-Control", "no-store")
            await send(message)
        if scope["type"] == "http":
            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)

app = CORSMiddleware(
    SecurityHeaders(api),
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

`/docs`에서 multipart 파일과 X-API-Key를 보내거나 HTTP 클라이언트로 업로드한다. 유효한 UTF-8 파일은 201과 서버 생성 file_id를 반환한다. 잘못된 키는 401, UTF-8이 아닌 입력과 NUL 바이트는 415, 5MiB 초과는 413이다. 거절된 파일은 완성 저장 파일로 남지 않아야 한다. 파일명에 경로 문자를 넣어도 서버 저장 이름은 UUID다.

여기서 중요한 한계가 있다. `UploadFile` 엔드포인트에 들어오기 전에 multipart 파서가 요청 본문을 읽어 임시 파일에 보관할 수 있다. 라우트의 5MiB 검사는 저장·처리 크기를 제한하지만 업로드 수신 자체의 메모리와 임시 디스크를 완전히 보호하지 않는다. 인증 의존성도 파서가 읽은 바이트를 소급해 없애지 못한다. 운영에서는 프록시의 전체 요청 크기와 업로드 속도·시간 제한, multipart 파서 제한, 임시 저장 공간, 동시 업로드 수를 함께 설정한다.

UTF-8 확인은 무해성의 증명이 아니다. 텍스트 안에도 HTML, 악성 링크, 모델 지시가 들어갈 수 있다. 이 실습에는 바이러스 검사, 콘텐츠 격리 승인, 사용자별 소유권, 다운로드 API, 파일 보존 정책이 없다. 운영 파싱은 권한을 줄인 별도 작업 환경에서 크기·시간을 제한하고 공개 다운로드는 검증 상태와 권한을 확인한다.

취소와 파일 정리는 별도 검증이 필요하다. 예제 finally는 일반 거절 시 임시 결과를 제거한다. 서버 프로세스 강제 종료나 머신 장애는 finally 실행을 보장하지 않으므로 미완성 파일을 정리하는 주기적 정책과 저장 상태 관리가 필요하다. 취소 전파가 정리 await에 미치는 영향도 사용하는 서버와 테스트 환경에서 확인한다.

## 15.7 API Key와 Secret 관리

API Key는 기계 클라이언트에 편한 자격 증명이지만 같은 키를 공유하면 누가 호출했는지 구분하기 어렵다. 운영 키는 ID와 비밀 부분을 나누고 소유자, 허용 권한, 만료, 폐기, 마지막 사용 시각을 기록한다. 충분한 무작위 비밀값을 한 번 보여 주고 서버에는 검증용 해시를 저장하는 방식을 검토한다.

비밀값은 저장소, Docker 이미지, 프런트엔드 번들에 넣지 않는다. 환경변수와 비밀 관리 시스템의 접근 권한, 배포 파이프라인 출력, 오류 수집에서 노출되지 않도록 한다. 개발용 키도 운영 키와 구분한다. 키를 바꿀 때 신·구 키를 잠깐 함께 검증하는 기간과 구 키 폐기 시점을 설계하면 클라이언트 중단을 줄일 수 있다.

실습의 API Key는 하나의 설정값과 상수 시간 비교를 보여 주는 단순화다. 비교 함수 하나로 키의 생성, 보관, 회수 문제가 해결되지는 않는다. URL query에 키를 넣으면 방문 기록과 로그에 남기 쉽기 때문에 헤더 전송을 사용한다. 공개 브라우저 코드에 서비스 전체 비밀키를 포함하지 않는다.

## 15.8 요청 데이터 검증과 보안 경계

Pydantic 검증은 자료형과 범위를 확인하는 첫 경계다. 비즈니스 권한, 외부 URL 접근, 파서 실행, 모델 도구 권한은 별도 경계다. `HttpUrl`이 통과해도 내부 IP, localhost, 클라우드 메타데이터 주소 접근을 막는 정책은 생기지 않는다. URL을 서버가 대신 요청하는 기능에는 SSRF 방어와 네트워크 접근 정책이 필요하다.

모든 자원 ID는 요청자가 그 자원을 사용할 수 있는지 확인한다. 존재하는 ID라는 사실과 사용 가능한 ID라는 사실을 구분한다. 업데이트 모델에서 `role`, `owner_id`, `billing_limit` 같은 내부 필드를 자동 복사하면 대량 할당 취약점이 생길 수 있다. 허용 필드만 선언한 입력 DTO와 명시적 갱신 코드를 사용한다.

문서 파싱과 AI 도구 실행에는 크기, 실행 시간, 권한, 네트워크, 파일 접근 제한을 둔다. “문서 내용에 관리자로 실행하라고 적혀 있다”는 것은 외부 입력이다. 모델이 만든 tool argument도 검증하고 실제 실행 전에 현재 사용자의 서버 정책을 다시 적용한다. 보안 경계는 자연어 지시보다 코드와 인프라에서 강제한다.

## 15.9 보안 헤더와 프록시 설정

실습의 `nosniff`는 브라우저가 Content-Type을 임의 추측하는 것을 줄이고, Referrer-Policy는 참조 URL 전송을 제한한다. Cache-Control no-store는 민감 응답이 브라우저나 중간 캐시에 저장되는 것을 줄인다. 모든 API에 동일 캐시 정책을 고정하기보다 공개 캐시 가능 응답과 민감 응답을 구분한다. 헤더만으로 접근 제어가 생기는 것은 아니다.

TrustedHostMiddleware는 예상 호스트를 제한한다. 하지만 신뢰하는 프록시가 원래 host와 scheme을 어떤 헤더로 전달하는지도 맞춰야 한다. 프록시 헤더를 모두 믿으면 공격자가 원래 IP와 scheme을 조작할 수 있다. FastAPI의 [프록시 뒤 배포 안내](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)를 참고해 실제 프록시 주소만 신뢰한다.

개념 실행 명령, 로컬 프록시가 127.0.0.1에 있을 때의 예시:

```powershell
python -m uvicorn upload_lab:app --proxy-headers --forwarded-allow-ips 127.0.0.1
```

컨테이너와 로드밸런서에서는 실제 주소와 네트워크가 다르므로 그대로 복사하지 않는다. 프록시에서 `/api`를 제거해 전달하면 `root_path`와 외부 URL 생성도 확인한다. 잘못된 scheme 신뢰는 HTTPS redirect 반복, OAuth callback URL 오류, 잘못된 Secure 쿠키 판단으로 이어질 수 있다.

## 실무 적용과 확인 문제

보안 리뷰는 데이터 흐름을 따라간다. 입력이 인증되었는가, 자원 권한을 확인했는가, 외부 요청 대상과 파일 경로를 제한했는가, 파싱 비용을 제한했는가, 출력 문맥에서 안전하게 렌더링되는가를 각 책임자와 연결한다. 정적 설정만 보지 말고 실제 잘못된 요청을 보내 차단 여부를 확인한다.

1. CORS 허용 목록이 API Key를 대신할 수 있는가? **해설:** 아니다. 브라우저 외 클라이언트는 CORS 정책과 무관하며 일부 브라우저 요청도 서버에서 먼저 실행될 수 있다.
2. UploadFile을 사용하면 파일 크기 방어가 자동 완성되는가? **해설:** 아니다. multipart 수신과 임시 저장은 엔드포인트의 내용 검사보다 앞설 수 있다. 프록시와 파서, 동시성 제한이 필요하다.
3. ORM이 있으면 모든 SQL Injection이 막히는가? **해설:** 바인드 값을 사용하면 안전한 경계를 만들 수 있지만 raw SQL 문자열 조립이나 임의 정렬 구조는 별도 방어가 필요하다.
4. 실습 과제: 빈 파일, 잘못된 UTF-8, 5MiB 초과, 경로형 파일명, 잘못된 API Key, 허용하지 않은 Origin을 테스트하라. **평가 기준:** 응답과 저장 파일을 함께 확인하고 CORS 차단을 서버 인증 실패와 혼동하지 않는다. 수신 단계 크기 제한이 없는 실습의 한계를 설명한다.

## 요약과 다음 장

API 보안은 TLS, 브라우저 정책, 인증, 권한, 입력 사용 위치, 자원 제한, 프록시 신뢰를 함께 다룬다. 파일명을 경로로 사용하지 않고 값과 SQL 구조를 분리하며 입력 검증을 넘어 실제 사용 경계를 보호한다. 다음 장은 외부 HTTP API를 호출할 때 연결 풀, timeout, 재시도, 장애 격리를 설계한다.

## 공식 참고자료

- [FastAPI — CORS](https://fastapi.tiangolo.com/tutorial/cors/): origin과 브라우저 교차 출처 정책.
- [FastAPI — Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/): 전달 헤더와 외부 주소 처리.
- [OWASP — File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): 파일명, 검사, 저장 및 크기 제한.
- [OWASP — CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): 쿠키 인증의 요청 위조 방어.
- [FastAPI — HTTPS](https://fastapi.tiangolo.com/deployment/https/): TLS 종료와 배포 구성.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 14장 예외 처리와 오류 응답](../14-errors/chapter.md) · [16장 HTTP 클라이언트와 외부 API 연동 →](../16-http-clients/chapter.md)
