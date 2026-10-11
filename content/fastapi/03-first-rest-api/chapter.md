---
title: "03장. 첫 번째 REST API 개발"
description: "문서를 만들고 조회하고 수정하고 삭제하는 API를 구현한다. 경로·쿼리·헤더·본문의 차이와 HTTP 메서드의 의미를 설명하고, 응답 코드와 OpenAPI 계약을 실제 요청으로 확인한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 3
part: 1
---

> PART 1. FastAPI 시작하기

## 학습 목표와 도입 사례

문서를 만들고 조회하고 수정하고 삭제하는 API를 구현한다. 경로·쿼리·헤더·본문의 차이와 HTTP 메서드의 의미를 설명하고, 응답 코드와 OpenAPI 계약을 실제 요청으로 확인한다.

클라이언트 팀이 문서 수정 API를 요청했다고 생각해 보자. 서버는 `POST /edit` 하나로 모든 일을 처리할 수도 있다. 하지만 문서의 식별 방법, 부분 수정인지 전체 교체인지, 없는 문서를 어떻게 처리하는지 모호해진다. 좋은 API는 호출자가 코드를 읽지 않아도 이 규칙을 이해하게 만든다.

## 3.1 FastAPI 애플리케이션 생성

애플리케이션 객체는 라우트와 미들웨어, 오류 처리 규칙을 모으는 구성 단위다. import할 때 객체를 만들고 경로를 등록한 뒤 ASGI 서버가 이를 호출한다. `title`과 `version`은 문서 메타데이터다. `version="0.1.0"`을 적는다고 URL 버전 관리나 배포 버전 추적이 자동으로 만들어지지는 않는다.

작은 실습은 단일 파일로 시작한다. 파일을 먼저 나누는 것보다 요청 계약을 결정하는 것이 우선이다. 여러 도메인이 생기면 9장에서 `APIRouter`와 계층 구조로 분리한다. 이 장의 메모리 저장소는 HTTP 규칙을 관찰하기 위한 장치다.

## 3.2 데코레이터와 라우팅 원리

`@app.get("/documents/{document_id}")`는 경로 패턴과 메서드에 함수를 등록한다. 같은 경로여도 `GET`과 `DELETE`는 다른 동작이다. 요청이 들어오면 경로를 매칭하고 입력값을 준비해 함수를 호출한다. 등록 순서가 중요한 패턴도 있다. `/documents/recent` 같은 정적 경로는 `/documents/{document_id}` 같은 넓은 경로보다 먼저 등록하는 편이 명확하다.

경로에 `document_id`라는 이름을 적고 함수에 동일한 매개변수를 선언하면 그 값이 경로 입력이 된다. 함수 매개변수 이름을 바꾸면 계약도 함께 검토해야 한다. 경로가 맞지만 HTTP 메서드가 지원되지 않으면 일반적으로 `405 Method Not Allowed`다. 문서가 없는 `404`와 다른 실패다.

## 3.3 GET, POST, PUT, PATCH, DELETE

`GET`은 읽기다. 조회 횟수를 통계로 기록하는 내부 부수효과는 있을 수 있지만, 클라이언트가 요청한 리소스 상태를 변경하는 기능으로 설계하지 않는다. 링크 미리보기나 재시도만으로 삭제가 일어나게 `GET /delete`를 만들면 위험하다.

`POST`는 서버가 새 리소스를 만들거나 특정 처리를 수행하는 데 사용한다. 이 장에서는 서버가 새 ID를 발급한다. 같은 요청을 반복하면 새 문서가 반복 생성되므로 기본적으로 멱등성이 없다. 실제 생성 API에는 중복 요청 키를 도입할 수 있다.

`PUT`은 지정된 리소스의 표현을 교체하는 의미로 설계한다. 필수 필드가 빠졌는데 기존 값을 슬쩍 유지하면 호출자가 전체 교체와 부분 수정을 구분하기 어렵다. 이 실습은 기존 문서만 교체하고 없는 문서는 `404`를 반환한다. PUT으로 생성까지 지원할지는 API 계약에서 별도로 정한다.

`PATCH`는 부분 변경이다. 모든 PATCH가 자동으로 멱등인 것은 아니다. `title`을 지정값으로 바꾸는 연산과 숫자를 1 증가시키는 연산은 반복 효과가 다르다. `DELETE`는 삭제 상태를 만든다. 두 번째 삭제를 `404`로 응답해도 서버의 최종 상태가 계속 삭제라는 점에서 멱등성의 의미와 모순되지 않는다.

HTTP 메서드의 표준 의미는 [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)에 정의되어 있다. 실무에서는 표준 의미와 도메인의 재시도 조건을 함께 문서화한다.

## 3.4 Path Parameter와 Query Parameter

경로는 리소스 식별에, 쿼리는 검색·필터·정렬·페이지 조건에 적합하다. `/documents/42`는 문서 하나를, `/documents?q=async&limit=10`은 조건을 만족하는 목록을 표현한다. 매개변수 위치만 바꾸는 것이 아니라 호출 의도가 달라진다.

