---
title: "40장. 품질 개선부터 배포와 운영 검증까지"
description: "실제로 실행한 검사와 아직 확인하지 않은 범위를 남긴다. 품질 회귀·데이터 수명·운영 복구를 기여 기록으로 연결한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 40
part: 9
enableToc: true
---

# 40장. 품질 개선부터 배포와 운영 검증까지

## 학습 목표

- 실제로 실행한 검사와 아직 확인하지 않은 범위를 남긴다.
- 품질 회귀·데이터 수명·운영 복구를 기여 기록으로 연결한다.

## 검증 결과의 층위

코드 문법·단위/통합 테스트·실제 모델 smoke·평가 지표·공개 배포·사람 검수는 서로 다른 증거다. 한 층위의 성공을 다른 층위의 성공으로 바꾸어 기록하지 않는다. appendix verification과 기계 판독 결과가 실제 집필 검증의 원본이다.

기본 테스트는 문서·벡터·순위·인용·권한·삭제·API·파서를 검사한다. 신경망 실험은 작은 가상 질문에서 BM25·dense·hybrid를 비교한다. 리랭커와 로컬 생성 모델은 제한된 한국어 질문으로 실제 연결을 확인한다. 프레임워크는 검색 어댑터만 검증한다.

## 실패를 보존하는 보고

dense가 BM25보다 낮은 dev 순위도 그대로 남겼다. 작은 test 점수가 높다고 실서비스 정확도를 주장하지 않는다. 인용 부분 문자열 검사가 의미적 오답을 통과시키는 한계도 테스트와 응답에 표시한다. 데이터와 평가 코드가 공개되어야 다음 기여자가 같은 조건을 재현할 수 있다.

문서 수정·삭제·권한 회수는 품질 평균과 별도의 중단 기준이다. 실제 새 인덱스를 도입할 때도 이러한 회귀를 먼저 확인한다. 캐시·요약·그래프를 추가하면 파생 데이터의 삭제·인가 테스트를 확장한다.

## 배포 전 추가 검증

TLS·운영 인증·요청 바이트 제한·비밀 주입·모델 자원·대기열·기한·백업 복원을 실제 환경에서 확인한다. 컨테이너가 있다면 대상 OS·CPU/GPU·파일 권한·종료 신호·모델 캐시 수명을 시험한다. 코드 파일이 존재하는 것과 운영이 검증된 것은 다르다.

장애 실험에서는 모델 중단·색인 쓰기 실패·부분 갱신·권한 변경·느린 질의·디스크 부족을 테스트 전용 데이터로 재현한다. 복구 후 오래된 근거와 비인가 내용이 남지 않는지 확인한다. 임베딩만 백업하고 원본·메타데이터·권한·모델 revision을 잃으면 재현이 어렵다.

## 기여 결과로 정리

Markdown 원고·book.json·승인 목차·공식 자료·예제 소스·의존성 lock·검증 기록·다운로드를 함께 제출한다. 모델 가중치·운영 문서·접속 비밀·실행 DB·업로드·가상환경은 포함하지 않는다. 정확한 저작 모델을 확인하지 못했다면 추측해 적지 않는다.

저장소 메타데이터 검사는 책 경로·목차·출처 형식을 확인한다. 기술 설명과 모델 품질의 전체 검수를 대신하지 않는다. PR에는 대상 독자·범위·실제 명령·실행 결과·미검증 영역을 명시하고 이후 개선이 필요한 부분을 숨기지 않는다.

## 실습과 평가

기본 테스트·CLI 평가·실제 모델 선택 실습을 자신의 환경에서 재현한다. 저장소 루트의 `python scripts/validate-books.py`와 책의 링크·다운로드 검사를 수행한다.

결과를 추가할 때는 OS·패키지·모델 digest·문서 snapshot·질문 split·실제 출력·기준 날짜를 기록하고 메타데이터·ZIP도 함께 갱신한다. 전체 사람 검수를 수행하지 않았다면 그대로 명시한다.

## 확인 문제

검색 점수와 테스트가 모두 좋으므로 공개 배포·보안·사람 검수도 완료라고 표시해도 되는가?

[해설](../appendices/answers.md#장-40)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [unittest — Unit testing framework — Python 3.15.0 documentation](https://docs.python.org/3/library/unittest.html)
- [Pull requests - GitHub Docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)

---

[이전 장](../39-capstone-pipeline/chapter.md) · [책 목차](../index.md)
