---
title: "13장. 인증과 인가"
description: "비밀번호 검증, 세션, JWT의 신뢰 경계를 구분하고 FastAPI 의존성으로 현재 사용자를 확인한다. 역할 검사와 자원 소유권 검사를 분리하며, refresh token을 안전하게 갱신하려면 어떤 서버 상태가 필요한지 설계한다. 최소 실습은 단일 사용자로 로컬 로그인과 Bearer access toke"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 13
part: 4
---

## 학습 목표

비밀번호 검증, 세션, JWT의 신뢰 경계를 구분하고 FastAPI 의존성으로 현재 사용자를 확인한다. 역할 검사와 자원 소유권 검사를 분리하며, refresh token을 안전하게 갱신하려면 어떤 서버 상태가 필요한지 설계한다. 최소 실습은 단일 사용자로 로컬 로그인과 Bearer access token 검증을 구현한다.

Knowledge Hub 사용자는 로그인할 수 있어도 다른 사용자의 비공개 문서를 읽을 수 없어야 한다. 로그인 성공은 신원을 확인했다는 의미이고 특정 문서에 대한 읽기 권한은 별도 판단이다. URL의 숫자만 바꿔 다른 문서를 읽을 수 있다면 비밀번호 해시와 JWT 서명이 강해도 서비스는 안전하지 않다.

## 13.1 인증(Authentication)과 인가(Authorization)

인증은 “누구인가”를 판단하고 인가는 “이 작업을 해도 되는가”를 판단한다. 인증 결과는 내부 사용자 ID, 활성 상태, 인증 방식 같은 정보다. 인가에는 역할, 조직, 문서 소유권, 공유 정책, 요청한 행위가 들어간다. 둘을 한 번의 `is_admin` 검사로 뭉치지 않는다.

인증되지 않은 요청에는 일반적으로 401과 인증 방식 안내를 보낸다. 인증되었지만 허용되지 않은 요청은 403이 보통이다. 비공개 자원의 존재 자체를 숨기는 정책이라면 권한 없는 조회에 404를 사용할 수도 있다. 정책은 API 전체에서 일관되게 적용하고 내부 감사 로그에는 실제 원인을 구분한다.

신원은 사용자가 전송한 `user_id` 필드에서 얻지 않는다. 서버가 검증한 세션 또는 토큰에서 내부 ID를 얻고 실제 사용자 상태를 확인한다. 사용자가 본문에 `owner_id`를 넣더라도 허용된 작업인지 검사하거나 서버가 소유자를 지정한다. 입력 검증의 성공은 권한의 증명이 아니다.

## 13.2 비밀번호 해싱과 검증

비밀번호는 복호화해 비교할 수 있는 암호문으로 저장하기보다 비밀번호 전용 해시로 저장한다. 일반 SHA-256은 빠르다는 특성 때문에 비밀번호 추측 공격을 어렵게 만드는 용도에 적합하지 않다. Argon2 같은 알고리즘은 계산과 메모리 비용을 조절해 대량 추측 비용을 높인다.

좋은 라이브러리는 salt와 알고리즘 설정을 해시 문자열에 포함하고 검증 때 이를 읽는다. 같은 비밀번호도 다른 salt로 다른 해시가 나오는 것이 정상이다. 비교를 직접 구현하지 말고 검증 함수를 사용한다. 알고리즘이나 비용 정책을 바꾸면 로그인 때 검증 후 새 정책으로 재해시하는 절차를 마련할 수 있다.

해싱은 CPU와 메모리를 소비한다. `async def` 로그인에서 해시를 직접 계산하면 이벤트 루프가 지연될 수 있으므로 실습에서는 `asyncio.to_thread()`로 이동한다. 이것은 서버 전체의 무제한 로그인 공격을 해결하지 않는다. 로그인 rate limit, 동시 해시 수, 사용자 존재 여부를 드러내지 않는 오류, 최대 입력 길이를 함께 설계한다.

입력 길이 상한은 매우 긴 문자열의 비용을 제한하기 위한 것이다. 비밀번호를 조용히 잘라 검증하면 서로 다른 긴 비밀번호가 같은 것으로 취급될 수 있으므로 거절 정책을 명시한다. 로그, 추적, 오류 응답에 비밀번호를 남기지 않는다. 초기 비밀번호 역시 코드에 넣지 않고 환경변수로 받아 데모를 시작한다.

