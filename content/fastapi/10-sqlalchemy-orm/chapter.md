---
title: "10장. SQLAlchemy와 ORM"
description: "이 장에서는 ORM 객체와 DB 행의 관계, Engine과 Session의 책임, 관계 로딩이 발생시키는 쿼리를 설명한다. SQLAlchemy 2.x의 select()와 Mapped를 사용해 Knowledge Hub의 사용자와 문서를 저장한다. 최소 실습은 외부 DB 없이 SQLite에서 실행한다. HT"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 10
part: 3
---

## 학습 목표

이 장에서는 ORM 객체와 DB 행의 관계, Engine과 Session의 책임, 관계 로딩이 발생시키는 쿼리를 설명한다. SQLAlchemy 2.x의 `select()`와 `Mapped`를 사용해 Knowledge Hub의 사용자와 문서를 저장한다. 최소 실습은 외부 DB 없이 SQLite에서 실행한다. HTTP와 비동기 실행을 잠시 분리해 저장 계층의 동작 자체를 관찰한다.

문서 목록 API는 개발 DB에서 빨랐지만 사용자가 늘자 지연이 길어졌다고 하자. 서버 코드에는 `for document in documents: print(document.owner.name)` 한 줄만 있다. 이 줄이 문서 수만큼 SELECT를 실행한다면 코드의 길이와 DB 비용은 일치하지 않는다. ORM을 잘 사용하려면 객체 접근이 언제 SQL 실행으로 이어지는지 알아야 한다.

## 10.1 ORM의 개념과 동작 원리

관계형 DB는 표와 행으로 데이터를 저장하고 애플리케이션은 객체를 사용한다. ORM은 매핑 정보를 바탕으로 행을 객체로 만들고 객체의 변경을 INSERT, UPDATE, DELETE로 변환한다. SQL을 없애는 기술이 아니라 SQL 생성과 객체 상태 관리의 일부를 맡기는 기술이다.

문서 객체의 `title`을 바꿨다고 즉시 UPDATE가 전송되는 것은 아니다. Session이 변경을 기록하고 flush 시점에 반영한다. 같은 Session에서 같은 기본 키를 읽으면 identity map을 통해 같은 객체가 반환될 수 있다. 하지만 임의의 목록 조회 결과 전체를 재사용하는 범용 캐시는 아니다. 쿼리를 실행해야 조건에 맞는 행을 찾고, 행을 읽은 뒤 이미 존재하는 객체와 연결한다. Session의 기본 역할은 [SQLAlchemy Session 문서](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)에서 확인할 수 있다.

영속성 상태는 크게 transient, pending, persistent, detached로 볼 수 있다. 새 객체는 아직 세션과 무관하고, `add()` 뒤에는 삽입 대기 상태, flush 뒤에는 DB 행과 연결된 상태가 된다. 세션을 닫으면 객체가 분리된다. 모든 속성이 이미 로딩되었다면 값 자체는 읽을 수 있지만 아직 가져오지 않은 관계를 읽으면 새 SQL을 수행할 세션이 없어 실패할 수 있다.

## 10.2 SQLAlchemy 2.x 아키텍처

SQLAlchemy에는 SQL 표현식과 연결을 다루는 Core, 객체 매핑과 상태를 다루는 ORM이 있다. Core의 `select`, `insert`, `update`는 ORM에서도 사용한다. 2.x 스타일은 SELECT 문을 만들고 `session.execute()` 또는 `session.scalars()`로 실행하는 방식이다. 예전 자료의 `session.query()`와 새로운 예제를 섞기보다 한 스타일을 유지하면 결과 형태를 이해하기 쉽다.

SQL 표현식은 데이터베이스 방언에 따라 SQL로 컴파일되고 DBAPI 드라이버에 전달된다. PostgreSQL과 SQLite가 동일한 Python 표현을 받아도 자료형, 반환 기능, 락, 트랜잭션 동작까지 같아지는 것은 아니다. “ORM을 썼으므로 DB를 언제든 바꿀 수 있다”는 기대는 과하다. 이식성을 원한다면 DB별 기능 사용을 표시하고 대상 DB에서 통합 테스트한다.

