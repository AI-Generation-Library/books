---
title: "22장. Actuator·로그·메트릭·트레이스"
description: "Actuator 노출·health·liveness/readiness, Micrometer 지표·카디널리티·구조 로그·분산 추적을 장애 질문에 연결한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 22
part: 5
enableToc: true
---

> PART 5. 검증과 운영

## 도입: 서버는 UP인데 사용자는 예약할 수 없다

프로세스는 살아 있고 단순 health도 성공하지만 DB 풀이 고갈돼 예약이 모두 실패한다. “살아 있음”과 “요청을 처리할 준비가 됨”과 “업무가 성공함”은 다른 신호다. 운영 관측은 이 차이를 드러내야 한다.

## 22.1 Actuator는 운영 기능의 입구다

Actuator는 health·info·metrics 등 운영용 endpoint를 제공한다. endpoint가 존재하는 것, 웹에 노출되는 것, 권한상 접근 가능한 것은 별도다. `management.endpoints.web.exposure.include=*`를 그대로 공개 인터넷에 연결하지 않는다. 환경·빈·로그·덤프에 민감한 정보가 포함될 수 있다.

예제는 health와 info만 노출하고 health의 세부 정보는 숨긴다. SecurityConfig는 health만 익명 허용한다. Prometheus 수집·트레이스 전송기를 포함하지 않으므로 endpoint 몇 개가 열린 것을 완성된 모니터링이라고 부르지 않는다.

## 22.2 liveness와 readiness

**Liveness**는 프로세스를 다시 시작해야 하는 내부 생존 상태, **readiness**는 지금 트래픽을 받을 준비가 됐는지를 판단하는 관점이다. 공유 DB가 잠깐 느릴 때 모든 앱의 liveness를 실패시키면 동시에 재시작하며 장애를 악화시킬 수 있다.

readiness에 어떤 외부 의존성을 포함할지는 서비스 특성에 따라 정한다. 일부 기능만 영향을 받는 외부 검색 장애 때문에 모든 예약 트래픽을 끊어야 하는지 검토한다. 관리 포트의 health만 성공하고 실제 서비스 포트가 고장 난 상황도 고려한다.

## 22.3 메트릭은 질문의 숫자 표현이다

**Micrometer**는 여러 관측 백엔드에 메트릭을 전달하는 추상화다. Counter는 누적 횟수, Timer는 시간과 횟수 분포, Gauge는 현재 값에 적합하다. 다음은 별도 관측 확장 시 사용할 부분 코드다.

```java
registry.counter("reservation.result", "outcome", "out_of_stock").increment();
```

outcome처럼 값 종류가 제한된 태그를 사용한다. 사용자 ID·예약 ID·전체 URL·예외 메시지를 태그에 넣으면 시계열 수가 폭증하는 **높은 카디널리티** 문제가 생긴다. 개별 사건은 로그·트레이스에 두고 집계 메트릭은 제한된 차원을 유지한다.

| 장애 질문 | 함께 볼 신호 |
| --- | --- |
| DB를 못 빌리는가? | 풀 active·idle·pending·획득 timeout |
| SQL이 느린가? | 쿼리 지연, 락 대기, DB CPU·I/O |
| 앱이 과부하인가? | 처리량, in-flight, 스레드, GC·CPU |
| 업무가 실패하는가? | 성공·품절·인프라 실패를 분리한 비율 |
| 이벤트가 밀리는가? | Outbox 미처리 나이·건수·재시도 |

품절 409는 제품 재고 문제이고 DB 500은 인프라 실패다. 둘을 같은 “에러율”로만 묶으면 운영 판단이 어려워진다.

## 22.4 로그·트레이스·상관관계

구조 로그에는 시각·수준·서비스 버전·업무 코드·trace ID 등을 둔다. 인증 헤더와 비밀번호, 전체 요청 본문을 기본 기록하지 않는다. **MDC — Mapped Diagnostic Context**는 로그 문맥에 값을 연결하는 도구이며 스레드 풀에서 정리하지 않으면 다음 요청으로 새어 나갈 수 있다.

**Trace**는 여러 서비스에 걸친 한 작업의 경로이고 **Span**은 그 안의 구간이다. trace ID와 업무 멱등 키는 목적이 다르다. 재시도마다 trace가 달라도 같은 업무 키일 수 있다. 외부 HTTP·메시지 경계로 추적 문맥을 전달할 설정이 필요하며 직접 만든 클라이언트가 Boot builder의 자동 계측을 우회하는지 확인한다.

샘플링 때문에 모든 요청의 trace가 저장되지는 않을 수 있다. 추적 정보가 없다는 이유로 요청이 없었다고 단정하지 않는다. 비용과 장애 분석 요구에 맞춰 샘플링·보존 정책을 정한다.

## 22.5 알림은 사용자가 겪는 문제와 연결한다

**SLI — Service Level Indicator**는 관측 지표, **SLO — Service Level Objective**는 그 목표다. 예를 들어 “유효한 예약 요청의 99%가 500ms 안에 완료”처럼 대상과 기간을 정한다. 숫자는 예시이며 실제 목표는 사용자 요구와 측정 결과로 선택한다.

CPU 80% 하나보다 지연·실패율·포화도와 함께 경보를 설계한다. 일시적인 스파이크마다 알림을 보내면 대응자가 지친다. 알림에는 영향, 확인할 대시보드, 완화 절차, 책임자를 연결한다.

## 실습: 장애 가설을 세운다

health가 UP이고 요청 지연이 증가한 가상 상황에서 세 가지 가설을 적는다. 풀 고갈, 외부 API 대기, GC 정지가 후보일 수 있다. 각각을 구분할 지표와 로그를 하나씩 고른다. 단순히 로그 레벨을 전부 DEBUG로 올리는 것보다 필요한 증거를 좁힌다.

## 확인 문제와 해설

**Q1. 평균 응답 50ms면 대부분 빠른가?** 긴 꼬리 지연이 가려질 수 있으므로 p95·p99와 표본 수를 함께 본다.

**Q2. 사용자 ID 태그는 왜 위험한가?** 사용자 수만큼 시계열 조합이 늘어 메모리·저장·쿼리 비용을 크게 만든다.

**Q3. health UP이 결제 성공을 보장하는가?** 검사 범위에 포함된 상태만 의미한다. 업무 성공률은 별도로 측정한다.

## 참고자료

- [Actuator endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)
- [Boot Metrics](https://docs.spring.io/spring-boot/reference/actuator/metrics.html)
- [Boot Tracing](https://docs.spring.io/spring-boot/reference/actuator/tracing.html)

---

[전체 목차](../index.md) · [← 이전 장](../21-testing/chapter.md) · [다음 장 →](../23-performance-concurrency/chapter.md)