## 13.3 세션 기반 인증과 토큰 기반 인증

세션 방식은 예측 불가능한 식별자를 클라이언트에 주고 서버가 세션 상태를 찾는다. 서버에서 로그아웃과 권한 회수를 반영하기 쉬우며 세션 저장소가 필요하다. 브라우저 쿠키를 사용하면 `HttpOnly`, `Secure`, `SameSite`, 수명과 경로를 정하고 CSRF를 함께 검토한다.

토큰 방식은 요청에 자격 증명을 싣는다. JWT라면 서버가 서명과 claim을 검증해 일부 상태를 토큰에서 읽을 수 있다. 검증에 서버 저장소를 전혀 사용하지 않을 수도 있지만 사용자 비활성화와 즉시 권한 회수 요구가 있으면 저장소 조회나 폐기 목록이 필요해질 수 있다. “토큰은 무조건 무상태”라는 분류는 실제 보안 정책을 설명하기에 부족하다.

토큰은 저장 위치와 전송 방식도 중요하다. Authorization 헤더로 전송하면 브라우저가 자동으로 붙이는 쿠키와 동작이 다르다. 그러나 JavaScript가 읽는 저장소에 보관하면 XSS로 유출될 수 있다. 쿠키는 JavaScript 접근을 줄일 수 있지만 자동 전송 때문에 CSRF 정책이 필요하다. 어떤 선택도 단일 설정으로 모든 공격을 막지는 못한다.

## 13.4 JWT 구조와 검증 원리

JWT의 흔한 서명 형식은 header, payload, signature를 점으로 연결한 구조다. header와 payload의 인코딩은 암호화가 아니다. 비밀번호, 개인정보, 비밀키를 payload에 넣지 않는다. 서명은 내용이 신뢰하는 발급자에 의해 만들어졌고 변조되지 않았다는 판단에 사용한다.