ORM이 유리한 곳은 관계가 있는 업무 객체와 여러 단계의 변경을 다룰 때다. 대규모 일괄 적재나 집계 쿼리는 Core 또는 명시적 SQL이 더 읽기 쉬울 수 있다. 동일 프로젝트 안에서 혼용할 수 있으며 어떤 경로가 어떤 트랜잭션 안에서 실행되는지 명확히 하면 된다.

## 10.3 Engine, Connection, Session

Engine은 DB URL, 드라이버, 방언, 연결 풀의 진입점이다. 생성한다고 모든 연결이 즉시 열리는 것은 아니며 보통 필요할 때 연결을 얻는다. Connection은 DB와의 실제 대화 통로를 나타내고 트랜잭션을 실행한다. Session은 ORM 상태와 업무 변경을 관리하면서 필요할 때 Engine에서 연결을 빌린다.

따라서 Engine은 일반적으로 프로세스에서 재사용하고 Session은 짧은 업무 단위마다 만든다. 전역 Session 하나를 모든 요청에서 쓰면 서로 다른 요청의 변경과 트랜잭션이 뒤섞인다. Connection이나 Session을 요청 종료 후 캐시에 넣어 재사용해서도 안 된다. ORM 객체를 응답 캐시에 넣으면 객체의 상태와 세션 수명까지 따라가므로, 캐시에는 직렬화한 응답 값이나 DTO를 넣는다.

세션의 `close()`는 사용할 자원을 반환하는 정리 작업이다. 변경을 저장하려면 commit이 필요하다. `with Session(...)`만으로 성공한 변경이 자동 commit되는 것은 아니다. `with session.begin()`은 정상 종료 시 commit, 예외가 빠져나가면 rollback이라는 경계를 제공한다. 중첩 블록의 의미를 정확히 읽어야 “코드가 끝났는데 데이터가 없다”는 혼란을 줄일 수 있다.

## 10.4 Declarative Model 정의

`DeclarativeBase`를 상속한 Base에 매핑 클래스를 연결하고 `Mapped[T]`와 `mapped_column()`으로 컬럼을 선언한다. 모델은 DB의 행 구조이며 Pydantic 요청 모델과는 책임이 다르다. 사용자 입력 모델에 ORM의 비밀번호 해시나 내부 상태 필드를 그대로 노출하지 않는다.

외래 키는 DB의 참조 무결성을 위한 제약이고 `relationship()`은 Python 객체 사이의 탐색 방식이다. 관계만 선언하고 외래 키를 생략하면 원하는 DB 제약이 생기지 않는다. 반대로 외래 키가 있어도 ORM 탐색을 위해 관계 설정이 필요할 수 있다. 고유 제약 역시 입력 검증과 별도로 DB에 두어야 동시 삽입을 막는다.

`nullable`, 인덱스, 길이는 데이터의 의미에 따라 결정한다. 모든 컬럼에 인덱스를 두면 쓰기 비용과 저장 공간이 늘어난다. 문서 검색 조건이 `owner_id`라면 해당 인덱스는 이유가 있지만, 사용하지 않는 임의 문자열 인덱스는 필요성을 증명해야 한다. SQLite는 선언된 문자열 길이를 PostgreSQL과 같은 방식으로 강제하지 않을 수 있으므로 실습 성공을 운영 제약의 검증으로 간주하지 않는다.

## 10.5 CRUD 구현: 완전 실행 실습

새 디렉터리에 `orm_lab.py`를 만들고 다음 명령을 실행한다. 이 예제는 메모리 SQLite를 사용하므로 실행할 때마다 빈 DB로 시작한다. 스키마를 만드는 `create_all()`은 실험용 초기화이며 운영 스키마 변경 도구는 아니다.

```powershell
python -m pip install "sqlalchemy>=2.0,<3"
python orm_lab.py
```

완전 실행 예제, `orm_lab.py`:

