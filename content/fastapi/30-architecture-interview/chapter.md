---
title: "30장. 실전 아키텍처 설계와 기술 면접"
description: "프레임워크 선택, 목표 처리량, 장기 연결, DB 풀, Agent 복구 문제를 조건과 근거로 설명한다. 면접 답변을 키워드 나열에서 벗어나 “무엇을 측정하고 어떤 실패를 줄일 것인가”로 구성하는 것이 목표다. 이 장의 숫자는 설계 연습의 가정이며 FastAPI의 검증된 최대 성능을 주장하는 수치가 아니다"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 30
part: 7
---

## 학습 목표와 도입 사례

프레임워크 선택, 목표 처리량, 장기 연결, DB 풀, Agent 복구 문제를 조건과 근거로 설명한다. 면접 답변을 키워드 나열에서 벗어나 “무엇을 측정하고 어떤 실패를 줄일 것인가”로 구성하는 것이 목표다. 이 장의 숫자는 설계 연습의 가정이며 FastAPI의 검증된 최대 성능을 주장하는 수치가 아니다.

면접관이 “초당 1,000개의 AI 요청을 처리할 수 있나요?”라고 묻는다. 처음 해야 할 일은 워커 개수를 말하는 것이 아니다. 요청이 문서 조회인지 모델 생성인지, 응답 시간 목표와 payload 크기, 외부 공급자의 제한, 성공·거절 정책을 확인한다. 1,000 RPS의 접수와 1,000개의 생성 완료는 매우 다른 요구다. 설계자는 모호한 숫자를 실행 가능한 계약으로 바꾼다.

## 30.1 FastAPI와 Spring Boot 선택 기준

FastAPI는 Python 생태계와 가까워 데이터 처리·모델 어댑터·실험 코드를 서비스에 연결하기 편하다. 타입 힌트와 Pydantic 검증, ASGI 기반 I/O 모델을 사용한다. Spring Boot는 JVM 기반의 조직과 라이브러리, 보안·트랜잭션·운영 관행이 이미 축적된 환경에서 자연스러운 선택일 수 있다. 비교는 팀의 경험, 핵심 라이브러리, 업무 복잡도, 장애 대응 능력까지 포함해야 한다.

“Spring은 동기, FastAPI는 비동기”라고 단순화하지 않는다. Spring MVC와 WebFlux의 실행 모델은 다르며 라이브러리까지 같은 모델에 맞춰야 한다. WebFlux를 선택해도 블로킹 DB 호출을 이벤트 처리 스레드에서 수행하면 문제가 된다. FastAPI도 `async def` 안의 동기 DB 호출은 블로킹이다. 특정 프레임워크 이름보다 전체 호출 경로와 사용하는 드라이버가 중요하다. [Spring WebFlux 공식 개요](https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html)

거래 규칙과 트랜잭션이 복잡하고 운영 팀이 JVM에 익숙하다면 기존 시스템 유지가 개발·운영 위험을 줄일 수 있다. 모델 연구 팀의 Python 자산을 빠르게 서비스화하려면 FastAPI가 맞을 수 있다. 둘을 나눠 거래 시스템과 AI gateway를 구성하는 선택도 가능하지만 네트워크 경계·배포·분산 추적 비용이 생긴다. 분리할 이유가 충분하지 않으면 언어를 늘리는 것이 좋은 아키텍처는 아니다.

면접 답변에서는 가정을 먼저 말하고 검증 계획을 덧붙인다. “우리 팀이 Python async 운영 경험을 갖고 AI 어댑터의 변경이 잦으므로 FastAPI를 선택하겠습니다. 트랜잭션 정확성이 핵심인 주문 도메인은 기존 서비스를 유지하고, 실제 요청 분포에서 p95·DB 풀·운영 비용을 비교하겠습니다.” 같은 답은 유행보다 업무 조건을 연결한다.

## 30.2 FastAPI와 Node.js 선택 기준

