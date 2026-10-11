---
title: "27장. AI Agent 서버 구축"
description: "Agent가 다음 행동을 제안하는 것과 서버가 행동을 허용하는 것을 분리한다. 실행 상태, 체크포인트, 작업 큐, 승인 기록의 역할을 구분하고 장기 실행을 안전하게 재개하는 구조를 설계한다. LangGraph를 사용하더라도 인증·멱등성·비용 경계는 애플리케이션의 책임이라는 점을 이해하는 것이 목표다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 27
part: 7
---

## 학습 목표와 도입 사례

Agent가 다음 행동을 제안하는 것과 서버가 행동을 허용하는 것을 분리한다. 실행 상태, 체크포인트, 작업 큐, 승인 기록의 역할을 구분하고 장기 실행을 안전하게 재개하는 구조를 설계한다. LangGraph를 사용하더라도 인증·멱등성·비용 경계는 애플리케이션의 책임이라는 점을 이해하는 것이 목표다.

Knowledge Hub의 사용자가 “배포 매뉴얼을 읽고 변경 티켓을 만들어 줘”라고 요청한다. Agent는 검색과 요약 다음에 티켓 생성 도구를 선택한다. 외부 티켓 생성은 성공했지만 워커가 결과를 저장하기 전에 죽었다. 단순히 마지막 노드를 다시 실행하면 티켓이 두 개 생길 수 있다. Agent의 복구 문제는 대화 기록을 저장하는 문제만이 아니라 실제 부작용과 실행 상태를 일치시키는 문제다.

## 27.1 AI Agent의 실행 구조

Agent는 관찰, 계획 또는 다음 행동 선택, 도구 실행, 결과 해석, 종료 판단을 반복한다. 모델은 행동 후보를 생성하고 서버는 도구 목록·권한·입력·예산을 검증한 뒤 실행한다. 무한 루프를 방지하려면 최대 단계 수, 최대 도구 호출 수, 전체 deadline, 최대 비용을 함께 둔다. “목표를 달성할 때까지”는 운영 가능한 종료 조건이 아니다.

실행 상태에는 입력, 현재 노드, 완료 단계, 근거 ID, 도구 결과 참조, 남은 예산, 승인 대기 정보, 실패 이유를 포함한다. 상태에 DB Session, HTTP 클라이언트, 파일 핸들을 넣으면 직렬화와 복구가 어려워진다. 대신 문서·작업·도구 실행 ID를 저장하고 재개 시 필요한 리소스를 새로 획득한다. 긴 텍스트와 대용량 산출물은 객체 저장소에 두고 상태에는 참조와 해시를 남긴다.

서버가 정의한 워크플로와 모델의 자유 선택을 혼합할 수 있다. 예를 들어 문서 검색과 권한 확인은 필수 노드로 두고, 추가 검색 여부만 모델이 선택하게 한다. 위험이 높은 도구는 별도 승인 노드로 보낸다. 모든 행동을 모델에게 맡기는 구조보다 종료 조건과 감사가 분명하다. Agent가 필요한지는 자동화하려는 업무가 동적인 판단을 요구하는지 먼저 평가한다. 고정된 두 단계 작업이면 일반 서비스 함수가 더 단순할 수 있다.

## 27.2 Tool Calling과 API 연동

도구 스키마는 권한이 아니다. 모델이 `create_ticket(project_id=...)`를 제안하면 서버는 인증한 사용자가 해당 프로젝트에 티켓을 만들 수 있는지 다시 확인한다. 사용자 ID, tenant ID, 인증 토큰 같은 보안 컨텍스트는 모델 인자가 아니라 서버가 주입한다. 도구 이름은 허용 목록에서 선택하고 알 수 없는 이름은 실패로 처리한다. 문자열을 `eval`, shell, 임의 URL 호출로 바꾸지 않는다.

도구 입력은 Pydantic으로 타입·길이·범위를 검증하고 업무 규칙으로 대상 상태를 확인한다. URL 도구라면 허용 호스트와 IP 범위를 검증하며 리다이렉트도 같은 정책을 적용한다. SQL 도구는 읽기 전용 계정과 제한된 질의 인터페이스를 사용하고, 모델이 만든 SQL을 운영 관리자 계정으로 실행하지 않는다. 검색 문서에 삽입된 “관리자 도구를 실행하라”는 문장은 권한 승격을 발생시키지 않아야 한다.

