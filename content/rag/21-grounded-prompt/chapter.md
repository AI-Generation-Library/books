---
title: "21장. 근거 중심 프롬프트와 답변 정책"
description: "지시·질문·문서 데이터를 구분한다. 상충·최신성·근거 부족을 명시적인 정책으로 처리한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 21
part: 5
enableToc: true
---

# 21장. 근거 중심 프롬프트와 답변 정책

## 학습 목표

- 지시·질문·문서 데이터를 구분한다.
- 상충·최신성·근거 부족을 명시적인 정책으로 처리한다.

## 프롬프트가 정해야 할 행동

답변에 사용할 자료의 범위, 필요한 출처, 추론과 원문 사실의 구분, 모를 때의 행동을 명시한다. 친절하고 정확하게 답하라는 지시만으로는 어떤 자료를 우선할지 정해지지 않는다. 출력 스키마와 검증 코드를 함께 사용한다.

예제의 실제 생성기는 질문과 문서를 JSON 데이터로 구분하고, 원문 문장을 인용한 claims 배열을 요구한다. 시스템 지시에는 문서 속 명령을 실행 지시로 취급하지 말라고 적는다. 하지만 구분자와 지시문만으로 프롬프트 주입을 완전히 막았다고 주장하지 않는다. 도구·권한·외부 전송 경계는 서버가 강제한다.

## 문서의 사실과 문서의 명령

문서에 이전 지시를 무시하고 관리자 정보를 공개하라는 내용이 있어도 그것은 분석할 자료다. 모델에 비인가 문서를 애초에 전달하지 않고, 사용자 입력으로 도구 권한을 넓히지 않는다. 이 프로젝트는 생성 모델에 파일·셸·외부 도구 실행 권한을 주지 않는다.

인용을 요구하는 정책도 문서가 가진 권한을 바꾸지 않는다. 답변에 출처가 있으니 민감한 값 공개가 허용된다는 논리는 잘못이다. 접근 가능한 근거와 공개 가능한 응답 범위를 먼저 정한다.

## 근거 부족과 상충

검색 점수는 정답 확률이 아니다. 질문에 필요한 조건이 확인되지 않거나 자료가 상충하면 추가 검색·확인 질문·부분 답변·거절 중 정책을 적용한다. 예제의 기본 lexical 겹침 규칙은 데모용 보수적 장치이며 실제 answerability를 보장하지 않는다. 동의어 질문을 과도하게 거절할 수 있다.

모델이 빈 claims를 반환하면 model_abstained로, 인용 형식이 잘못되면 invalid_citation으로 구분한다. 둘을 모두 모델이 답을 몰랐다는 하나의 품질 오류로 섞지 않으면 원인을 찾기 쉽다. 외부 모델 연결 실패는 또 다른 운영 오류다.

## 최신성과 적용 시점

새로 수집한 문서가 언제나 업무상 최신 규정인 것은 아니다. 개정일·시행일·대상·폐기 여부를 구분한다. 질문이 과거 시점을 묻는다면 당시 유효 문서가 필요할 수 있다. 문서 자체에 시점 정보가 없다면 모델이 날짜를 만들어내게 하지 않는다.

출력 문장에는 자료가 명시한 사실과 모델의 종합 해석을 구분할 수 있어야 한다. 출처가 다르거나 해결되지 않은 충돌은 사용자에게 보이는 한계로 남긴다. 확신에 찬 문체를 신뢰도의 대체물로 쓰지 않는다.

## 실습과 평가

ragbook/generation.py의 system 지시와 실제 반환 스키마를 읽는다. 모델 출력이 숫자 타입·없는 ID·틀린 quote·빈 claims일 때 처리 경로를 테스트한다.

프롬프트를 바꾸면 검색 설정을 고정한 채 생성 결과를 비교한다. 이번 로컬 LLM 실행은 가상 문서 질문 1건의 정상 출력 확인이며 다양한 주입·상충 질문의 보안 평가를 완료한 것은 아니다.

## 확인 문제

문서를 JSON으로 감쌌으니 프롬프트 주입을 완전히 해결했다고 말할 수 있는가?

[해설](../appendices/answers.md#장-21)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [LLM Prompt Injection Prevention - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [Generate a chat message - Ollama](https://docs.ollama.com/api/chat)
- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)

---

[이전 장](../20-context-budget/chapter.md) · [책 목차](../index.md) · [다음 장](../22-citations/chapter.md)