```python
from __future__ import annotations
from sqlalchemy import ForeignKey, String, create_engine, event, select
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, mapped_column,
    relationship, selectinload,
)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    documents: Mapped[list[Document]] = relationship(
        back_populates="owner", lazy="raise"
    )

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    owner: Mapped[User] = relationship(
        back_populates="documents", lazy="raise"
    )

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def main() -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        user = User(name="learner")
        user.documents = [
            Document(title="비동기 입문"),
            Document(title="ORM 입문"),
        ]
        session.add(user)
        session.flush()
        document_id = user.documents[0].id

    with Session(engine) as session:
        statement = select(Document).options(
            selectinload(Document.owner)
        ).order_by(Document.id)
        documents = session.scalars(statement).all()
        print([(d.title, d.owner.name) for d in documents])

    with Session(engine) as session, session.begin():
        document = session.get(Document, document_id)
        assert document is not None
        document.title = "비동기 데이터베이스"

    with Session(engine) as session, session.begin():
        document = session.get(Document, document_id)
        assert document is not None
        session.delete(document)

    with Session(engine) as session:
        remaining = session.scalars(select(Document)).all()
        assert [d.title for d in remaining] == ["ORM 입문"]
        print("CRUD 검증 완료")
    engine.dispose()

if __name__ == "__main__":
    main()
```

기대 결과는 사용자와 두 문서의 INSERT, 문서 목록과 소유자 조회, 한 문서의 UPDATE와 DELETE다. 마지막 출력은 `CRUD 검증 완료`다. `echo=True`는 SQL 관찰용이며 실제 운영에서는 파라미터가 개인정보를 포함할 수 있어 무분별하게 사용하지 않는다.

읽기에서는 `session.get()`이 기본 키 한 개를 조회하고 `scalars(select(...))`는 행에서 첫 번째 값인 모델 객체를 꺼낸다. `execute(select(Document.title, User.name))`처럼 여러 컬럼을 선택하면 Row 결과를 다룬다. `scalars()`를 사용하면 첫 컬럼만 남으므로 결과의 형태를 고려해야 한다.

수정은 읽은 persistent 객체의 속성을 바꾼 후 commit 경계를 통과한다. 삭제는 `session.delete()`로 예약하고 flush 또는 commit 때 SQL이 나간다. 대량 수정은 객체를 전부 로딩하는 대신 `update()` 문으로 실행할 수 있으나 identity map의 기존 객체와 DB 값의 동기화 정책을 확인해야 한다. 실행 방식의 선택은 SQL 횟수와 메모리 사용에 영향을 준다.

## 10.6 관계 매핑과 JOIN

`select(Document).join(Document.owner).where(User.name == "learner")`는 사용자 이름으로 문서를 필터링하는 JOIN이다. JOIN을 썼다는 이유만으로 `document.owner`가 모두 로딩되는 것은 아니다. 쿼리의 행 선택과 관계 속성의 로딩은 별개다. 필요한 경우 로딩 옵션을 추가하거나 `contains_eager()`로 명시적 JOIN 결과를 관계에 연결한다.

개념 예제, 앞 실습의 모델과 세션을 사용하는 조회문:

```python
statement = (
    select(Document)
    .join(Document.owner)
    .where(User.name == "learner")
    .options(selectinload(Document.owner))
)
```

다대다 관계는 연결 테이블이 필요하고, 연결 자체에 역할이나 생성 시각이 있으면 연결을 별도 모델로 만드는 편이 좋다. 예를 들어 문서 공유의 `viewer`, `editor`는 단순 사용자 목록이 아니라 업무 정보다. 관계를 편하게 순회하려는 이유만으로 공유 권한의 의미를 숨기지 않는다.

삭제 전파도 설계 대상이다. 사용자를 삭제할 때 문서를 모두 삭제할지, 소유자를 변경할지, 삭제를 금지할지 업무 규칙을 정한 다음 ORM cascade와 DB `ON DELETE`를 맞춘다. 두 설정은 작동 위치가 다르다. 실습에서는 문서 하나만 삭제해 사용자 삭제 정책을 암묵적으로 정하지 않았다.

