---
title: "11장. 비동기 데이터베이스 처리"
description: "이 장의 핵심은 await session.execute()라는 문법이 아니다. 요청마다 세션과 트랜잭션을 어떻게 소유하고 종료할지, 연결 풀이 꽉 찼을 때 어디에서 대기하는지, 실패한 업무를 어떻게 되돌릴지 설명하는 것이다. Knowledge Hub의 문서 등록 API를 비동기 DB로 구현하고 유일성 충"
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: false
part: 3
---

> PART 3 · 데이터베이스와 아키텍처

이 장의 핵심은 await session.execute()라는 문법이 아니다. 요청마다 세션과 트랜잭션을 어떻게 소유하고 종료할지, 연결 풀이 꽉 찼을 때 어디에서 대기하는지, 실패한 업무를 어떻게 되돌릴지 설명하는 것이다. Knowledge Hub의 문서 등록 API를 비동기 DB로 구현하고 유일성 충

[이 장 본문 읽기 →](./chapter.md)

[전체 학습 목차](../index.md)
