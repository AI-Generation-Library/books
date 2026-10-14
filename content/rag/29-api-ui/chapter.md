---
title: "29장. RAG API와 사용자 인터페이스"
description: "검색·질문·문서 관리 API의 경계를 정한다. 스트리밍·취소·오류와 출처 표시를 사용자 경험에 연결한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 29
part: 7
enableToc: true
---

# 29장. RAG API와 사용자 인터페이스

## 학습 목표

- 검색·질문·문서 관리 API의 경계를 정한다.
- 스트리밍·취소·오류와 출처 표시를 사용자 경험에 연결한다.

## 서비스의 계약

검색만 확인하는 /search와 최종 답변을 만드는 /query를 나누면 실패 원인을 분리하기 좋다. 문서 추가·수정·삭제는 관리자 권한의 별도 경로다. 질문 본문이 tenant나 권한을 지정하지 못하게 인증에서 얻은 Principal을 서버가 전달한다.

| 경로 | 역할 | 권한 |
| --- | --- | --- |
| POST /search | 허용 후보와 점수 확인 | reader/admin |
| POST /query | 근거 기반 답변 또는 거절 | reader/admin |
| POST /query/stream | 단계 상태와 검증 후 답변 SSE | reader/admin |
| PUT /documents | tenant 범위의 문서 교체 | admin |
| DELETE /documents/:id | 문서와 청크 삭제 | admin |
| GET /health | 프로세스 응답 확인 | 공개 |

기본 bearer 토큰은 가상 데이터·localhost 실습용이다. 실제 계정 관리·서명 토큰 검증·조직 인증 제공자를 구현한 서비스가 아니다. 공개 배포 전 인증과 비밀 주입을 교체해야 한다.

## 입력과 오류

질문 길이·검색 mode·limit·문서 ID·역할·본문 길이를 검사하고 알 수 없는 필드를 거부한다. 입력 타입 검사가 인증·인가는 아니다. 대용량 요청은 애플리케이션 값 검사 이전의 프록시/ASGI 요청 바이트 제한도 필요하다.

401·403·422·400·502를 서로 다른 실패로 처리한다. 모델 연결 오류의 내부 주소·스택·비밀을 그대로 반환하지 않는다. 응답에 request ID를 붙여 내부 진단과 연결한다. 입력과 답변 전체를 기본 로그에 무조건 저장하지 않는다.

## 스트리밍의 실제 의미

토큰이 생성될 때마다 즉시 표시하면 빠르게 느껴질 수 있지만 아직 검증하지 않은 주장이 먼저 노출될 수 있다. 예제 SSE는 retrieving 상태를 먼저 보내고 답변·인용 검사가 끝난 후 완성 결과를 보낸다. 모델 토큰을 실시간 전달한 구현으로 표시하지 않는다.

클라이언트가 연결을 끊었다고 동기 스레드의 모델 호출이 자동 취소되는 것은 아니다. 모델 API의 취소 지원·기한·대기 수·동시 실행 수를 따로 관리한다. UI의 120초 기한과 모델 HTTP 읽기 기한 90초는 서로 다른 계층이다.

## 화면에 무엇을 보여 줄까

기본 화면은 질문·답변·모드·거절·출처·버전·문자 범위를 표시한다. source와 모델 답변을 textContent로 넣어 HTML로 실행하지 않는다. 토큰은 브라우저 저장소에 보관하지 않는다. 가상 문서 출처는 실제 링크인 척하지 않고 텍스트로 보여 준다.

모델 점수를 확신도 퍼센트로 바꾸지 않는다. 거절 이유는 사용자가 자료가 부족한지 요청이 실패했는지 이해할 수 있게 하되 비인가 문서의 존재를 드러내지 않는다. 사용자에게 유용한 출처 확인과 피드백 경로를 제공한다.

## 실습과 평가

`python serve.py`로 localhost:8000을 열고 reader-local-token으로 질문한다. 기본 화면은 발췌 데모라고 명시한다. 실제 모델 모드는 예제 README의 환경 변수를 사용한다.

API 테스트는 인증·스키마·권한·문서 교체/삭제·SSE를 확인한다. 실제 브라우저 화면의 시각·접근성 QA와 공개 TLS 배포는 별도 검증 범위다.

## 확인 문제

SSE로 첫 상태 메시지를 보냈으니 LLM 토큰 스트리밍과 동일한 지연 특성을 갖는가?

[해설](../appendices/answers.md#장-29)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Tutorial - User Guide - FastAPI](https://fastapi.tiangolo.com/tutorial/)
- [Custom Response - HTML, Stream, File, others - FastAPI](https://fastapi.tiangolo.com/advanced/custom-response/)
- [HTML Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

[이전 장](../28-experiments/chapter.md) · [책 목차](../index.md) · [다음 장](../30-index-lifecycle/chapter.md)
