---
title: "09장. FastAPI 프로젝트 아키텍처"
description: "이 장을 마치면 HTTP 처리와 업무 규칙을 분리하고, 새 기능을 어느 모듈에 넣어야 하는지 설명할 수 있다. APIRouter로 주소를 묶는 방법에 그치지 않고 설정, 객체 생성, 저장소 교체의 책임을 정한다. 실습은 Knowledge Hub의 문서 등록 기능을 메모리 저장소로 구현한다. 앞 장의 코드"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 9
part: 3
---

## 학습 목표

이 장을 마치면 HTTP 처리와 업무 규칙을 분리하고, 새 기능을 어느 모듈에 넣어야 하는지 설명할 수 있다. `APIRouter`로 주소를 묶는 방법에 그치지 않고 설정, 객체 생성, 저장소 교체의 책임을 정한다. 실습은 Knowledge Hub의 문서 등록 기능을 메모리 저장소로 구현한다. 앞 장의 코드를 계속 덧붙이는 방식이 아닌, 새 디렉터리에서 실행하는 독립 예제다.

첫 구현에서는 `main.py` 하나에 로그인, 문서 등록, 검색을 모두 넣어도 된다. 문제는 문서 이름의 규칙을 바꿀 때 생긴다. 등록 API에서는 금지한 제목이 관리자 일괄 등록에서는 허용되고, 테스트는 HTTP 서버를 거쳐야만 규칙을 검증한다. 폴더가 적다는 것보다 같은 규칙이 여러 곳에서 서로 다르게 구현되는 것이 더 큰 비용이다. 아키텍처는 이 변경 비용을 줄이는 방법이다.

## 9.1 단일 파일 구조의 한계

단일 파일은 작은 실험에 적합하다. 전체 요청 흐름이 눈에 보이고 파일 간 이동도 없다. 기능 수보다 중요한 분리 신호는 변화의 이유다. HTTP 상태 코드는 API 계약 때문에 바뀌고, 제목 규칙은 업무 요구 때문에 바뀌며, SQL은 저장 방식 때문에 바뀐다. 서로 다른 이유로 변하는 코드가 한 함수에 섞이면 하나를 고칠 때 나머지도 함께 이해해야 한다.

다음 문장으로 함수를 설명해 보자. “요청을 읽고, 사용자를 확인하고, SQL을 만들고, 제목을 검사하고, 응답을 만든다.” 접속사마다 독립적인 책임이 숨어 있다. 반대로 파일을 쪼개도 모든 함수가 `Request`와 전역 DB를 받으면 결합은 그대로다. 분리의 효과는 파일 개수보다 함수의 입력과 출력에서 드러난다.

Knowledge Hub의 첫 분리 기준은 문서, 사용자, 검색이라는 기능 영역이다. 문서 등록과 수정이 같은 업무 규칙을 사용하도록 문서 영역 안에 서비스를 둔다. 모든 영역에 복잡한 추상 계층을 강제하기보다, 반복되는 규칙과 교체 가능한 외부 의존성을 찾아 경계를 만든다.

## 9.2 APIRouter를 이용한 API 분리

