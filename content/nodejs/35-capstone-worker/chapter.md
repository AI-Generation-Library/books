---
title: "35장. 업로드·작업 큐·실시간 알림 연결"
description: "outbox·큐·worker·조회 흐름을 연결한다. 중복 실행과 재연결의 결과를 검증한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 35
part: 8
enableToc: true
---

# 35장. 업로드·작업 큐·실시간 알림 연결

## 학습 목표

- outbox·큐·worker·조회 흐름을 연결한다.
- 중복 실행과 재연결의 결과를 검증한다.

## 전달과 실행은 다른 단계

outbox에 행이 있다고 worker가 실행 중이라는 뜻은 아니다. dispatcher는 미전달 의도를 읽고 큐에 추가하며, worker가 메시지를 가져가 분석한다. 작업이 completed로 바뀐 뒤 사용자 조회가 그 결과를 읽는다. 단계별 지연을 관찰해야 어디서 막혔는지 알 수 있다.

실제 파일은 `queue.mjs`·`bull-queue.mjs`·`files.mjs`·`worker.mjs`다. dispatcher는 비동기 타이머 중첩을 피하고 종료 시 실행 중 전달을 기다린다. producer 연결은 빠른 실패를, worker 연결은 지속적인 큐 소비를 고려한 정책을 사용한다.

## 텍스트 분석의 경계

worker는 UUID 파일을 스트림으로 읽는다. TextDecoder가 청크 사이의 미완성 UTF-8을 보관하고 마지막 flush에서 남은 오류를 검사한다. 각 청크에서 코드포인트와 LF를 세며 마지막 줄의 개행 여부를 반영한다. 입력 전체를 배열로 모으지 않는다.

코드포인트 계산은 텍스트 청크를 순회한다. 파일 크기 제한이 있어 계산량도 제한되지만, 큰 압축 해제나 복잡한 문서 파싱으로 확장하면 CPU 분리·폭발적 결과 크기·최종 분석 기한을 다시 설계해야 한다. 파일 I/O가 비동기라는 이유로 모든 변환이 비차단인 것은 아니다.

## 중복 소비와 결과 보존

이미 completed면 다시 분석하지 않는다. 동시에 중복 처리되더라도 입력 파일이 변하지 않고 계산이 결정적이라는 전제에서 같은 결과를 저장한다. 업데이트 조건은 완료 결과를 failed로 덮지 않게 한다. 이 예제는 실행 횟수가 반드시 한 번이라는 보장을 하지 않는다.

업무가 외부 전송처럼 비가역 부수 효과를 포함하면 별도 멱등 설계가 필요하다. 파일도 처리 중에 바뀌지 않도록 UUID별 불변 저장을 유지한다. 운영에 삭제 기능을 추가하면 재시도·큐 보관 기한과 파일 보관 정책을 맞춰야 한다.

## 상태를 사용자에게 보여 주기

GET은 현재 상태를 읽고 SSE는 일정 시간 최신 상태를 계속 전송한다. 상태 변화 이력을 모두 저장하지 않으므로 빠르게 지나간 processing을 클라이언트가 못 볼 수 있다. 최종 결과가 일관되고 접근 권한이 유지되는 것이 현재 계약이다.

worker가 실패하면 BullMQ 재시도 정책에 따라 retrying 또는 failed를 기록한다. 큐·DB 장애에 따라 상태 기록 자체가 실패할 수 있다. 오랫동안 processing인 작업과 큐 상태를 대조하는 운영 점검이 필요하다. 단순 UI 상태만으로 실제 소비 중 여부를 완벽하게 추론하지 않는다.

## 전용 통합 검증

실제 PostgreSQL·Redis 테스트는 사용자·작업·파일을 만들고 outbox 전달과 worker 결과를 확인한다. 생성한 데이터만 정리하고 전용 서비스에서 실행한다. 실행 환경이 없다면 skip을 명시한다. 메모리 구현 통과를 실제 큐 실행 성공으로 바꾸어 기록하지 않는다.

## 실습과 관찰

`npm test`로 기본 흐름과 멱등성·전달 실패를 검사한다. 실제 서비스 통합은 `NODEBOOK_INTEGRATION=1`과 DB·Redis 주소를 설정해 `npm run test:integration`으로 실행한다. 구체적인 PowerShell 명령은 프로젝트 안내를 따른다.

worker를 중단한 동안 접수한 작업이 큐에 쌓이고 다시 시작한 뒤 처리되는지 확인하는 실험은 별도 장애 시험이다. 이번 집필에서 실행하지 않은 장애 주입까지 완료로 기록하지 않았다.

## 확인 문제

같은 작업이 중복 처리되어도 문자 통계는 안전했다. 이메일 발송 작업도 그대로 바꾸어 넣어도 되는가?

[해설 보기](../appendices/answers.md#장-35)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Workers | BullMQ](https://docs.bullmq.io/guide/workers)
- [Util | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/util.html)
- [HTML Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

[이전 장](../34-capstone-api/chapter.md) · [책 목차](../index.md) · [다음 장](../36-capstone-validation/chapter.md)