검증기는 허용 알고리즘을 서버 설정으로 고정한다. 토큰이 보내 온 `alg`를 그대로 허용 목록으로 사용하면 안 된다. 만료 `exp`, 발급자 `iss`, 대상 `aud`, 주체 `sub`를 검증하고 필요한 claim이 빠졌을 때도 거절한다. `exp` 검증 기능을 켠 것과 `exp`가 반드시 존재하게 만드는 것은 구분해야 한다. PyJWT의 검증 옵션과 알고리즘 주의사항은 [공식 API 문서](https://pyjwt.readthedocs.io/en/stable/api.html)를 참고한다.

HS256은 발급과 검증이 같은 비밀키를 공유한다. 여러 서비스가 검증할 때 키를 받은 서비스도 토큰을 발급할 수 있다는 점을 고려한다. 비대칭 서명은 발급자의 개인키와 검증자의 공개키를 나눌 수 있지만 키 배포, rotation, `kid` 선택, JWKS 캐시 정책이 필요하다. 토큰의 `kid`를 파일 경로나 임의 URL로 바로 사용하지 않고 신뢰하는 키 집합 안에서만 찾는다.

## 13.5 Access Token과 Refresh Token

Access token은 API에 접근하는 짧은 자격 증명이고 refresh token은 새 access token을 얻는 자격 증명이다. 둘을 동일 검증 경로에서 받아들이면 refresh token을 API에 직접 사용할 수 있는 문제가 생긴다. 실습의 claim `token_use="access"`는 용도를 분리한다. 토큰의 대상과 발급자도 필요한 경우 분리한다.

짧은 access token은 유출 후 사용 가능한 시간을 줄인다. 하지만 짧게 정했다는 사실만으로 즉시 폐기가 되지는 않는다. 서버에서 만료 전 로그아웃을 강제하려면 사용자 토큰 버전, 세션 상태, 토큰 ID 폐기 목록 등 추가 상태가 필요하다. `jti`가 있다고 자동으로 폐기 목록이 생기는 것도 아니다.

Refresh token은 높은 엔트로피의 임의 값으로 만들고 DB에는 원문 대신 해시를 저장하는 방식이 가능하다. 이 값은 사람이 정한 비밀번호와 달리 충분히 무작위이므로 조회 가능한 해시 사용의 전제가 다르다. token family, 현재 토큰 상태, 사용 시각, 만료, 폐기 상태를 저장한다. 갱신 시 이전 토큰의 일회 사용과 다음 토큰 생성을 같은 DB 트랜잭션으로 묶는다.

최소 실습에는 refresh endpoint를 넣지 않는다. 인메모리 목록만으로 rotation을 구현하면 여러 워커의 동시 갱신과 서버 재시작을 처리하지 못한다. 아래 정책은 운영 설계의 기준이며 배포 가능한 완성 구현이라고 주장하지 않는다.

## 13.6 OAuth2와 OpenID Connect

OAuth2는 다른 애플리케이션에 접근 권한을 위임하는 프로토콜이다. 사용자 로그인의 신원 의미를 다루는 OpenID Connect는 OAuth2 위에 ID token과 관련 규칙을 더한다. Access token을 사용자 로그인 증거로 기계적으로 해석하거나 ID token을 일반 API access token으로 사용하는 것은 피한다.

브라우저·모바일에서 외부 신원 제공자를 사용한다면 Authorization Code와 PKCE 같은 흐름을 검토한다. redirect URI의 정확한 검증, state와 OIDC nonce, 코드의 일회 사용, 토큰 검증을 신뢰하는 라이브러리와 제공자 규칙에 맞춘다. HTTPS와 안전한 callback도 필요하다.

옛 자료에서 흔한 OAuth2 password grant는 현재 보안 권고의 대상이 아니다. [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700)은 Resource Owner Password Credentials grant 사용을 금지한다. 따라서 아래 `/login`은 자체 서비스의 로컬 JSON 로그인 실습이며 OAuth2 제공자 구현이라고 부르지 않는다. FastAPI의 OAuth2 도구는 보안 스키마와 토큰 추출을 돕는 도구이고 프로토콜 전체의 올바른 구현을 자동으로 보장하지 않는다.

## 13.7 Depends를 활용한 인증 구현: 실행 실습

새 디렉터리에 `auth_lab.py`를 저장한다. 데모 비밀번호와 JWT 키는 현재 PowerShell 세션에서 준비한다. 실제 운영 비밀을 실습에 사용하지 않는다. 키를 매번 새로 만들면 이전 토큰이 검증되지 않는 것이 정상이다.

```powershell
python -m pip install "fastapi>=0.121,<1" "uvicorn[standard]" "PyJWT>=2,<3" "pwdlib[argon2]>=0.2,<1"
$env:HUB_JWT_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:HUB_DEMO_PASSWORD = Read-Host "실습용 비밀번호를 입력하세요"
python -m uvicorn auth_lab:app --reload
```

이 `Read-Host` 예시는 실습 입력이며 운영 비밀 주입 방식은 아니다. 환경변수는 현재 프로세스와 자식 프로세스에 전달되며 코드 저장소에 기록하지 않는다.

완전 실행 예제, `auth_lab.py`:

```python
import asyncio
import os
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

ISSUER = "knowledge-hub-local"
AUDIENCE = "knowledge-hub-api"
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class User:
    id: str
    username: str
    hashed_password: str
    role: str
    active: bool = True

class Login(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def unauthorized() -> HTTPException:
    return HTTPException(
        401, "인증 정보를 확인하세요",
        headers={"WWW-Authenticate": "Bearer"},
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    secret = os.environ["HUB_JWT_SECRET"]
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT 키는 충분히 긴 무작위 값이어야 합니다")
    hashed = await asyncio.to_thread(
        password_hash.hash, os.environ["HUB_DEMO_PASSWORD"]
    )
    user = User("u1", "learner", hashed, "member")
    app.state.users = {user.id: user}
    app.state.jwt_secret = secret
    app.state.documents = {
        1: {"id": 1, "owner_id": "u1", "title": "내 비공개 문서"}
    }
    yield

app = FastAPI(title="Knowledge Hub Auth Lab", lifespan=lifespan)

@app.post("/login", response_model=TokenResponse)
async def login(body: Login, request: Request):
    user = request.app.state.users["u1"]
    valid = await asyncio.to_thread(
        password_hash.verify, body.password, user.hashed_password
    )
    if not valid or body.username != user.username or not user.active:
        raise unauthorized()
    now = datetime.now(timezone.utc)
    lifetime = timedelta(minutes=5)
    payload = {
        "sub": user.id, "iss": ISSUER, "aud": AUDIENCE,
        "iat": now, "nbf": now, "exp": now + lifetime,
        "jti": secrets.token_urlsafe(24), "token_use": "access",
    }
    token = jwt.encode(
        payload, request.app.state.jwt_secret, algorithm="HS256"
    )
    return TokenResponse(access_token=token, expires_in=300)

async def current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer)
    ],
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        payload = jwt.decode(
            credentials.credentials,
            request.app.state.jwt_secret,
            algorithms=["HS256"], audience=AUDIENCE, issuer=ISSUER,
            options={"require": [
                "exp", "iat", "nbf", "iss", "aud", "sub", "jti"
            ]},
        )
        if payload.get("token_use") != "access":
            raise jwt.InvalidTokenError("wrong token use")
        user = request.app.state.users.get(payload["sub"])
        if user is None or not user.active:
            raise jwt.InvalidTokenError("inactive user")
        return user
    except jwt.InvalidTokenError as error:
        raise unauthorized() from error

CurrentUser = Annotated[User, Depends(current_user)]

def require_roles(*roles: str):
    async def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(403, "이 작업의 권한이 없습니다")
        return user
    return check

@app.get("/me")
async def me(user: CurrentUser):
    return {"id": user.id, "username": user.username, "role": user.role}

@app.get("/admin")
async def admin(user: Annotated[User, Depends(require_roles("admin"))]):
    return {"message": "관리자 작업 허용", "user_id": user.id}

@app.get("/documents/{document_id}")
async def read_document(
    document_id: int, request: Request, user: CurrentUser
):
    document = request.app.state.documents.get(document_id)
    if document is None or document["owner_id"] != user.id:
        raise HTTPException(404, "문서가 없습니다")
    return {"id": document["id"], "title": document["title"]}
```

`POST /login`에 사용자 이름 `learner`와 설정한 비밀번호를 JSON으로 보내면 토큰이 반환된다. `/me` 호출에는 `Authorization: Bearer 받은_토큰`을 사용한다. `/me`는 200이고 `/admin`은 member 역할이므로 403이다. 토큰 없이 요청하거나 서명 부분을 변경하면 401이며 만료 후에도 401이어야 한다. `/docs`의 Authorize에 Bearer 토큰을 넣어 확인할 수도 있다.

예제는 사용자 저장소를 매 요청 확인하므로 활성 상태와 역할은 토큰의 오래된 역할 claim이 아니라 현재 서버 상태에서 가져온다. 데모는 한 명만 있으므로 모든 로그인에 같은 해시 검증을 수행한 뒤 사용자 이름을 비교한다. 실제 다중 사용자 저장소에서는 없는 사용자에 대해서도 준비한 dummy hash를 검증하여 사용자 존재 여부의 시간 차이를 줄이는 방식을 검토한다.

실습은 DB 사용자 관리, 가입, 비밀번호 재설정, refresh rotation, MFA, 로그인 제한까지 완성한 시스템이 아니다. 특히 환경변수로 초기 사용자 해시를 매 실행 다시 만드는 구조는 학습용이다. 실제 사용자 해시는 영속 저장하고 감사 이력과 재해시 정책을 설계한다.

## 13.8 RBAC 기반 권한 관리

RBAC는 역할에 작업 권한을 묶는 방식이다. `member`, `admin` 문자열을 모든 라우터에 직접 비교하면 역할 변경 비용이 커진다. “문서 삭제”, “조직 관리” 같은 권한을 정의하고 역할과 연결하면 검사가 업무 행위에 가까워진다. 작은 서비스에서는 역할 검사부터 시작하되 정책이 늘어나는 방향을 고려한다.

역할 검사가 객체 수준 권한을 대신하지 않는다. member가 문서를 읽을 수 있다는 사실과 그 문서가 해당 사용자의 것이라는 사실은 모두 필요하다. 쿼리에서 `owner_id == current_user.id` 조건을 붙여 허용 범위 밖의 행을 가져오지 않는 방식도 유용하다. 관리자 예외가 있으면 그 예외의 이유와 감사 기록을 남긴다.

다중 조직 서비스에서는 사용자 역할이 조직마다 다를 수 있다. 글로벌 role 하나만 토큰에 넣으면 다른 조직에서도 권한이 잘못 적용될 수 있다. 조직 ID, 멤버십, 자원 소속을 함께 확인한다. 검색과 RAG의 검색 결과 필터에도 같은 정책을 적용해야 한다. 생성된 답변에서만 숨기는 방식은 이미 검색 단계에서 읽은 비공개 근거를 보호하지 못한다.

## 13.9 토큰 탈취와 갱신 토큰 보안

토큰은 소지한 사람이 사용할 수 있는 자격 증명인 경우가 많다. TLS, 안전한 저장, 로그 마스킹, 짧은 수명, scope 제한으로 유출 가능성과 피해 범위를 줄인다. 헤더를 그대로 access log에 기록하거나 오류 수집 도구에 요청 전체를 보내면 토큰이 다른 시스템에 복제될 수 있다.

Refresh rotation은 이전 토큰을 사용 완료로 표시하고 새 토큰을 발급한다. 이전 토큰이 재사용되면 탈취나 정상 클라이언트의 중복 요청을 판단할 정책이 필요하다. 무조건 같은 새 토큰을 여러 요청에 반환하는 것은 보안 의미가 달라진다. 가족 전체 폐기, 제한된 재시도 창, 클라이언트의 갱신 요청 직렬화 등을 요구에 맞게 정한다.

서버 구현에서는 조회 후 사용 표시를 별개 단계로 처리하면 두 요청이 같은 refresh token을 함께 성공시킬 수 있다. 조건부 UPDATE 또는 행 락으로 `미사용 상태이면 사용 표시`와 다음 토큰 저장을 같은 트랜잭션에서 처리한다. 갱신 응답이 유실된 경우의 재로그인 경험도 고려한다. 상태 없는 access token의 편리함 때문에 refresh token의 상태 관리를 생략해서는 안 된다.

로그아웃, 비밀번호 변경, 계정 비활성화의 효과를 명시한다. 예를 들어 모든 refresh family를 폐기하고 access token은 최대 5분 남는 정책을 선택할 수 있다. 이것은 예시 정책이며 즉시 차단이 필요한 서비스에는 부족할 수 있다. 토큰 회수 요구와 DB 조회 비용을 함께 평가한다.

## 확인 문제와 해설

1. JWT payload는 암호화되어 있는가? **해설:** 흔한 서명 JWT의 payload는 읽을 수 있다. 서명은 무결성과 발급자 확인에 사용한다.
2. `verify_exp=True`만으로 만료 claim 누락을 막을 수 있는가? **해설:** 라이브러리의 검증과 필수 claim 옵션을 함께 확인해야 한다. 실습은 `require`에 exp를 포함한다.
3. admin 역할이 있으면 모든 조직 문서를 읽어도 되는가? **해설:** 서비스 정책에 따라 다르다. 역할의 적용 범위, 조직 멤버십, 자원 소속을 함께 정의한다.
4. 실습 과제: 만료 토큰, 잘못된 audience, token_use가 refresh인 토큰을 직접 발급해 `/me`를 호출하라. **평가 기준:** 모두 401이고 원문 토큰이나 세부 검증 오류가 응답에 노출되지 않는다. 정상 member는 200이며 admin 경로는 403이다.
5. 설계 과제: refresh token 동시 갱신 두 건을 시간 순서로 그려라. **평가 기준:** 한 번만 소비되는 DB 원자 연산과 재사용 감지 후 정책을 설명한다.

## 요약과 다음 장

인증 결과를 신뢰하려면 해시, 토큰 서명, claim, 현재 사용자 상태를 함께 확인한다. 인가는 역할과 자원 소유권을 분리하고 refresh token은 별도 수명과 서버 상태로 관리한다. 다음 장은 인증 실패를 포함한 오류를 일관된 응답과 안전한 로그로 표현한다.

## 공식 참고자료

- [FastAPI — JWT and Password Hashing](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/): 보안 의존성과 해시 도구의 사용 형태.
- [PyJWT — API Reference](https://pyjwt.readthedocs.io/en/stable/api.html): 허용 알고리즘과 claim 검증 옵션.
- [RFC 9700 — OAuth 2.0 Security](https://datatracker.ietf.org/doc/html/rfc9700): OAuth 보안 권고와 refresh token 보호.
- [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html): 신원 프로토콜과 ID token의 의미.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 12장 Redis와 캐싱 전략](../12-redis-cache/chapter.md) · [14장 예외 처리와 오류 응답 →](../14-errors/chapter.md)
