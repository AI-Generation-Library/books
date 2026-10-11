---
title: "04장. Pydantic과 데이터 검증"
description: "입력 자료형과 실제 검증의 관계를 이해하고, 누락과 null을 구분하고, 요청·내부 데이터·응답 모델을 분리한다. 직렬화 결과를 예측하고 응답 필터링의 보안 한계를 설명한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 4
part: 1
---

> PART 1. FastAPI 시작하기

## 학습 목표와 도입 사례

입력 자료형과 실제 검증의 관계를 이해하고, 누락과 null을 구분하고, 요청·내부 데이터·응답 모델을 분리한다. 직렬화 결과를 예측하고 응답 필터링의 보안 한계를 설명한다.

문서 생성 API에서 클라이언트가 `owner_id`를 자유롭게 보내고 서버가 그대로 저장했다고 생각해 보자. 자료형이 정수라는 이유만으로 안전하지 않다. 입력 계약에는 사용자에게 결정권이 있는 필드만 넣어야 한다. 검증은 “맞는 모양”의 문제이고 권한은 “누가 결정할 수 있는가”의 문제다.

## 4.1 Python 타입 힌트 이해하기

`title: str`은 변수나 매개변수에 대한 타입 정보다. 일반 Python 함수에 숫자를 넘겼다고 타입 힌트만으로 항상 실행이 중단되는 것은 아니다. 정적 검사 도구와 IDE는 이 정보를 분석하고, Pydantic은 모델 경계에서 실제 입력을 검사한다.

`list[str]`은 문자열 목록, `str | None`은 문자열 또는 None, `Annotated[int, ...]`는 정수 타입에 추가 메타데이터가 있음을 표현한다. Java의 런타임 객체 타입과 TypeScript의 컴파일 검사 경험을 그대로 대입하지 말자. Python에서 어떤 도구가 타입 정보를 소비하는지 구분해야 한다.

타입 표기는 읽는 사람을 위한 문서이기도 하다. `dict`보다 구체적인 모델을 사용하면 필수 필드, 길이 제한, 중첩 구조를 확인할 수 있다. 반대로 아무 구조나 받는 `dict[str, object]`를 남용하면 계약을 호출자와 구현자 모두 추측하게 된다.

## 4.2 Pydantic BaseModel의 구조

`BaseModel`을 상속하고 필드를 선언하면 모델이 입력을 받아 검증·변환한 객체를 만든다. 핵심 질문은 원본 입력이 정확히 어떤 타입이었는지보다, 검증 결과가 계약을 만족하는지다. 기본 모드에서는 일부 변환이 허용된다. 숫자처럼 보이는 문자열이 정수로 바뀔 수 있다.