## 10.7 Lazy Loading과 Eager Loading

Lazy loading은 관계 속성이 실제로 필요해질 때 조회한다. 쓰지 않는 데이터를 가져오지 않는 장점이 있지만, 직렬화 단계에서 뜻밖의 SQL이 발생할 수 있다. Eager loading은 쿼리 시점에 필요한 관계를 가져온다. `selectinload()`는 부모 키를 모아 추가 조회하고 `joinedload()`는 JOIN 결과에서 관계를 채운다. 구체적인 로딩 방식은 [SQLAlchemy 관계 로딩 문서](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)에 정의되어 있다.

선택 기준은 관계의 크기와 결과 행 수다. 한 문서의 작은 소유자 정보를 JOIN으로 가져오는 것은 자연스럽다. 사용자마다 수천 개 문서가 있고 댓글까지 JOIN하면 결과 행이 크게 늘어 같은 사용자 데이터가 반복될 수 있다. SQL이 한 번이라고 비용도 작다고 판단해서는 안 된다.

컬렉션 `joinedload()`는 결과에 부모 행이 중복되므로 `session.scalars(statement).unique().all()`처럼 중복 제거가 필요하다. `selectinload()`는 대개 목록 응답에 다루기 쉽지만 키 수가 크면 나뉜 추가 조회가 일어날 수 있다. “항상 정확히 두 쿼리”라는 단정도 피한다. 실습의 작은 소유자 목록에서는 예상하기 쉬운 수의 SELECT가 나타난다.

실습의 `lazy="raise"`는 관계를 미리 가져오지 않았다면 접근을 실패시킨다. 이것은 개발자가 응답에 필요한 관계를 의식적으로 결정하도록 돕는다. 비동기 ORM에서는 일반 속성 접근으로 숨은 I/O가 생기는 것이 특히 문제여서 다음 장에서도 이런 명시성을 유지한다.

## 10.8 N+1 쿼리 문제

N+1은 목록 조회 한 번 뒤 각 행의 관계를 개별 조회하는 패턴이다. 문서 100개라면 최대 101번이라는 형태가 흔하지만 실제 횟수는 identity map에 이미 들어 있는 소유자 수, 관계 방향, 조회 옵션에 따라 달라진다. 같은 사용자 소유의 문서가 많으면 추가 조회가 줄 수 있으므로 작은 테스트 데이터가 문제를 숨길 수 있다.

탐지하려면 응답 결과만 보지 말고 SQL 개수와 시간을 측정한다. 여러 소유자를 만들고 문서 수를 늘려도 쿼리 수가 일정 범위에 머무르는지 확인한다. 쿼리 하나가 빠르더라도 네트워크 왕복이 반복되면 전체 지연이 커진다. 반대로 모든 관계를 거대한 JOIN으로 해결하면 행 폭과 중복 때문에 더 느려질 수 있다.

목록 API는 필요한 필드만 선택하는 방식도 검토한다. `select(Document.id, Document.title, User.name).join(Document.owner)`는 ORM 관계 객체를 전부 만들 필요가 없는 읽기 모델이다. 페이지 크기 상한과 안정적인 정렬 키를 정해 반환 개수도 제한한다. ORM 로딩 최적화만으로 무제한 목록의 메모리 문제를 해결할 수는 없다.

## 10.9 SQLAlchemy와 JPA 비교

JPA는 Java의 영속성 표준이며 Hibernate는 대표 구현이다. SQLAlchemy는 Python 라이브러리이면서 Core와 ORM을 함께 제공한다. JPA의 EntityManager와 영속성 컨텍스트에 익숙하면 Session과 identity map을 연결해 이해할 수 있다. 하지만 프레임워크가 트랜잭션을 자동으로 설정한다고 가정하면 안 된다. FastAPI 자체에는 Spring의 `@Transactional`과 같은 DB 트랜잭션 경계를 내장한 기능이 없다.