`Query(ge=1, le=100)`처럼 범위를 선언하면 지나치게 큰 페이지를 요청 경계에서 거절할 수 있다. 기본값은 서버와 클라이언트 사이의 계약이다. 목록 반환량을 무제한으로 두면 데이터 증가 후 직렬화·네트워크·메모리 비용이 동시에 커진다.

이 장은 `offset` 페이지를 사용한다. 학습과 관리용 목록에는 이해하기 쉽지만, 데이터가 자주 추가되거나 큰 offset을 사용하면 결과 중복과 비용 문제가 생길 수 있다. 정렬 키와 커서를 이용한 페이지는 10장의 SQL 설계와 연결해서 검토한다.

## 3.5 Request Body와 Header 처리

본문 모델은 생성·수정할 데이터의 구조를 표현한다. 헤더는 인증 토큰, 조건부 요청, 추적 식별자와 같은 메타데이터에 적합하다. 쿼리나 경로에 비밀을 넣으면 URL 로그와 브라우저 기록에 남을 수 있으므로 인증 정보를 넣는 장소로 사용하지 않는다.

FastAPI에서 `Header()`를 사용하면 헤더를 입력으로 선언할 수 있다. Python 매개변수의 밑줄과 HTTP 헤더의 하이픈 변환 규칙도 존재한다. 이 장은 `alias="X-Client-Name"`으로 이름을 명확히 지정한다. 헤더 문자열을 받았다고 그 값의 신뢰성이 생기는 것은 아니다. 사용자나 권한의 근거로 쓰려면 인증 검증이 필요하다.

## 3.6 HTTP 상태 코드와 응답 반환

상태 코드는 성공·실패의 종류를 프로그램이 구분할 수 있게 한다. 생성 성공은 `201`, 조회 성공은 `200`, 본문 없는 삭제 성공은 `204`로 설계한다. 없는 문서는 `404`, 검증 실패는 기본적으로 `422`다. 모든 응답을 `200`으로 감싸고 JSON에만 실패 표시를 넣으면 프록시·모니터링·클라이언트의 표준 기능을 활용하기 어려워진다.

`204`에는 본문이 없어야 한다. `{"message":"deleted"}`를 함께 보내고 싶은 경우에는 `200` 등 다른 계약을 정한다. 응답 모델의 역할은 다음 장에서 깊게 다룬다. 이 장도 출력 구조를 명시해 실수로 내부 필드를 반환하지 않도록 한다.

## 3.7 Swagger UI와 OpenAPI 자동 생성

OpenAPI는 엔드포인트와 데이터 구조를 기계가 읽을 수 있게 표현한 명세다. Swagger UI는 그 명세를 보여주고 요청을 실험하는 화면이다. 화면 이름과 명세 형식을 같은 것으로 생각하지 않는다. 자동 생성한 명세를 검토하면 필드의 required 여부와 nullable 여부를 빠르게 확인할 수 있다.

문서 화면에서 성공 요청만 누르면 계약을 충분히 검증한 것이 아니다. 빈 제목, 잘못된 ID, 너무 큰 limit, 명시적인 null을 넣는다. 인증이 추가되면 문서 화면의 토큰 입력과 실제 서버의 검증도 연결해야 한다. API 설명문에는 동작의 의미와 제한을 적고, 서버 내부 클래스 이름을 노출할 필요는 없다.

## 기본 실습: 메모리 문서 API

**완전 실행 예제.** 별도 폴더에서 FastAPI·Uvicorn·Pydantic을 설치한 뒤 아래 전체 코드를 `main.py`로 저장한다. 저장소는 단일 프로세스의 메모리이며 서버를 다시 시작하면 사라진다.

```python
from itertools import count
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI(title="Knowledge Hub — 문서 API")
ids = count(1)
documents: dict[int, dict] = {}

class DocumentWrite(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20_000)

class DocumentPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=20_000)

class DocumentRead(DocumentWrite):
    id: int

def require_document(document_id: int) -> dict:
    document = documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document_not_found")
    return document

@app.post("/documents", response_model=DocumentRead, status_code=201)
async def create_document(
    data: DocumentWrite,
    response: Response,
    client_name: Annotated[str | None, Header(alias="X-Client-Name")] = None,
):
    document_id = next(ids)
    document = {"id": document_id, **data.model_dump()}
    documents[document_id] = document
    response.headers["Location"] = f"/documents/{document_id}"
    # client_name은 메타데이터이며 사용자 인증 정보가 아니다.
    return document

@app.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    q: Annotated[str | None, Query(max_length=100)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    selected = sorted(documents.values(), key=lambda value: value["id"])
    if q is not None:
        selected = [value for value in selected if q.casefold() in value["title"].casefold()]
    return selected[offset:offset + limit]

@app.get("/documents/{document_id}", response_model=DocumentRead)
async def read_document(document_id: int):
    return require_document(document_id)

@app.put("/documents/{document_id}", response_model=DocumentRead)
async def replace_document(document_id: int, data: DocumentWrite):
    require_document(document_id)
    document = {"id": document_id, **data.model_dump()}
    documents[document_id] = document
    return document

@app.patch("/documents/{document_id}", response_model=DocumentRead)
async def patch_document(document_id: int, data: DocumentPatch):
    document = require_document(document_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="empty_patch")
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="null_not_allowed")
    document.update(changes)
    return document

@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int):
    require_document(document_id)
    del documents[document_id]
    return Response(status_code=204)
```