Node.js와 FastAPI 모두 I/O 대기가 많은 API에 적합한 구조를 만들 수 있다. Node.js의 JavaScript/TypeScript는 프런트엔드와 언어·타입 도구를 공유하기 쉽고 FastAPI는 Python 데이터·AI 라이브러리를 활용하기 쉽다. 어느 쪽이 항상 더 빠르다는 결론은 payload, 검증, 직렬화, 드라이버, CPU 작업에 따라 달라진다.

Node.js도 이벤트 루프에서 긴 계산이나 동기 I/O를 수행하면 다른 연결을 지연시킨다. 런타임의 일부 작업은 worker pool을 사용하지만 모든 사용자 계산이 자동으로 병렬 실행되는 것은 아니다. Python의 비동기 함수도 CPU 작업을 병렬화하지 않는다. 본 책의 Python 3.12 일반 CPython 환경은 GIL의 영향을 받으며 CPU 작업에는 프로세스·별도 워커 또는 해당 작업에 맞는 네이티브 연산을 검토한다. [Node.js 이벤트 루프와 worker pool 공식 설명](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)

팀이 이미 TypeScript 모노레포와 Node 관측·배포 도구를 운영한다면 AI 연동만을 위해 모든 API를 Python으로 옮길 필요는 없다. Python 모델 서비스는 별도 HTTP/작업 인터페이스로 연결할 수 있다. 반대로 Python 중심 팀이 도구 체인을 두 개 운영할 이유가 없다면 FastAPI로 시작하는 편이 단순하다. 변경 비용과 장애 조사 경로도 선택 표에 넣는다.

| 비교 기준 | 검토할 질문 |
|---|---|
| 핵심 라이브러리 | 실제 업무를 수행할 안정적인 라이브러리가 어느 환경에 있는가? |
| 팀 경험 | 이벤트 루프 블로킹, 취소, 풀 고갈을 누가 조사할 수 있는가? |
| 타입·계약 | OpenAPI와 클라이언트 생성, DTO 변경을 어떻게 관리하는가? |
| 운영 | 배포·관측·비밀 관리·온콜이 어느 환경에서 검증되어 있는가? |
| 성능 | 같은 검증·DB·응답 크기로 비교한 결과가 있는가? |

## 30.3 초당 1,000개 요청을 처리하는 API 설계

먼저 요청 mix를 정한다. 예를 들어 읽기 80%, 쓰기 15%, AI 접수 5%는 연습 가정이다. 일반 읽기 p95 150ms, 접수 p95 200ms, AI 완료 15초를 목표로 삼을 수 있다. 실제 제품 요구를 받기 전 이 값을 확정하지 않는다. payload 크기와 응답 크기, 캐시 적중률, 읽는 DB 행 수, 외부 호출 빈도를 기록한다.

서비스 전체에서 도착률과 평균 체류 시간을 곱해 평균 in-flight를 추정한다. 1,000 RPS와 평균 100ms라면 약 100개다. DB connection 평균 점유 시간이 20ms이고 모든 요청이 한 번 접근한다면 평균 약 20개의 DB 작업이 겹친다. p99, burst, 장기 트랜잭션, 재시도가 존재하므로 이 평균만으로 풀 크기를 20이라고 확정하면 안 된다. pool wait와 DB CPU/lock을 부하 시험에서 측정한다.

요청당 API CPU 시간이 평균 3ms라는 가정이면 이상적인 계산 비용은 초당 약 3 CPU-seconds다. 여기에 GC, 로그, TLS, 스케줄링, 직렬화, OS 비용과 여유를 더해야 한다. CPU 코어 세 개면 반드시 1,000 RPS를 처리한다고 해석하지 않는다. 단순 계산은 측정할 범위를 정하는 출발점이다. 캐시 도입과 SQL 최적화가 워커 증설보다 먼저 필요한지도 확인한다.