도구를 읽기, 상태 변경, 외부 전송으로 분류하면 승인 정책을 정하기 쉽다. 내부 문서 검색은 자동 실행할 수 있어도 외부 티켓 작성은 검토가 필요할 수 있다. 도구 결과 역시 신뢰할 수 없는 입력이다. 웹 페이지가 비밀을 요구하는 내용을 반환했다고 후속 도구가 토큰을 전달하면 안 된다. 서버가 허용한 정보 흐름을 넘는 행동은 모델 설명이 그럴듯해도 거절한다.

도구 실행 원장은 `(run_id, step_id, operation_id)`로 관리한다. 호출 전 intent를 기록하고 실행 후 결과·외부 ID를 기록한다. 외부 시스템이 idempotency key를 지원하면 같은 operation ID를 전달한다. 결과 저장 전에 장애가 나면 외부 ID 조회나 멱등성 재요청으로 수행 여부를 확인한다. 외부 시스템에 이런 기능이 없다면 exactly once를 보장한다고 주장하지 않고 결과 불명 상태와 사람 확인 경로를 둔다.

## 27.3 LangGraph와 FastAPI 통합

LangGraph는 상태와 노드, 간선으로 실행 흐름을 구성한다. 각 노드는 상태를 읽고 업데이트를 반환하고, 간선은 다음 단계를 결정한다. 체크포인터를 통해 대화·실행 상태를 보존할 수 있지만 메모리 저장소는 프로세스 종료 후 상태를 유지하지 않는다. 이 장에서는 이 제한을 운영 구조와 연결한다. [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

FastAPI 라우터는 요청을 검증하고 run을 저장한 뒤 202와 run ID를 반환한다. 워커가 LangGraph 실행을 담당한다. 짧고 부작용 없는 실험은 라우터에서 `ainvoke`를 호출할 수 있지만, 장기 작업과 승인 대기는 HTTP 연결 수명에서 분리한다. 그래프 정의는 프로세스 시작 시 만들 수 있으며 DB checkpointer와 HTTP 어댑터 수명은 lifespan 또는 워커 생명주기에 맞춘다.

아래는 **개념 예제**다. 설치 버전에 맞는 LangGraph API를 확인해 적용한다. 모델 호출은 전혀 하지 않으며 그래프와 비동기 라우트의 연결을 보여 준다. `InMemorySaver`는 학습용이고 서버 재시작 복구를 제공하지 않는다. 실제 인증·작업 DB·큐를 구현한 코드로 간주하면 안 된다.

```python
from typing import TypedDict
from fastapi import FastAPI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    question: str
    answer: str

async def compose(state: State):
    return {"answer": "모의 응답: " + state["question"]}

builder = StateGraph(State)
builder.add_node("compose", compose)
builder.add_edge(START, "compose")
builder.add_edge("compose", END)
graph = builder.compile(checkpointer=InMemorySaver())
app = FastAPI()

# Isolated local demonstration; a production route first verifies ownership.
@app.post("/demo")
async def demo(question: str):
    import uuid
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    return await graph.ainvoke({"question": question, "answer": ""}, config)
```

운영의 thread ID는 서버가 발급하고 `(tenant, user, conversation)` 소유권과 연결한다. 사용자가 임의 thread ID를 보내 다른 사람의 체크포인트를 이어 쓰지 못하게 조회·재개·스트림 모두 인가한다. 그래프 내부 상태를 그대로 API에 보내지 않는다. 체크포인트에는 프롬프트, 도구 입력, 검색 결과가 포함될 수 있으므로 필요한 공개 이벤트만 별도 응답 모델로 변환한다.

## 27.4 Agent 실행 상태 관리

작업 상태는 queued, running, waiting_approval, succeeded, failed, cancelled, outcome_unknown처럼 정의한다. 상태 전이는 조건부 UPDATE로 보호한다. running이었던 워커만 completed를 기록해야 하며, 이미 cancelled인 작업을 늦은 결과가 succeeded로 덮어쓰지 않도록 버전 또는 lease token을 함께 확인한다. 상태 행과 이력 이벤트를 같은 트랜잭션으로 저장하면 “완료 상태인데 완료 이벤트가 없다”는 불일치를 줄일 수 있다.

워크플로 체크포인트와 공개 작업 상태는 서로 다르다. 체크포인트는 그래프를 재개할 내부 상태이고 작업 행은 API가 보여 주는 접수·권한·정산 상태다. 두 저장소의 커밋은 자동으로 하나의 트랜잭션이 되지 않는다. 재조정기가 체크포인트와 job을 비교해 어긋난 상태를 복구할 수 있게 run ID를 연결한다. 최종 상태를 명확히 결정하는 책임자를 하나 두고 여러 컴포넌트가 제각각 완료를 선언하지 않는다.

## 27.5 사용자 세션과 대화 기록

대화 ID, 실행 ID, HTTP request ID는 각각 다르다. 대화는 여러 실행을 묶고 실행은 하나의 입력 처리 과정을 식별하며 요청 ID는 접수나 조회 호출 하나를 추적한다. 이 식별자를 혼용하면 같은 대화에 동시에 입력했을 때 체크포인트가 덮어써지거나 작업 결과가 섞인다. 대화별 직렬 실행, 버전 충돌 거절, 분기 대화 중 하나를 선택한다.

기록 전체를 매번 프롬프트에 넣으면 비용과 개인정보 노출이 증가한다. 필요한 최근 메시지와 검증한 요약을 구성한다. 요약에도 오류가 들어갈 수 있으므로 업무상 중요한 승인·수치·문서 버전은 구조화 저장소에서 다시 읽는다. “사용자가 이전에 관리자라고 말했다”는 대화 기억은 인증 정보가 아니다. 장기 기억 저장소의 namespace와 조회에도 tenant/user 조건을 적용한다.

보존 기간, 사용자 삭제 요청, 접근 감사도 대화 기능의 일부다. 체크포인트를 영구 보존하면 모델 호출보다 저장 비용이 더 커질 수 있다. 오래된 이벤트를 정리할 때 실행 재개와 SSE 재생의 최소 보존 기간을 함께 고려한다. 삭제된 대화의 worker가 늦게 기록을 다시 생성하지 않도록 종료 상태와 tombstone을 확인한다.

## 27.6 장기 실행 Agent의 작업 관리

내구성 큐에서 메시지를 받은 워커는 lease를 획득하고 heartbeat로 갱신한다. 장애로 lease가 만료되면 다른 워커가 가져갈 수 있다. 그러나 이전 워커가 잠시 느려졌을 뿐 살아 있다면 두 워커가 동시에 실행할 수 있다. fencing token이나 버전 조건을 저장 연산에 적용해 오래된 워커가 상태를 바꾸지 못하게 한다. 외부 도구는 이 조건을 공유하지 않으므로 별도 멱등성 경계가 필요하다.

API의 DB commit과 queue publish를 직접 연속 호출하면 사이의 장애 창이 생긴다. job과 outbox를 같은 DB 트랜잭션에 저장하고 발행기가 재시도한다. 메시지가 두 번 발행될 수 있으므로 워커는 run ID를 기준으로 중복을 흡수한다. outbox는 발행 누락을 줄이고 dedup은 중복 처리 결과를 막는 역할이다. 큐 제품을 선택했다고 이 두 문제가 자동으로 해결되지는 않는다.

사용자 취소는 상태 변경 요청이다. 취소 가능 노드에서 실행을 멈추고 리소스를 정리한다. 이미 외부에 전송한 작업은 취소 API 지원 여부에 따라 결과가 다르다. 티켓을 만들고 나서 되돌리는 것은 원래 작업의 rollback과 같지 않은 보상 작업이다. 보상도 실패할 수 있으므로 감사 기록과 재시도 정책을 갖는다. “취소 버튼을 누르면 없던 일이 된다”는 계약은 피한다.

## 27.7 Agent 실행 결과 스트리밍

Agent 이벤트는 단계 시작·끝, 근거 발견, 승인 필요, 모델 delta, 오류, 최종 결과로 나눌 수 있다. 내부 프롬프트와 도구 비밀 정보를 공개하지 않고 안전한 공개 DTO로 만든다. 도구 결과 원문에 다른 권한 범위의 데이터가 포함될 수 있으므로 공개 전에 검증한다. 사고 과정을 그대로 전송하기보다 수행한 작업의 간단한 상태와 근거를 제공한다.

이벤트를 저장한 뒤 전송하면 재접속 때 `Last-Event-ID`로 재생할 수 있다. at least once 재생에서는 클라이언트가 event ID로 중복 delta를 제거해야 한다. 보존 기간이 지난 cursor라면 불완전한 이어쓰기를 시도하지 않고 snapshot과 새 cursor를 제공한다. 느린 클라이언트 때문에 워커가 멈추지 않도록 생성 실행과 전송 구독을 분리하고 구독자 버퍼 크기에 상한을 둔다.

## 27.8 Human-in-the-Loop 승인 구조

사람의 승인은 특정 행동에 대한 권한이다. “Agent 실행을 승인함”만 저장하면 Agent가 승인 후 인자를 바꿔 전혀 다른 행동을 수행할 수 있다. 승인 화면에는 도구, 대상, 입력, 예상 영향, run/step ID를 보여 주고 canonical payload의 해시와 만료 시간을 저장한다. 실행 직전에 현재 인가와 인자 해시를 다시 확인한다. 승인한 뒤 조직 권한이 철회되었으면 실행을 거절해야 한다.

LangGraph의 interrupt는 실행을 중단해 입력을 기다리는 흐름을 표현한다. 재개 시 노드 코드가 다시 실행될 수 있으므로 interrupt 이전 부작용을 안전하게 설계해야 한다. 승인 기록의 업무 정책과 외부 도구 멱등성은 별도로 구현한다. [LangGraph Interrupts 공식 문서](https://docs.langchain.com/oss/python/langgraph/interrupts)

다음은 **완전 실행 예제** `approval_demo.py`다. 네트워크 호출 없이 승인과 실제 인자 결합을 확인한다. 표준 라이브러리만 필요하며 `python approval_demo.py`로 실행한다. 메모리 기록은 프로세스 재시작에 견디지 못하므로 업무 구조 학습용이다.

```python
import hashlib
import json
from dataclasses import dataclass


def fingerprint(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode()
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class Approval:
    owner: str
    run_id: str
    step_id: str
    payload_hash: str


class Agent:
    def __init__(self):
        self.approvals: dict[tuple[str, str], Approval] = {}
        self.results: dict[tuple[str, str], dict] = {}

    def approve(self, owner: str, run: str, step: str, payload: dict):
        self.approvals[(run, step)] = Approval(owner, run, step, fingerprint(payload))

    def execute(self, owner: str, run: str, step: str, payload: dict) -> dict:
        approval = self.approvals[(run, step)]
        if approval.owner != owner or approval.payload_hash != fingerprint(payload):
            raise PermissionError("approval does not authorize this action")
        if payload.get("tool") != "create_mock_ticket":
            raise ValueError("tool not allowed")
        key = (run, step)
        if key not in self.results:
            self.results[key] = {"ticket_id": "mock-001", "title": payload["title"]}
        return self.results[key]


if __name__ == "__main__":
    agent = Agent()
    payload = {"tool": "create_mock_ticket", "title": "배포 검토"}
    agent.approve("alice", "run-1", "step-1", payload)
    first = agent.execute("alice", "run-1", "step-1", payload)
    assert agent.execute("alice", "run-1", "step-1", payload) == first
    try:
        agent.execute("alice", "run-1", "step-1", {**payload, "title": "다른 작업"})
    except PermissionError:
        print("변경한 행동 거절")
    else:
        raise AssertionError("modified payload was incorrectly approved")
    print(first)
```

기대 결과는 “변경한 행동 거절”과 mock-001 결과다. 이 코드의 결과 사전은 실제 분산 멱등성을 제공하지 않는다. 운영에서는 승인 행 unique 제약, 조건부 상태 전이, 결과 원장, 외부 시스템의 멱등성 기능을 결합한다. 승인 API를 접수하는 사용자가 승인자 역할을 갖는지도 확인한다.

## 27.9 Agent 오류 처리와 실행 복구

오류를 transient, validation, permission, budget, human rejection, unknown outcome으로 나눈다. 일시적인 검색 장애는 다시 시도할 수 있지만 거절된 승인과 권한 오류는 모델에게 더 강하게 요청해서 해결할 문제가 아니다. 도구 오류 원문을 모델에 넘길 때 비밀 키, SQL, 내부 호스트가 포함되지 않도록 정규화한다. 최종 오류는 사용자에게 행동 가능한 안내를 주되 내부 정보를 노출하지 않는다.

복구는 체크포인트의 마지막 노드를 무조건 다시 실행하는 일이 아니다. 노드가 무엇을 수행했는지 원장과 비교해야 한다. 외부 효과가 완료되었다면 저장 결과를 읽고 다음 단계로 넘어간다. 실행 여부가 불명확하면 외부 조회 또는 사람 확인을 요청한다. 프롬프트·그래프 버전이 변경되었다면 예전 실행을 새 구조에 그대로 재개할 수 있는지도 확인한다. 장기 작업에는 실행 버전을 고정하는 전략이 유용하다.

## 27.10 다중 Agent 실행 관리

여러 Agent를 동시에 돌리면 서로 다른 관점을 얻을 수 있지만 비용과 실패 조합도 늘어난다. Agent별 역할, 도구 권한, 입력 범위를 최소화하고 최종 결정을 누가 내리는지 정한다. 요약 Agent가 티켓 작성 도구까지 가질 필요는 없다. 한 Agent의 생성 내용을 다른 Agent가 사실로 받아들이지 않도록 출처와 검증 상태를 전달한다.

부모 작업 예산은 자식에게 할당한 예산의 합을 제한한다. 각 자식이 같은 전체 예산을 받으면 fan-out 수만큼 비용이 증가한다. 결과 취합에는 deadline과 실패 정책을 정의한다. 일부 결과만으로 답할지 모두 실패로 처리할지 업무 특성에 맞춘다. 여러 자식이 같은 외부 행동을 제안하면 최종 실행 조정자가 한 operation ID로 합쳐야 한다. 다중 Agent는 중복 행동을 허용하는 근거가 아니다.

## 확인 문제와 해설

1. 체크포인트가 있으면 외부 티켓을 정확히 한 번 생성할 수 있는가? **해설:** 체크포인트와 외부 효과는 원자적으로 커밋되지 않는다. operation 원장, 외부 멱등성·조회, 결과 불명 정책이 필요하다.
2. 승인을 받은 뒤 도구 인자를 바꾸면 왜 다시 검증해야 하는가? **해설:** 승인은 특정 대상과 payload에 결합되어야 한다. 해시, 만료, 현재 권한을 실행 직전에 확인한다.
3. 사용자가 thread ID를 알고 있으면 체크포인트를 이어 실행해도 되는가? **해설:** 식별자 보유는 권한이 아니다. thread 소유권과 접근 범위를 별도로 인가한다.
4. 복구 실습의 합격 기준은 무엇인가? **해설:** 외부 효과 직후 장애를 주입해 동일 operation 재실행이 중복 효과를 만들지 않는지 확인한다. 보장할 수 없는 시스템이면 outcome_unknown과 검토 경로를 명시해야 한다.

## 요약과 다음 장

Agent는 모델의 행동 제안 위에 서버의 허가, 작업 상태, 승인, 복구를 결합한 시스템이다. LangGraph는 실행 흐름과 상태를 조직하지만 제품의 보안과 부작용 정책을 대신하지 않는다. 다음 장은 많은 사용자가 동시에 Agent와 스트림을 사용했을 때 용량과 비용을 어떻게 통제하는지 다룬다.

## 공식 참고자료

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api): 상태·노드·간선 구성.
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence): 체크포인터와 저장소 범위.
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts): 중단·재개와 노드 재실행 주의.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 26장 RAG 서비스 백엔드 구축](../26-rag/chapter.md) · [28장 AI 서비스 성능과 확장성 →](../28-ai-scalability/chapter.md)