`python -m uvicorn main:app --reload`로 실행한다. PowerShell에서 다음 요청을 차례대로 보낸다.

```powershell
$bookBody = @{ title = '비동기 입문'; content = 'await의 의미를 배우자' } | ConvertTo-Json
Invoke-RestMethod 'http://127.0.0.1:8000/documents' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($bookBody))
Invoke-RestMethod 'http://127.0.0.1:8000/documents?limit=10'
$bookPatch = @{ title = '이벤트 루프 입문' } | ConvertTo-Json
Invoke-RestMethod 'http://127.0.0.1:8000/documents/1' -Method Patch -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($bookPatch))
```

생성 결과의 ID가 1인지 먼저 확인하고 그 ID로 조회한다. 부분 수정 후 `content`는 유지되고 `title`만 바뀐다. PUT에 title만 넣으면 content 누락으로 실패한다. PATCH의 `{}`는 이 API가 정한 `400`, `{"title":null}`은 `422`다. Swagger UI에서도 응답 상태와 `Location`을 확인할 수 있다.

## 내부 흐름과 실무 적용

```text
POST /documents
  → Content-Type/본문 읽기
  → DocumentWrite 검증
  → create_document 실행
  → 내부 저장소 갱신
  → DocumentRead 계약에 맞춰 출력
  → 201 + Location + JSON
```

실무에서는 저장소 갱신을 DB 트랜잭션으로 바꾸고, 인증된 사용자 ID를 문서의 소유자로 기록한다. 목록 API는 사용자가 볼 수 있는 문서만 조회해야 한다. 응답 모델에서 소유자 필드를 숨기는 것만으로 조회 권한이 생기는 것은 아니다.

동시 수정에서는 마지막 쓰기가 이전 쓰기를 덮어쓸 수 있다. 클라이언트가 읽은 버전을 함께 보내는 낙관적 잠금이나 `ETag`·`If-Match`를 검토한다. 본문 검증에 성공했어도 변경 시점에 데이터가 바뀌었으면 충돌 응답이 필요할 수 있다.

## 성능 및 주의사항

이 실습의 async 함수는 실질적인 I/O 대기가 없다. 작은 메모리 조작을 보여주기 위한 선택이며, 모든 CRUD를 async로 써야 한다는 규칙이 아니다. 전역 dict는 워커 간에 공유되지 않는다. 파일 저장이나 DB 작업을 추가할 때는 동기·비동기 드라이버에 맞춰 실행 위치를 바꿔야 한다.

목록 전체를 정렬하고 문자열 검색하는 코드는 데이터 수에 비례해 CPU와 메모리를 사용한다. 실제 서비스에서 인덱스가 있는 DB 조회와 페이지 제한으로 대체한다. Pydantic 길이 검증도 네트워크 수신 단계의 전체 요청 크기 제한을 대신하지 않는다.

## 확인 문제와 해설

1. PUT과 PATCH에서 content가 누락되었을 때 이 API의 결과는 어떻게 다른가?
2. DELETE 두 번째 호출의 `404`가 멱등성을 깨는가?
3. `X-Client-Name`을 사용자 ID처럼 믿으면 어떤 문제가 생기는가?
4. 실습: `limit=101`, `/documents/abc`, PATCH의 null을 보내고 실패 종류를 설명하라.

**해설.** 1번은 PUT 전체 입력이 검증 실패하고 PATCH는 해당 필드를 유지한다. 2번은 아니다. 멱등성은 최종 서버 상태에 관한 의미이며 매번 같은 상태 코드를 요구하지 않는다. 3번은 호출자가 값을 위조해 다른 사용자인 척할 수 있다. 4번은 쿼리 범위 오류, 경로 정수 변환 오류, API의 null 금지 규칙으로 구분한다. 오류의 위치와 의도한 계약을 함께 기록한다.

## 요약과 다음 장

HTTP 입력의 위치와 메서드는 호출 의도를 표현한다. 상태 코드와 스키마를 함께 확인해야 API 계약이 완성된다. 다음 장에서는 이 계약을 표현하는 Pydantic 모델과 출력 경계를 깊게 살펴본다.

## 공식 참고자료

- [FastAPI 경로 매개변수](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI 쿼리 검증](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
- [FastAPI 본문 갱신](https://fastapi.tiangolo.com/tutorial/body-updates/)
- [FastAPI 상태 코드](https://fastapi.tiangolo.com/tutorial/response-status-code/)
- [HTTP Semantics — RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 02장 개발 환경 구성](../02-development-environment/chapter.md) · [04장 Pydantic과 데이터 검증 →](../04-pydantic-validation/chapter.md)
