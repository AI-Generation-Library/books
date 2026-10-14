---
title: "31장. 접근 권한과 RAG 보안"
description: "검색·리랭킹·생성·로그에 같은 권한 경계를 적용한다. 문서 속 지시와 도구 권한을 분리한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 31
part: 7
enableToc: true
---

# 31장. 접근 권한과 RAG 보안

## 학습 목표

- 검색·리랭킹·생성·로그에 같은 권한 경계를 적용한다.
- 문서 속 지시와 도구 권한을 분리한다.

## 검색 후 필터만으로 부족하다

비인가 문서를 검색한 뒤 최종 답변에서만 지우면 이미 외부 리랭커·모델·로그에 내용이 전달되었을 수 있다. 인증된 tenant·roles로 후보를 먼저 제한하고 각 파생 단계도 같은 경계를 유지한다. 사용자 질문에 적힌 역할과 tenant를 서버 권한으로 사용하지 않는다.

예제의 Store.authorized는 tenant를 DB에서 제한한 뒤 역할을 확인해 허용 청크만 반환한다. 임베딩 점수·RRF·리랭커·컨텍스트는 그 집합만 받는다. 다른 tenant와 관리자 문서는 reader 검색 결과에 들어가지 않는 테스트가 있다.

## 프롬프트 주입

문서에 도구 실행·비밀 공개·정책 변경 지시가 들어갈 수 있다. 시스템 프롬프트가 이를 데이터로 구분하도록 돕지만 완벽한 보안 장치로 보지 않는다. 모델에 권한 밖 정보를 주지 않고 도구의 서버 측 인가·허용 작업·기한·결과 크기를 제한한다.

기본 생성 모델은 셸·파일·네트워크 도구를 호출할 수 없다. 나중에 Agentic RAG를 붙이면 도구 경계가 새로 생긴다. 읽기 검색 권한과 외부 전송·업무 변경 권한을 분리한다. 모델의 자연어 승인이나 문서 속 명령으로 권한을 부여하지 않는다.

## 캐시와 대화도 데이터 전달이다

동일 질문이라도 사용자 권한에 따라 답이 다르다. 질문 문자열만 캐시 키로 쓰면 관리자 답변이 reader에게 갈 수 있다. tenant·사용자/역할·권한 revision·문서 snapshot·모델/프롬프트를 반영하고 권한 회수와 삭제에 맞춰 무효화한다. 예제는 결과 캐시를 기본 구현하지 않는다.

로그·trace·평가 데이터에도 근거 텍스트와 개인정보가 들어갈 수 있다. 기본 로그는 요청 ID·메서드·상태·시간만 남긴다. 디버그 기록을 켤 때는 저장 범위·마스킹·접근·보관·삭제를 설계하고 외부 관측 서비스 전송을 검토한다.

## 입력과 외부 시스템

문서 업로드·URL 수집·PDF 파싱에는 크기·페이지·형식·기한 제한을 둔다. 파일 파서 취약점과 리소스 고갈을 고려해 필요하면 격리된 처리 환경을 사용한다. 현재 관리자 API는 JSON 문서만 받고 임의 URL을 내려받지 않는다.

실습 토큰은 가상 자료 localhost용이다. 실제 배포에서는 인증 제공자·토큰 만료·조직 관계·감사·비밀 주입을 갖춘다. 브라우저에 관리자 토큰을 저장하거나 공개 예제의 문자열을 실제 자격 증명으로 쓰지 않는다.

## 실습과 평가

관리자 전용 코드 질의를 reader와 admin으로 실행해 차이를 확인한다. 비인가 후보가 리랭커에 전달되지 않는 테스트도 함께 실행한다.

문서 삭제·권한 회수가 생성 중 발생할 때 답변이 차단되는지 본다. 이번 테스트는 포괄적인 침투 시험이나 모든 프롬프트 주입 공격에 대한 방어 인증이 아니다.

## 확인 문제

관리자와 reader가 같은 질문을 했으니 답변 캐시를 공유해도 되는가?

[해설](../appendices/answers.md#장-31)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [LLM Prompt Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [Authorization - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Security - FastAPI](https://fastapi.tiangolo.com/tutorial/security/)

---

[이전 장](../30-index-lifecycle/chapter.md) · [책 목차](../index.md) · [다음 장](../32-latency-cost/chapter.md)