두 계열 모두 변경 추적, 관계 매핑, 지연 로딩 때문에 실제 SQL을 관찰해야 한다. Python의 자료형 선언과 동적 런타임 특성은 Java의 엔티티 설계 관례와 다르고, 세션 만료와 로딩 옵션의 세부 규칙도 직접 확인해야 한다. 비슷한 개념을 출발점으로 쓰되 메서드 이름을 기계적으로 대응시키지 않는다.

실무에서는 저장소 메서드가 ORM 객체를 밖으로 내보낼지 DTO를 내보낼지 정한다. 객체를 반환하면 변경 추적과 관계 탐색을 서비스에서 사용할 수 있지만 세션 수명이 따라온다. DTO를 반환하면 읽기 경계가 선명해지지만 업데이트 경로를 별도로 설계해야 한다. 어떤 방법이든 세션 종료 후 응답 직렬화에서 DB를 읽지 않도록 필요한 값을 준비한다.

## 성능과 주의사항

DB 병목을 객체 개수만으로 판단하지 않는다. 실행 계획, 인덱스, 반환 행 수, 왕복 횟수, 트랜잭션 유지 시간을 함께 본다. `echo=True`의 출력 순서를 읽어 “변경했지만 아직 SQL이 없다”, “SELECT 앞에서 flush가 일어났다” 같은 관찰을 기록한다. autoflush가 조회 전에 미완성 객체를 저장하려다 제약 오류를 낼 수도 있다.

SQLite 실습은 매핑과 CRUD를 익히는 데 적합하지만 PostgreSQL의 락, 연결 풀, 격리 수준, 마이그레이션 검증을 대신하지 않는다. 운영 데이터 접근에서는 유일성, 외래 키, 인덱스 같은 DB 제약을 유지하고 오류를 처리해야 한다. 애플리케이션이 먼저 중복 여부를 확인해도 다른 요청이 그 사이 같은 값을 넣을 수 있다.

## 확인 문제와 해설

1. `session.add()` 직후 ID가 항상 있는가? **해설:** 애플리케이션이 미리 부여한 키가 아니면 보통 INSERT가 실행되는 flush 후 생성 키를 얻는다. commit 전에도 ID가 있을 수 있다.
2. JOIN으로 문서를 필터링하면 소유자 관계도 자동 로딩되는가? **해설:** 일반적인 명시적 JOIN은 행 선택용이다. 관계 로딩 옵션이나 결과 연결 설정이 별도로 필요하다.
3. Session을 Redis 캐시 대신 사용할 수 있는가? **해설:** identity map은 한 세션의 객체 동일성과 상태 관리에 초점을 둔다. 여러 요청이 공유하는 조회 결과 캐시가 아니다.
4. 실습 과제: 서로 다른 사용자 20명에게 문서를 하나씩 넣고 소유자 이름 목록을 조회하라. **평가 기준:** 결과뿐 아니라 SQL 개수를 기록하고 lazy 접근, selectin 로딩, 컬럼 JOIN 조회의 차이를 설명한다. 측정하지 않은 응답시간은 성능 결과로 보고하지 않는다.

## 요약과 다음 장

Engine은 연결 인프라, Session은 짧은 업무 상태와 트랜잭션을 관리한다. 객체 접근 뒤에 숨은 SQL을 찾고 쿼리의 행 선택과 관계 로딩을 구분한다. 다음 장에서는 동일한 원칙을 AsyncEngine과 AsyncSession에 적용하며 요청 동시성, 풀 고갈, 롤백을 다룬다.

## 공식 참고자료

- [SQLAlchemy 2.0 ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html): 매핑과 2.x 조회 스타일.
- [SQLAlchemy — Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html): 세션과 트랜잭션 수명.
- [SQLAlchemy — Relationship Loading](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html): 로딩 옵션과 결과 중복 처리.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 09장 FastAPI 프로젝트 아키텍처](../09-project-architecture/chapter.md) · [11장 비동기 데이터베이스 처리 →](../11-async-database/chapter.md)