아래는 **완전 실행 예제** `capacity_plan.py`다. 표준 라이브러리만 필요하며 `python capacity_plan.py`로 실행한다. 벤치마크가 아니라 DB 연결 예산과 SSE 버퍼 가정을 계산한다.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    instances: int = 4
    workers: int = 2
    pool: int = 8
    overflow: int = 2
    background_connections: int = 20
    operations_reserve: int = 20
    db_max: int = 150

    def connections(self) -> int:
        api = self.instances * self.workers * (self.pool + self.overflow)
        return api + self.background_connections + self.operations_reserve


if __name__ == "__main__":
    plan = Plan()
    total = plan.connections()
    assert total == 120
    print({"configured_connections": total,
           "remaining_db_margin": plan.db_max - total,
           "mean_inflight_assumption": 1000 * 0.1,
           "sse_buffer_mib_assumption": 10000 * 65536 / 1024**2})
    enlarged = Plan(workers=4)
    assert enlarged.connections() > enlarged.db_max
    print("워커 증설안은 DB 연결 예산을 초과합니다:", enlarged.connections())
```

출력은 총 연결 120, 여유 30, 평균 in-flight 가정 100, SSE 버퍼 가정 625 MiB다. 워커를 네 개로 늘리는 안은 연결 200으로 DB 최대 150을 넘는다. 인스턴스·worker마다 pool이 별도로 생기는 것을 놓치지 않는 것이 핵심이다. 이 계획은 실제 동시성이 아니라 설정으로 발생할 수 있는 연결 상한을 보여 준다.

설계에는 overload 동작도 포함한다. 대기열 상한과 deadline을 두고 중요한 기능을 보호한다. 요청 제한을 모두 프록시에 맡기면 사용자별 예산과 업무 우선순위를 표현하기 어렵다. API gateway, 서비스 admission control, DB pool, 모델 슬롯을 서로 다른 경계로 두고 어느 계층에서 왜 거절했는지 측정한다. 테스트는 목표 도착률을 유지하는 구간과 burst·복구 구간을 포함한다.

## 30.4 10,000개 SSE 연결 관리 설계

SSE 수는 생성 작업 수가 아니다. 완료 이벤트를 기다리거나 알림만 구독하는 연결도 존재한다. 10,000개 연결을 유지하면서 생성은 최대 100건으로 제한할 수 있다. connection gateway와 작업 워커를 분리하고 이벤트 저장소를 통해 연결한다. 매 연결마다 DB connection을 영구 점유하지 않도록 짧게 조회하거나 알림 fan-out 뒤 저장소에서 재생한다.

먼저 파일 디스크립터와 소켓 제한, 프록시 연결·buffering, TLS 메모리, Task와 구독 버퍼를 측정한다. 64 KiB×10,000의 625 MiB는 사용자 버퍼만의 계산이고 총 메모리가 아니다. 실제 per-connection RSS는 대표 환경에서 연결 수를 단계적으로 늘려 기울기를 측정한다. 구독 큐를 메시지 개수만 제한하지 않고 바이트 상한도 적용한다.

느린 클라이언트는 계속 메모리를 쌓는 대신 제한에 도달하면 snapshot 전환이나 재접속으로 처리한다. 이벤트 ID와 보존 정책을 두고 `Last-Event-ID` 재생에서 사용자 권한을 확인한다. 토큰 만료와 권한 철회를 반영할 연결 최대 수명도 정한다. 수천 연결이 동시에 재접속하지 않도록 reconnect jitter와 접수 제한을 적용한다.

로드밸런서 뒤에서 특정 인스턴스 메모리만 이벤트를 갖고 있으면 재접속 결과가 달라진다. 공유 영속 이벤트와 job 상태를 사용하면 어느 인스턴스에 연결해도 복구할 수 있다. sticky session을 사용해도 인스턴스 장애 시나리오를 별도로 검증한다. drain 과정에서 연결 종료 안내와 마지막 cursor를 제공하고 완료되지 않은 작업은 그대로 공유 저장소에 남긴다.

## 30.5 장시간 실행되는 AI Agent 서버 설계

HTTP 접수는 짧게, Agent 수행은 내구성 작업으로 분리한다. job·outbox를 같은 트랜잭션에 저장하고 queue는 job ID를 전달한다. worker는 lease/version으로 claim하고 graph checkpoint를 저장한다. 상태 변경 도구는 operation 원장과 승인 기록을 확인한다. SSE는 영속 이벤트를 구독하고 사용자 연결이 끊겨도 job 실행 수명은 명시한 정책에 따라 유지된다.

30분 작업에 단일 timeout만 두기보다 전체 deadline과 단계별 제한을 함께 둔다. 도구가 대기하는 시간과 승인 대기 시간을 구분한다. 사람 승인이 며칠 걸릴 수 있다면 워커를 점유한 채 기다리지 않고 waiting_approval로 저장한 뒤 lease를 반납한다. 승인 시점에 payload hash, 대상, 만료, 현재 인가를 다시 확인해 재개한다.

복구할 상태는 적어도 네 가지다. 실행 전 확정 실패는 안전하게 다시 시도한다. 읽기 도구 완료는 저장 결과를 재사용할 수 있다. 외부 변경 완료는 operation 결과를 조회해 다음 단계로 간다. 결과 불명은 외부 조회·멱등성 또는 사람 확인으로 처리한다. checkpoint가 있다고 모든 노드를 재실행하는 전략은 중복 외부 효과와 비용을 만든다.

그래프 정의와 프롬프트 버전을 run에 고정하면 배포 중 오래된 실행을 재현하기 쉽다. 새 버전으로 이어 실행하려면 state migration 규칙을 만든다. 작업 삭제·보존·취소도 모델 스레드와 업무 DB, 객체 저장소를 함께 고려한다. event retention이 job보다 짧다면 오래된 cursor에 snapshot을 제공할 수 있어야 한다.

## 30.6 DB 커넥션 풀 고갈 문제 해결

pool timeout은 DB를 무조건 더 크게 만들라는 신호가 아니다. 먼저 연결 acquisition wait, transaction duration, checked-out 수, DB active query와 lock wait를 확인한다. 모델 호출 동안 transaction을 유지하거나 streaming generator 전체에 DB 의존성 수명을 걸면 연결이 오래 반환되지 않을 수 있다. 필요한 데이터를 읽고 트랜잭션을 닫은 뒤 외부 호출을 수행한다.

pool_size를 늘리면 대기 중 요청이 DB에 더 많이 진입한다. DB CPU·디스크·lock이 병목이면 처리량은 같고 tail latency만 악화된다. 인스턴스와 worker, background worker의 pool 합을 최대 연결 수와 비교한다. 관리·migration·모니터링 연결 여유도 남긴다. DB pooler가 있다면 session/transaction pooling과 prepared statement·세션 설정 호환성을 실제 드라이버로 검증한다.

동시에 여러 SQL을 실행하려고 같은 AsyncSession을 `gather`에 넣는 방법은 피한다. Session은 하나의 트랜잭션 상태를 관리하는 객체다. 독립 병렬 작업에는 독립 세션을 사용하고 DB에 필요한 동시성을 제한한다. 이 경우에도 connection 수를 늘리는 효과가 있으므로 쿼리 합치기·eager loading·인덱스로 불필요한 접근을 먼저 줄인다.

면접 답변은 진단·완화·근본 해결을 나눠 말한다. 현재 overload를 제한하고 stuck 트랜잭션을 확인한 뒤, 외부 호출과 DB 생명주기를 분리하고 느린 쿼리를 수정한다. 변경 후 같은 workload에서 pool wait, throughput, p95·p99를 비교한다. “pool을 100으로 바꾸겠습니다”만으로 끝내지 않는다.

## 30.7 비동기 API 응답 지연 분석

요청 timeline을 proxy wait, app dispatch, dependency, DB acquire/query, external queue/call, validation, serialization으로 나눈다. 이벤트 루프 지연이 커지고 여러 endpoint가 함께 느려지면 blocking 함수·CPU 작업·과도한 로그를 조사한다. 특정 DB endpoint만 느리면 pool·query·lock을 먼저 본다. 특정 공급자 모델만 느리면 모델 슬롯·429·TTFT를 확인한다.

`await`가 많다는 이유로 비동기 최적화가 잘 되었다고 판단하지 않는다. `async def helper()` 안에서 requests, 동기 ORM, `time.sleep`, 큰 정렬을 수행하면 블로킹할 수 있다. def helper를 async 라우트에서 직접 호출하면 FastAPI가 자동으로 threadpool로 보내지 않는다. FastAPI가 관리하는 동기 endpoint/의존성과 직접 함수 호출을 구분한다.

trace에는 입력 원문 대신 안전한 크기·작업 ID·결과 코드를 남긴다. tail latency를 평균으로 숨기지 않고 p95/p99, timeout, 거절률을 함께 본다. 클라이언트 측 부하 생성기가 먼저 포화되면 결과가 잘못될 수 있다. 성능 회귀 원인을 찾을 때 코드 외에도 pool 설정·프롬프트 길이·문서 인덱스·모델 버전을 비교한다.

## 30.8 장애 복구가 가능한 백엔드 설계

장애 복구는 “재시작하면 된다”가 아니라 재시작 후 어떤 상태를 복원하는지 정의하는 일이다. 업무 DB의 durable state, queue delivery, checkpoint, external operation result, usage ledger를 연결한다. 적어도 한 번 전달되는 메시지에 대해 상태 전이를 멱등하게 만들고, 시스템 밖의 효과는 공급자 지원과 업무 정책으로 처리한다.

DB commit 후 queue publish 전 장애는 outbox로 줄인다. 외부 수행 후 DB 저장 전 장애는 operation ID와 외부 조회/멱등성으로 대응한다. lease 만료 뒤 이전 worker가 돌아오는 경우는 fencing/version으로 늦은 저장을 막는다. 사용자 reconnect 때 event 중복은 event ID와 snapshot으로 처리한다. 각 장애 창을 구체적으로 설명할 수 있어야 복구 설계가 검토 가능하다.

복구 실험은 통제된 환경에서 해당 창에 강제 종료를 넣는다. 상태가 복구되는지뿐 아니라 중복 과금·도구 효과·예약 누수가 없는지 확인한다. 삭제된 문서가 재처리로 부활하는지도 시험한다. recovery time과 data loss 범위를 측정하고 제품이 감당할 수 있는 목표와 비교한다. backup 존재만 확인하지 말고 실제 복원 절차를 연습한다.

## 30.9 FastAPI 핵심 기술 면접 질문

다음 답변은 단어 암기보다 경계를 설명하는 연습이다. 각 답 뒤에는 자신의 프로젝트에서 확인한 예와 한계를 덧붙인다.

| 질문 | 답변의 핵심 |
|---|---|
| ASGI의 scope, receive, send는 무엇인가? | scope는 연결/요청 정보, receive와 send는 비동기 메시지 경로다. 단일 body 문자열 함수와 다르다. |
| async def와 def 라우트는 어떻게 다른가? | async 라우트는 이벤트 루프에서 실행되고 FastAPI가 관리하는 def 라우트는 threadpool로 처리한다. 직접 호출한 def helper는 자동 offload되지 않는다. |
| Coroutine과 Task는 같은가? | coroutine 객체는 실행 가능한 작업이고 Task는 이벤트 루프가 스케줄링하는 실행 단위다. 소유권·예외·취소 수명을 관리해야 한다. |
| await는 새 스레드를 만드는가? | 아니다. 기다리는 awaitable에 제어를 넘길 수 있는 지점이다. CPU 병렬 실행을 보장하지 않는다. |
| Depends는 싱글턴 DI인가? | 요청별 의존성 그래프와 기본 요청 범위 캐싱을 갖는다. 객체 생명주기와 use_cache/yield 범위를 명확히 한다. |
| yield 의존성은 왜 사용하는가? | 리소스 획득과 정리를 연결한다. 응답·스트림 수명과 정리 시점은 사용하는 FastAPI 버전과 scope 설정을 확인한다. |
| AsyncSession을 공유해도 되는가? | 독립 concurrent Task 사이에는 공유하지 않는다. 세션은 트랜잭션 상태를 가진다. |
| worker를 늘리면 모든 병목이 해결되는가? | 아니다. 프로세스별 메모리·pool이 늘고 DB/모델 제한을 넘길 수 있다. 병목과 예산을 먼저 측정한다. |
| BackgroundTasks는 내구성 큐인가? | 아니다. 프로세스 장애 복구·중복·재시도 상태를 제공하는 작업 시스템과 다르다. |
| JWT를 decode하면 인증 완료인가? | 서명·허용 algorithm·exp·aud·iss·필수 claim과 계정 상태를 확인해야 한다. 인가는 각 리소스에서 별도다. |
| CORS는 인증을 대체하는가? | 아니다. 브라우저의 출처 정책이며 비브라우저 호출과 리소스 권한을 막지 않는다. |
| 스트림 중 오류를 500으로 바꿀 수 있는가? | 헤더를 이미 보냈다면 불가능하다. 오류 이벤트와 incomplete 상태를 표현한다. |
| client disconnect는 작업 취소와 같은가? | 제품 계약에 따라 다르다. 즉시 작업은 취소할 수 있고 내구성 job은 구독만 끊을 수 있다. |
| 캐시 키에 question만 넣어도 되는가? | RAG에서는 tenant/ACL·인덱스·모델·템플릿·맥락 버전이 필요하다. |
| outbox가 exactly once를 보장하는가? | 아니다. 발행 누락을 줄이고 중복은 소비자 멱등성으로 처리한다. 외부 효과는 별도 경계다. |
| checkpoint가 있으면 도구를 다시 실행해도 되는가? | 부작용 완료 여부와 operation 원장을 먼저 확인한다. 결과 불명은 조회 또는 사람 확인으로 처리한다. |
| p95가 좋아졌는데 거절률도 늘었다면? | 성공 요청만 빠르게 만들었을 수 있다. 목표 workload의 완료율·거절·품질과 함께 판단한다. |
| prompt injection은 시스템 프롬프트로 끝나는가? | 아니다. 검색 ACL·도구 allowlist·서버 인가·입력 검증·승인 경계를 모델 바깥에서 적용한다. |

좋은 답변에는 조건이 있다. 예를 들어 “threadpool로 보내면 해결됩니다” 대신 “짧은 블로킹 I/O는 제한된 threadpool로 옮길 수 있지만 CPU 작업은 병렬성·GIL·자원 비용을 따로 검토하고 기존 pool을 고갈시키지 않아야 합니다”라고 설명한다. 한 해결책의 적용 범위를 아는 것이 실무 역량이다.

## 30.10 실무 설계 리뷰와 개선 과제

설계 리뷰는 데이터 흐름과 실패 지점에서 시작한다. 사용자 입력이 인증·검증·권한을 어디서 통과하는지, DB connection을 얼마나 보유하는지, 외부 부작용의 성공을 어디서 기록하는지, SSE 오류를 어떻게 전달하는지 표시한다. 의존성 다이어그램이 아름다워도 이 질문에 답하지 못하면 운영 위험은 남는다.

29장 프로젝트를 리뷰하면 작은 단일판의 장점과 한계가 모두 보인다. owner SQL, 예산 트랜잭션, idempotency 제약, 영속 이벤트는 명확하다. 실제 임베딩·LangGraph·외부 도구·분산 lease·로그인 남용 방어·관측 exporter는 추가해야 한다. 이 목록을 “조금만 더 하면 완성”이라고 감추지 않고 우선순위와 검증 기준으로 바꾼다.

개선 과제 하나는 document revision과 삭제다. 업로드·인덱스 활성화·검색·과거 인용의 정책을 정하고 늦은 워커가 삭제 문서를 복구하지 못하게 시험한다. 또 다른 과제는 job lease와 fencing이다. 두 워커 중 이전 lease의 워커가 나중에 결과를 저장해도 거절되는지 검증한다. 세 번째는 외부 도구 operation 원장이다. 공급자 mock가 성공 후 응답을 잃는 상황에서 중복 효과와 결과 불명을 구분한다.

리뷰 문서는 선택, 이유, 대안, 위험, 검증을 짧게 연결한다. “Redis를 사용한다”보다 “동일 사용자의 접수 폭주를 여러 인스턴스에서 제한하기 위해 Redis 원자 연산을 사용하고, 장애 때 비용 상한을 지키도록 제한적으로 거절한다”가 검토하기 쉽다. 모든 컴포넌트를 한 번에 도입하기보다 위험한 경계를 먼저 구현하고 테스트한다.

## 확인 문제와 해설 및 설계 실습

1. 1,000 RPS와 평균 100ms로 필요한 서버를 정확히 계산할 수 있는가? **해설:** 평균 in-flight 약 100은 추정할 수 있지만 CPU·DB·burst·payload·tail latency·안전 여유를 모르면 인스턴스 수를 확정할 수 없다.
2. SSE 10,000연결이 있으면 모델 호출도 10,000건 동시에 허용해야 하는가? **해설:** 아니다. 구독 연결과 실행 슬롯은 분리한다. 큐와 영속 이벤트로 연결할 수 있다.
3. pool timeout이 발생하면 pool_size를 즉시 늘려도 되는가? **해설:** connection 점유·query·lock·DB 용량을 확인한다. DB 병목이면 동시성 증가는 tail latency를 악화시킬 수 있다.
4. 설계 발표 과제는 어떻게 평가하는가? **해설:** 요청 mix와 SLO, 모든 pool 합, admission control, 권한 경계, 장애 창, 비용 상한, 실험 계획을 설명해야 한다. 검증하지 않은 최대 RPS를 확정값처럼 제시하면 실패다.
5. Agent 복구 과제의 합격 기준은? **해설:** 외부 수행 직후와 DB 저장 직전 장애를 주입한다. 중복 operation을 흡수하거나 outcome_unknown을 명확히 표시하고 예약·정산을 일관되게 복구한다.

## 요약과 학습 이후

아키텍처 답변은 도구 이름보다 실행 경계와 검증 계획으로 완성된다. 비동기 I/O의 장점은 블로킹·무한 대기·무제한 동시성을 관리할 때 드러난다. 작은 프로젝트에서 권한·트랜잭션·작업·스트림·복구의 경계를 직접 확인하고, 실제 업무의 위험과 측정 결과에 맞춰 다음 기능을 확장한다. 책의 마지막 과제는 자신의 서비스 하나를 골라 이 경계와 실패 시나리오를 문서로 설명하는 것이다.

## 공식 참고자료

- [Spring WebFlux overview](https://docs.spring.io/spring-framework/reference/web/webflux/new-framework.html): 프레임워크 실행 모델 비교.
- [Node.js Don't Block the Event Loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop): 블로킹과 worker pool 경계.
- [Python 3.12 asyncio](https://docs.python.org/3.12/library/asyncio-task.html): Task·취소·deadline.
- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/): 프로세스와 배포 자원 고려.

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 29장 실전 프로젝트: RAG 기반 AI Agent 플랫폼](../29-capstone/chapter.md) · [학습 로드맵 →](../appendices/learning-roadmap.md)