`APIRouter`는 관련 경로, 태그, 의존성을 모으는 도구다. `include_router()`를 호출하면 그 라우트들이 애플리케이션에 등록된다. 별도 프로세스나 독립 서버가 만들어지는 것은 아니다. `/api/v1` 같은 공통 접두사는 조립 지점에서 붙이고 `/documents`는 기능 라우터에 두면 경로 버전과 기능 이름의 책임을 나눌 수 있다. 라우터 결합의 기본 동작은 [FastAPI의 다중 파일 안내](https://fastapi.tiangolo.com/tutorial/bigger-applications/)에서 확인할 수 있다.

태그는 OpenAPI 문서의 그룹 이름이며 권한 경계가 아니다. `dependencies=[Depends(...)]`는 검사 결과를 라우트 매개변수로 전달하지 않는다. 현재 사용자 객체가 필요하면 매개변수에 의존성을 선언한다. 동일 경로와 메서드를 여러 곳에 등록하거나, 동적 경로 `/{document_id}`보다 뒤에 `/search`를 넣어 경로를 가로채는 문제도 분리 이후 확인해야 한다. 폴더 분리가 라우트 충돌을 자동으로 막아 주지는 않는다.

## 9.3 Router, Service, Repository 계층

라우터는 요청 DTO를 읽고 서비스에 전달한 뒤 응답 DTO와 상태 코드를 만든다. 서비스는 “문서 제목은 공백만으로 구성될 수 없다” 같은 규칙과 업무 순서를 실행한다. 저장소는 필요한 데이터를 읽고 쓰는 방법을 담당한다. 서비스에서 저장소를 호출하는 방향은 자연스럽지만 저장소에서 라우터를 불러서는 안 된다.

| 책임 | 예시 | 피해야 할 결합 |
|---|---|---|
| Router | 빈 제목 오류를 422 응답으로 변환 | SQL 문자열 작성 |
| Service | 제목 정규화, 중복 정책 결정 | `HTTPException` 직접 생성 |
| Repository | 문서 저장, ID 조회 | HTTP 쿠키 해석 |

서비스가 `HTTPException`을 던지면 CLI 가져오기나 큐 작업에서도 HTTP 의미가 따라온다. 대신 도메인 예외를 던지고 라우터나 전역 핸들러에서 번역한다. 저장소를 지나치게 일반화한 `save_anything()`도 좋지 않다. 문서 서비스가 실제로 필요로 하는 `add(title)`와 `get(id)` 같은 작고 명확한 계약이 테스트와 구현을 단순하게 한다.

트랜잭션 책임은 계층 이름만으로 결정되지 않는다. “문서와 감사 로그를 함께 저장한다”는 업무 단위를 서비스가 정하고, 실제 세션의 시작과 종료는 별도 작업 단위 객체가 맡을 수 있다. 각 저장소가 마음대로 commit하면 서비스에서 두 저장을 원자적으로 묶기 어렵다. 11장에서 이 원칙을 실제 비동기 세션에 적용한다.

## 9.4 Domain 중심 프로젝트 구조

문서 기능을 수정하는 개발자가 `routers`, `schemas`, `services`, `repositories` 폴더 네 곳을 돌아다니는 구조도 가능하다. 하지만 영역이 많아지면 관련 파일을 함께 찾기 어렵다. 다음 구조는 문서 영역 안에서 기능의 전체 흐름을 읽을 수 있도록 한다. 이것은 최종 정답이 아니라 이 실습의 변경 패턴에 맞춘 선택이다.

```text
architecture_lab/
  app/
    __init__.py
    config.py
    main.py
    documents/
      __init__.py
      domain.py
      repository.py
      service.py
      router.py
```

공통 모듈에는 정말 여러 영역이 공유하는 설정과 인프라만 둔다. 이름을 정하기 어렵다는 이유로 `utils.py`에 함수를 계속 넣으면 의존 방향이 흐려진다. 사용자와 문서가 서로 필요하면 상대 영역의 ORM 모델을 직접 가져오기보다 사용자 ID, 권한 검사 계약처럼 작은 값과 기능으로 연결한다. 도메인 중심 구조는 반드시 마이크로서비스로 분리하라는 의미도 아니다. 하나의 배포 단위 안에서 업무 경계를 선명하게 하는 데 먼저 사용한다.

## 9.5 비즈니스 로직과 HTTP 계층 분리: 실행 실습

빈 `__init__.py` 두 개를 만들고 다음 파일을 저장한다. 이 예제는 Python 3.12 이상, FastAPI 0.121 이상 1 미만, Pydantic 2를 기준으로 작성했다. 메모리 저장은 프로세스가 종료되면 사라진다. 다중 워커에서 저장 내용도 공유되지 않는다. 데이터 영속성과 분산 정합성을 위한 구현으로 사용하지 않는다.

설치와 실행 명령이다. PowerShell에서 프로젝트 루트 `architecture_lab`을 현재 디렉터리로 사용한다.

```powershell
python -m pip install "fastapi>=0.121,<1" "uvicorn[standard]" "pydantic-settings>=2,<3"
python -m uvicorn app.main:app --reload
```

완전 실행 예제, `app/documents/domain.py`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Document:
    id: int
    title: str

class InvalidTitle(Exception):
    pass

class DocumentNotFound(Exception):
    pass
```

완전 실행 예제, `app/documents/repository.py`:

```python
from threading import RLock
from typing import Protocol
from .domain import Document

class DocumentRepository(Protocol):
    def add(self, title: str) -> Document: ...
    def get(self, document_id: int) -> Document | None: ...

class MemoryDocumentRepository:
    def __init__(self) -> None:
        self._rows: dict[int, Document] = {}
        self._next_id = 1
        self._lock = RLock()

    def add(self, title: str) -> Document:
        with self._lock:
            document = Document(self._next_id, title)
            self._rows[document.id] = document
            self._next_id += 1
            return document

    def get(self, document_id: int) -> Document | None:
        with self._lock:
            return self._rows.get(document_id)
```

완전 실행 예제, `app/documents/service.py`:

```python
from .domain import Document, DocumentNotFound, InvalidTitle
from .repository import DocumentRepository

class DocumentService:
    def __init__(self, repo: DocumentRepository, title_limit: int):
        self.repo = repo
        self.title_limit = title_limit

    def create(self, title: str) -> Document:
        normalized = title.strip()
        if not normalized or len(normalized) > self.title_limit:
            raise InvalidTitle("문서 제목의 길이가 올바르지 않습니다")
        return self.repo.add(normalized)

    def read(self, document_id: int) -> Document:
        document = self.repo.get(document_id)
        if document is None:
            raise DocumentNotFound()
        return document
```

완전 실행 예제, `app/documents/router.py`:

```python
from collections.abc import Callable
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .domain import DocumentNotFound, InvalidTitle
from .service import DocumentService

class CreateDocument(BaseModel):
    title: str = Field(min_length=1, max_length=200)

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str

def make_router(get_service: Callable[[], DocumentService]) -> APIRouter:
    router = APIRouter(prefix="/documents", tags=["documents"])
    Service = Annotated[DocumentService, Depends(get_service)]

    @router.post("", response_model=DocumentResponse, status_code=201)
    def create_document(body: CreateDocument, service: Service):
        try:
            return service.create(body.title)
        except InvalidTitle as error:
            raise HTTPException(422, str(error)) from error

    @router.get("/{document_id}", response_model=DocumentResponse)
    def read_document(document_id: int, service: Service):
        try:
            return service.read(document_id)
        except DocumentNotFound as error:
            raise HTTPException(404, "문서가 없습니다") from error

    return router
```

이 예제는 지역 타입 별칭을 라우트 정의 시 실제 객체로 평가하기 위해 `from __future__ import annotations`를 쓰지 않는다. 미래 주석을 도입할 때는 지역 별칭의 이름 해석을 검토하거나 의존성 별칭을 모듈 수준에 두어야 한다. 구조 변경이 런타임의 타입 분석에도 영향을 준다는 작은 사례다.

완전 실행 예제, `app/config.py`:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUB_", extra="ignore")
    app_name: str = "Knowledge Hub"
    title_limit: int = Field(default=120, ge=1, le=200)
```

완전 실행 예제, `app/main.py`:

```python
from fastapi import FastAPI
from .config import Settings
from .documents.repository import MemoryDocumentRepository
from .documents.router import make_router
from .documents.service import DocumentService

def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings if settings is not None else Settings()
    repo = MemoryDocumentRepository()
    service = DocumentService(repo, config.title_limit)
    app = FastAPI(title=config.app_name)
    app.include_router(make_router(lambda: service), prefix="/api/v1")
    return app

app = create_app()
```

`POST /api/v1/documents`에 `{"title":"  첫 문서  "}`를 보내면 201과 `{"id":1,"title":"첫 문서"}`를 받는다. 해당 ID 조회는 200, 존재하지 않는 ID는 404다. 공백만 보낸 요청은 DTO 길이 검증을 통과할 수 있지만 서비스의 정규화 규칙이 막는다. 전송 형태의 검증과 업무 규칙은 중복이 아니라 서로 다른 경계를 보호한다.

실행 순서는 라우트 입력 검증, 의존성 호출, 서비스 규칙, 저장소 잠금 구간, 응답 모델 변환이다. `def` 라우트는 FastAPI가 스레드 풀에서 실행하지만 그 안의 일반 서비스 호출은 같은 스레드에서 직접 실행된다. 불변 Document를 반환하므로 저장소 내부 객체를 응답 과정에서 수정할 수 없다. `RLock`은 이 프로세스의 ID 증가를 보호하며 여러 프로세스의 동시 변경을 해결하지는 않는다.

## 9.6 설정 관리와 환경변수

설정은 코드에 분산된 상수를 모으는 것부터 시작하지만 입력 검증도 중요하다. `HUB_TITLE_LIMIT=0`은 서버 시작 단계에서 실패해야 한다. 요청마다 오류가 나거나 조용히 잘못된 정책이 적용되는 것보다 실패 시점이 명확하다. 환경변수 입력과 모델 검증 방식은 [Pydantic Settings 문서](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)를 참고한다.

PowerShell에서 `$env:HUB_TITLE_LIMIT = "80"`을 설정하고 서버를 새로 시작하면 허용 길이가 달라진다. 실행 중 환경변수 값을 바꾼다고 이미 만들어진 Settings가 자동으로 바뀌지는 않는다. 설정 갱신이 필요하면 갱신 절차와 기존 연결 객체의 교체 방식을 함께 설계한다.

개발용 `.env`를 사용한다면 저장소에는 실제 비밀값 대신 필요한 변수 이름을 적은 `.env.example`을 둔다. DB 비밀번호와 JWT 키는 필수값으로 받고 운영에서 기본값을 두지 않는다. 설정 전체를 로그에 출력하는 것도 피한다. `SecretStr`의 마스킹은 표시 실수를 줄이는 기능이지 안전한 비밀 저장소나 메모리 암호화가 아니다.

## 9.7 순환 참조와 의존성 관리

위 실습에서 `main`은 모든 객체를 조립하지만 다른 모듈은 `main`을 가져오지 않는다. 라우터는 서비스와 도메인만 알고 서비스는 저장소 계약을 안다. 객체를 얻겠다고 `from app.main import app`을 여러 파일에서 사용하면 모듈 초기화가 끝나기 전에 상대 이름을 읽는 순환 참조가 발생하기 쉽다.

순환 참조를 발견했을 때 import를 함수 안으로 옮기면 당장의 오류는 줄어들 수 있다. 하지만 업무 경계가 양방향인 문제까지 해결된 것은 아니다. 공유할 작은 자료형을 별도 모듈로 옮기거나, 한 영역이 다른 영역의 작업을 직접 실행하는 대신 계약을 주입한다. `TYPE_CHECKING`은 타입 확인용 import를 런타임에서 피할 때 유용하지만 FastAPI가 런타임에 해석해야 하는 의존성 타입을 무작정 그 안에 숨기면 안 된다.

의존성의 수명도 구분한다. 설정과 엔진은 일반적으로 프로세스 수명, 세션은 요청 또는 업무 단위 수명이다. 위 서비스는 상태를 변경하지 않고 저장소만 참조하므로 공유할 수 있다. 요청별 현재 사용자나 DB 세션을 서비스 인스턴스의 필드에 계속 덮어쓰는 설계로 바꾸면 공유 인스턴스가 위험해진다. 객체가 무엇을 담는지 먼저 보고 수명을 정한다.

## 9.8 Clean Architecture 적용 시 고려사항

Clean Architecture의 유용한 질문은 “이 업무 규칙을 FastAPI 없이 실행할 수 있는가”다. 서비스를 콘솔에서 호출해 제목 규칙을 확인할 수 있다면 HTTP에 대한 결합이 낮다. 다른 질문은 “저장 방식을 바꾸면 어떤 파일이 변하는가”다. MemoryDocumentRepository 대신 SQL 저장소를 조립하는 변경이 서비스와 라우터 전체를 흔들지 않으면 경계가 제 역할을 한다.

모든 자료형을 세 번 복사하고 모든 함수에 인터페이스를 만드는 것은 비용이 있다. 세 줄짜리 단순 조회는 라우터와 SQL 조회 함수만으로 충분할 수 있다. 반면 결제, 권한 변경, 문서 접근 정책처럼 규칙과 부작용이 많은 기능은 별도 서비스가 가치 있다. 객체 변환 비용, 테스트 수, 팀의 탐색 비용을 포함해 판단한다.

실무 리뷰에서는 다음 변경을 상상한다. REST API 외에 큐로 문서를 가져온다. 저장소를 PostgreSQL로 바꾼다. 제목 규칙을 팀별로 바꾼다. 각 변경을 위해 고칠 곳을 표시하면 설계의 효과를 평가할 수 있다. “계층이 네 개라서 좋다”보다 변경의 영향이 한정되는 이유를 설명하는 것이 중요하다.

## 성능과 실패 사례

계층을 나눈다고 요청이 자동으로 느려지는 것은 아니다. 보통 함수 호출 비용보다 DB 왕복과 네트워크 대기가 더 크다. 그러나 저장소 메서드 하나를 부를 때마다 세션을 만들고 commit하는 설계는 불필요한 왕복을 만든다. 계층 경계와 자원 경계를 같게 취급하지 않는다.

공유 메모리 저장소는 데모에서 빠르지만 워커가 두 개면 문서를 만든 요청과 조회 요청이 서로 다른 저장소에 도달할 수 있다. 이런 404는 라우팅 오류가 아니라 상태 배치 오류다. 캐시 역시 각 프로세스 메모리로 시작했다면 같은 제한을 가진다. 폴더 구조를 설계할 때 데이터가 실제로 어디에 살아 있는지도 문서화한다.

## 확인 문제와 해설

1. 서비스에서 `HTTPException`을 없애면 무엇이 좋아지는가? **해설:** 동일 규칙을 큐, CLI, 테스트에서 재사용하고 각 진입점이 자기 오류 계약으로 번역할 수 있다. 단순히 import 수가 줄어드는 문제가 아니다.
2. 저장소를 Protocol로 정의하면 구현이 자동으로 안전해지는가? **해설:** 아니다. 타입 검사는 메서드 모양을 돕지만 잠금, 원자성, 영속성은 구현과 테스트의 책임이다.
3. `main.py`를 라우터에서 import하지 않도록 객체를 전달하는 위치는 어디인가? **해설:** `create_app()` 같은 조립 지점이다. 이 지점은 구체 저장소와 설정을 알 수 있다.
4. 실습 과제: `DocumentService`를 FastAPI 없이 호출하여 공백 제목을 거절하고 정상 제목을 정규화하는지 확인하라. **평가 기준:** HTTP 타입을 import하지 않으며, 예외의 종류와 저장소 변경 여부를 검사한다. 운영 전환 과제로 메모리 저장의 다중 워커 한계를 글로 설명한다.

## 요약과 다음 장

프로젝트 구조는 업무 규칙, HTTP 계약, 저장 방식의 변화 이유를 나누기 위한 도구다. 조립 지점에서 구체 객체를 만들고, 요청별 자원을 공유 상태에 섞지 않는다. 다음 장은 메모리 저장소를 관계형 DB의 객체 매핑으로 확장하며 ORM이 어떤 SQL을 실행하는지 관찰한다.

## 공식 참고자료

- [FastAPI — Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/): 라우터 등록과 기능별 파일 분리.
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): 환경변수 로딩과 설정 검증.
- [FastAPI — Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/): 호출 가능한 객체와 의존성 선언.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 08장 의존성 주입과 미들웨어](../08-dependencies-middleware/chapter.md) · [10장 SQLAlchemy와 ORM →](../10-sqlalchemy-orm/chapter.md)
