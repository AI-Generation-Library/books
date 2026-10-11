---
title: "FastAPI 완전 정복"
description: "FastAPI 완전 정복의 보충 학습 자료와 실습 안내."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
---

**Python 비동기 프로그래밍부터 REST API 설계, 데이터베이스, 인증, 성능 최적화, AI 서비스 운영까지**

이 책은 백엔드 개발 경험이 있는 독자가 FastAPI로 서비스를 만들고, 요청이 지연되거나 데이터가 꼬였을 때 원인을 설명할 수 있도록 쓴 실습형 기술서다. 제공받은 7부·30장 목차를 바탕으로 개념, 내부 동작, 실행 예제, 설계 판단, 실패 사례와 확인 문제를 함께 담았다.

처음에는 작은 문서 API를 만든다. 이후 비동기 실행 구조와 데이터 저장, 보안, 외부 시스템 연동, 운영을 학습하고 문서 기반 AI 서비스 **Knowledge Hub**로 확장한다. 각 장의 실습은 별도 작업 폴더에서 실행하는 독립 예제다. 여러 장의 `main.py`를 순서대로 붙이면 하나의 애플리케이션이 된다는 뜻은 아니다. 통합 실행판은 [29장 프로젝트](29-capstone/project/README.md)에 있다.

## 읽기 전에

- [머리말과 실습 기준](00-preface.md)
- [학습 로드맵](appendices/learning-roadmap.md)
- [용어 사전](appendices/glossary.md)
- [코드 검증 범위](appendices/verification.md)

## PART 1. FastAPI 시작하기

1. [FastAPI란 무엇인가?](01-fastapi-introduction/chapter.md)
2. [개발 환경 구성](02-development-environment/chapter.md)
3. [첫 번째 REST API 개발](03-first-rest-api/chapter.md)
4. [Pydantic과 데이터 검증](04-pydantic-validation/chapter.md)

## PART 2. FastAPI 내부 동작 원리

5. [ASGI와 Uvicorn의 내부 구조](05-asgi-uvicorn/chapter.md)
6. [Python asyncio와 이벤트 루프](06-asyncio-event-loop/chapter.md)
7. [FastAPI의 동시성 처리](07-concurrency/chapter.md)
8. [의존성 주입과 미들웨어](08-dependencies-middleware/chapter.md)

## PART 3. 데이터베이스와 백엔드 아키텍처

9. [FastAPI 프로젝트 아키텍처](09-project-architecture/chapter.md)
10. [SQLAlchemy와 ORM](10-sqlalchemy-orm/chapter.md)
11. [비동기 데이터베이스 처리](11-async-database/chapter.md)
12. [Redis와 캐싱 전략](12-redis-cache/chapter.md)

## PART 4. 인증, 보안, 예외 처리

13. [인증과 인가](13-authentication/chapter.md)
14. [예외 처리와 오류 응답](14-errors/chapter.md)
15. [API 보안](15-api-security/chapter.md)

## PART 5. 실무 API 개발과 테스트

16. [HTTP 클라이언트와 외부 API 연동](16-http-clients/chapter.md)
17. [실시간 통신과 스트리밍](17-streaming/chapter.md)
18. [백그라운드 작업과 메시지 큐](18-background-jobs/chapter.md)
19. [FastAPI 테스트 전략](19-testing/chapter.md)

## PART 6. 성능 최적화와 서비스 운영

20. [FastAPI 성능 측정](20-performance-measurement/chapter.md)
21. [FastAPI 성능 최적화](21-optimization/chapter.md)
22. [Docker와 배포 아키텍처](22-docker-deployment/chapter.md)
23. [로깅과 모니터링](23-observability/chapter.md)
24. [운영 장애와 고급 동시성](24-incidents-concurrency/chapter.md)

## PART 7. FastAPI를 활용한 AI 서비스 개발

25. [FastAPI와 LLM API](25-llm-api/chapter.md)
26. [RAG 서비스 백엔드 구축](26-rag/chapter.md)
27. [AI Agent 서버 구축](27-ai-agents/chapter.md)
28. [AI 서비스 성능과 확장성](28-ai-scalability/chapter.md)
29. [실전 프로젝트: RAG 기반 AI Agent 플랫폼](29-capstone/chapter.md)
30. [실전 아키텍처 설계와 기술 면접](30-architecture-interview/chapter.md)

각 장은 해당 번호의 폴더 안에 `chapter.md`로 저장했다. Markdown을 지원하는 편집기로 이 파일을 열면 목차에서 각 장으로 이동할 수 있다.
