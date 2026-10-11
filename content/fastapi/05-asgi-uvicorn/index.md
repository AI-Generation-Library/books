---
title: "05장. ASGI와 Uvicorn의 내부 구조"
description: "HTTP 요청이 네트워크 바이트에서 Python 함수 호출이 되고 다시 응답으로 나가는 과정을 설명한다. ASGI의 세 인자를 직접 사용하고, HTTP 요청 수명과 TCP 연결 수명, lifespan의 차이를 구분한다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: false
part: 2
---

> PART 2 · FastAPI 내부 동작 원리

HTTP 요청이 네트워크 바이트에서 Python 함수 호출이 되고 다시 응답으로 나가는 과정을 설명한다. ASGI의 세 인자를 직접 사용하고, HTTP 요청 수명과 TCP 연결 수명, lifespan의 차이를 구분한다.

[이 장 본문 읽기 →](./chapter.md)

[전체 학습 목차](../index.md)