의도하지 않은 변환을 거절해야 한다면 필드의 strict 옵션이나 strict 타입을 사용한다. strict를 무조건 켜는 것도 정답은 아니다. URL의 경로·쿼리는 텍스트에서 시작하므로 경계 위치와 API 사용성을 함께 판단한다. [Pydantic 모델 문서](https://docs.pydantic.dev/latest/concepts/models/)는 검증 결과와 데이터 변환을 구분한다.

모델은 데이터 저장소가 아니다. 모델 생성 후 DB에 저장되는 것은 아니고, 모델 인스턴스를 바꾸어도 기본 설정에서는 모든 할당이 다시 검증되는 것은 아니다. 중요한 변경에는 새 모델 검증이나 `validate_assignment` 설정을 검토한다.

## 4.3 Field를 이용한 데이터 검증

`Field(min_length=1, max_length=120)`은 문자열 길이를, `Field(ge=0, le=100)`은 숫자 범위를 나타낸다. 제약을 구체적으로 적으면 검증 실패와 JSON Schema 설명이 일치하기 쉽다. 다만 공백 하나도 길이가 1이므로 제목 정규화가 필요할 수 있다.

순서에도 의미가 있다. 앞뒤 공백을 제거한 뒤 길이를 검증하려면 before validator로 정규화한다. 이미 길이 검증이 끝난 뒤 공백을 제거하면 빈 문자열이 만들어지는 경로가 생길 수 있다. 검증 함수는 입력을 파괴적으로 바꾸기보다 새 값을 반환하는 편이 예측하기 쉽다.

기본값을 사용할 때도 정책이 필요하다. `Field(default_factory=list)`는 각 모델 인스턴스마다 새 목록을 만든다는 의도를 분명히 표현한다. 기본값의 검증이 필요한 경우 `validate_default`를 검토한다. 기본값이 있다고 모든 설정에서 동일하게 검증된다고 추측하지 않는다.

## 4.4 Optional, Union, Enum과 중첩 모델

Pydantic 2에서 `str | None`과 기본값 None은 다른 정보다. 다음 표의 세 줄을 기억하자.

| 선언 | 누락 가능 | 명시적 null 가능 |
|---|---|---|
| `name: str` | 아니오 | 아니오 |
| `name: str \| None` | 아니오 | 예 |
| `name: str \| None = None` | 예 | 예 |

`Optional[str]`도 `str | None`과 같은 nullable 표기이지 그 자체로 누락 허용 선언은 아니다. PATCH에는 누락과 null의 의미를 따로 정한다. “누락은 유지, null은 지우기”일 수 있고, 3장처럼 null을 금지할 수도 있다. `exclude_unset=True`와 `model_fields_set`이 이 구분을 돕는다.

Enum은 허용한 상태 이름을 계약으로 만든다. 문서 공개 상태를 `private`와 `public`으로 제한하면 오타를 경계에서 잡는다. 중첩 모델은 문서 메타데이터처럼 내부 구조가 있는 데이터를 표현한다. Union으로 서로 다른 이벤트를 표현할 때는 `Literal` 타입의 구별 필드를 가진 discriminated union을 검토하면 해석이 명확해진다.

## 4.5 field_validator와 model_validator

필드 검증은 제목의 공백 제거처럼 한 값의 규칙에, 모델 검증은 시작일과 종료일의 순서처럼 필드 사이 관계에 적합하다. 검증 실패에는 적절한 `ValueError` 등을 발생시키고, 정상일 때는 검증된 값이나 모델을 반환한다.

validator 안에서 DB나 외부 API를 호출하는 설계는 피한다. 모델 구성 작업이 숨은 I/O와 권한 검증을 갖게 되면 테스트와 성능 예측이 어려워진다. 문서의 존재 확인·소유권·중복 저장 여부는 서비스와 트랜잭션 경계에서 처리한다. 스키마 검증과 상태 의존 규칙을 분리하면 오류도 더 정확히 표현할 수 있다.

## 4.6 요청 DTO와 응답 DTO 분리

DTO는 경계를 넘기는 데이터 구조다. 생성 입력에는 제목·내용이 있고, 출력에는 서버가 정한 ID·생성 시각이 있을 수 있다. DB 모델에는 소유자·삭제 표시·내부 인덱싱 상태까지 들어간다. 한 모델을 모든 곳에서 공유하면 출력에 숨겨야 할 필드가 입력에서 수정 가능한 필드가 되기 쉽다.

계층별 모델 분리는 중복처럼 보여도 서로 다른 변경 이유를 표현한다. DB 컬럼을 추가해도 외부 API가 자동으로 바뀌지 않아야 한다. 응답 모델을 설계한 뒤 명시적으로 변환하는 것은 이런 독립성을 유지하는 방법이다.

## 4.7 직렬화와 역직렬화

역직렬화는 JSON이나 사전 형태 입력을 모델로 바꾸는 과정이고, 직렬화는 모델을 전송 가능한 표현으로 바꾸는 과정이다. `model_validate`는 Python 객체, `model_validate_json`은 JSON 입력을 받는 데 사용할 수 있다. 출력에서는 `model_dump`와 `model_dump_json`을 구별한다.

`model_dump()`의 기본 Python 모드는 datetime 같은 Python 값을 유지할 수 있다. `model_dump(mode="json")`은 JSON 호환 값으로 바꾸고, `model_dump_json()`은 JSON 문자열을 반환한다. JSON 문자열을 일반 응답 값으로 다시 반환하면 이중 인코딩이 생길 수 있다. 프레임워크에 모델을 반환할지, 직접 Response를 만들지 계약에 맞춰 선택한다.

타임존을 없애서 시각 비교 문제를 감추지 않는다. 운영 API는 timezone-aware 시각과 직렬화 규칙을 정한다. 이 장은 UTC aware 시각을 사용한다. 금액처럼 정확한 십진 표현이 필요한 데이터에는 부동소수점의 한계와 문자열·Decimal 직렬화 계약도 검토한다.

## 4.8 응답 모델과 데이터 필터링

응답 모델은 외부에 내보낼 구조를 지정한다. 일반적인 반환 처리에서 모델에 없는 내부 필드를 제외할 수 있다. 그러나 잘못 반환한 필수 필드나 잘못된 타입은 서버의 출력 계약 오류다. 이를 클라이언트 입력 오류와 혼동하지 않는다.

직접 `JSONResponse` 등 Response 객체를 반환하는 경로는 일반 응답 모델 필터링을 동일하게 기대하면 안 된다. 민감정보 제거를 한 가지 기능에만 의존하지 말고, 필요한 데이터만 조회하고 명시적인 DTO를 만들고 로그도 점검한다. FastAPI의 출력 계약은 [응답 모델 문서](https://fastapi.tiangolo.com/tutorial/response-model/)를 기준으로 확인한다.

## 기본 실습 A: 검증 순서와 nullable 관찰

**완전 실행 예제.** Pydantic 2 환경에서 `models_lab.py`로 저장하고 `python models_lab.py`로 실행한다.

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic import field_validator, model_validator

class Visibility(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"

class Metadata(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=10)

class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=120)
    visibility: Visibility = Visibility.PRIVATE
    metadata: Metadata = Field(default_factory=Metadata)
    starts_at: datetime
    ends_at: datetime | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_period(self) -> Self:
        if self.starts_at.utcoffset() is None:
            raise ValueError("starts_at requires a timezone")
        if self.ends_at is not None:
            if self.ends_at.utcoffset() is None:
                raise ValueError("ends_at requires a timezone")
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be later than starts_at")
        return self

class NullableRequired(BaseModel):
    subtitle: str | None

created = DocumentCreate(
    title="  첫 문서  ",
    starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
)
assert created.title == "첫 문서"
print(created.model_dump(mode="json"))
assert NullableRequired(subtitle=None).subtitle is None

for payload in ({}, {"subtitle": 3}):
    try:
        NullableRequired.model_validate(payload)
    except ValidationError as error:
        print(error.errors()[0]["type"])

try:
    DocumentCreate(title="   ", starts_at=created.starts_at)
except ValidationError as error:
    print(error.errors()[0]["type"])
```

정규화된 제목과 JSON 호환 시각이 출력된다. subtitle 누락, 잘못된 문자열 타입, 공백 제목이 각각 실패한다. 구체적인 오류 메시지 문구는 버전에 따라 달라질 수 있으므로 테스트는 오류 종류와 위치, 허용·거절 결과를 중심으로 설계한다.

## 기본 실습 B: 출력 경계 확인

**별도의 완전 실행 예제.** `main.py`를 다음으로 만들고 Uvicorn으로 실행한다.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class DocumentPublic(BaseModel):
    id: int
    title: str

@app.get("/documents/1", response_model=DocumentPublic)
async def document():
    internal = {"id": 1, "title": "응답 경계", "private_note": "외부 반환 금지"}
    return internal
```

`/documents/1`은 id와 title만 반환한다. `/openapi.json`에서도 private_note가 계약에 들어 있지 않은지 확인한다. 이 예제는 출력 필터의 관찰용이다. 실무에서는 공개 DTO를 직접 구성하고 사용자별 조회 권한을 먼저 검사한다.

## 실무 적용과 성능·함정

ORM 객체를 출력 모델로 변환하려면 `ConfigDict(from_attributes=True)`를 사용할 수 있다. 이때 속성을 읽는 순간 lazy loading이 일어나지 않도록 조회를 준비해야 한다. async DB 세션과 지연 로딩 문제는 11장에서 다룬다. 응답 직렬화가 숨은 DB 쿼리의 시작점이 되면 지연과 세션 수명이 뒤엉킨다.

검증 비용을 줄이려고 `model_construct`로 모든 입력 검사를 우회하지 않는다. 외부 입력에서는 먼저 정확성이 필요하다. 큰 목록의 중복 모델 변환이 실제 병목인지 측정한 뒤 출력 크기, 모델 생성 위치, 페이지 구성을 개선한다. 검증이 빠르더라도 큰 JSON의 메모리 비용은 남는다.

`extra="forbid"`는 정의하지 않은 입력 필드를 거절해 오타를 찾기 좋다. 하지만 API 변경 시 클라이언트의 추가 필드를 무시하던 기존 계약과 호환 문제가 생길 수 있다. 모델 정책은 외부 계약의 일부로 문서화한다. 비밀을 `SecretStr`로 감추는 기능도 적절한 출력 설계와 로그 정책을 대신하지 않는다.

## 확인 문제와 해설

1. `name: str | None`에서 `{}`와 `{"name":null}`은 왜 결과가 다른가?
2. 제목의 공백 제거를 before validator로 수행한 이유는?
3. `response_model`을 썼는데 직접 Response에 민감정보를 넣어 반환하면 안전한가?
4. 실습: 종료 시각이 시작보다 이른 입력, timezone 없는 입력, 정의하지 않은 owner_id를 넣어 실패를 확인하라.

**해설.** 1번은 기본값 없는 필드는 필수이고 타입만 nullable이기 때문이다. 2번은 정규화 후 길이 검증이 이루어지도록 하기 위해서다. 3번은 아니다. 직접 Response 반환 경로의 처리와 데이터 구성을 점검해야 한다. 4번은 모델 관계 규칙, timezone 규칙, extra 금지를 각각 검증한다. 실패 위치를 함께 기록하면 스키마 규칙과 모델 전체 규칙을 구분할 수 있다.

## 요약과 다음 장

Pydantic은 입력과 출력의 데이터 계약을 표현한다. 누락·null·변환을 명확히 정하고, 권한과 DB 규칙을 분리하고, 직렬화 경로를 점검해야 한다. 다음 장부터는 이런 계약을 실행하는 ASGI와 서버 구조를 살펴본다.

## 공식 참고자료

- [Pydantic 모델](https://docs.pydantic.dev/latest/concepts/models/)
- [Pydantic 필드](https://docs.pydantic.dev/latest/concepts/fields/)
- [Pydantic 검증 함수](https://docs.pydantic.dev/latest/concepts/validators/)
- [Pydantic 직렬화](https://docs.pydantic.dev/latest/concepts/serialization/)
- [FastAPI 응답 모델](https://fastapi.tiangolo.com/tutorial/response-model/)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 03장 첫 번째 REST API 개발](../03-first-rest-api/chapter.md) · [05장 ASGI와 Uvicorn의 내부 구조 →](../05-asgi-uvicorn/chapter.md)
