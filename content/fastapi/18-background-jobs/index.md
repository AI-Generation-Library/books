---
title: "18장. 백그라운드 작업과 메시지 큐"
description: "Knowledge Hub에 대용량 문서가 업로드되면 파싱, 임베딩 생성, 색인 등록이 이어진다. 요청을 2분 동안 붙잡아 두면 프록시 timeout과 사용자 재시도가 섞이고 같은 문서가 두 번 처리될 수 있다. 빠르게 작업 ID를 반환하고 별도 worker가 수행하면 사용자 요청의 수명과 작업의 수명을 "
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: false
part: 5
---

> PART 5 · 실무 API와 테스트

Knowledge Hub에 대용량 문서가 업로드되면 파싱, 임베딩 생성, 색인 등록이 이어진다. 요청을 2분 동안 붙잡아 두면 프록시 timeout과 사용자 재시도가 섞이고 같은 문서가 두 번 처리될 수 있다. 빠르게 작업 ID를 반환하고 별도 worker가 수행하면 사용자 요청의 수명과 작업의 수명을 

[이 장 본문 읽기 →](./chapter.md)

[전체 학습 목차](../index.md)
