---
title: "30장. Docker와 실행 환경 구성"
description: "이미지·설정·영속 데이터를 분리한다. 개발 Compose와 실제 운영의 보장 범위를 구분한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 30
part: 7
enableToc: true
---

# 30장. Docker와 실행 환경 구성

## 학습 목표

- 이미지·설정·영속 데이터를 분리한다.
- 개발 Compose와 실제 운영의 보장 범위를 구분한다.

## 실행 환경을 이미지로 표현하기

Docker 이미지는 런타임·의존성·소스를 묶는다. 호스트의 `node_modules`를 복사하는 대신 Linux 이미지 안에서 잠금 파일로 설치한다. 네이티브 의존성은 OS와 CPU 아키텍처의 영향을 받는다. `.dockerignore`로 의존성 디렉터리·비밀파일·진단 산출물을 빌드 문맥에서 제외한다.

```dockerfile
FROM node:24.18.0-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts && mkdir -p /app/var/uploads && chown node:node /app/var/uploads
COPY --chown=node:node src ./src
COPY --chown=node:node migrations ./migrations
ENV NODE_ENV=production HOST=0.0.0.0
USER node
EXPOSE 3000
CMD ["node", "src/main.mjs"]
```

[실행 파일](../examples/Dockerfile)

Dockerfile의 이미지는 이 책의 로컬 Node.js 패치와 맞춘 기준점이다. 실제 운영에 올리기 전에는 지원되는 최신 보안 패치와 이미지 취약점을 확인하고, 검증한 이미지 digest를 고정하는 방식을 검토한다. 정확한 태그를 적는 것과 최신 보안 상태를 유지하는 것은 별개 작업이다.

## 의존성 설치와 실행 권한

실행 이미지에는 개발 의존성을 생략한다. 이 프로젝트는 JavaScript를 직접 실행하므로 별도 TypeScript 빌드가 필요 없다. TypeScript 소스를 배포하는 다른 프로젝트라면 빌드 단계에서 컴파일러를 사용하고 결과와 실행 의존성만 다음 단계로 가져오는 multi-stage 구성을 검토한다.

서버를 root가 아닌 `node` 사용자로 실행하고 쓰기가 필요한 업로드 폴더만 준비한다. 컨테이너가 있다고 파일 권한·비밀정보·네트워크 정책이 자동으로 해결되지는 않는다. 외부 접속 주소와 포트 바인딩도 명시한다.

## Compose의 서비스 경계

예제 Compose는 PostgreSQL·Redis·초기화 작업·API·worker를 나눈다. DB와 Redis가 healthy가 된 뒤 마이그레이션을 실행하고, 그 성공 이후 애플리케이션을 시작한다. 시작 순서가 런타임 장애 복구를 보장하지는 않으므로 연결 실패 처리는 계속 필요하다.

`localhost`는 각 컨테이너 자신을 가리킨다. API에서 DB에 연결할 때는 Compose 서비스 이름 `postgres`를 사용한다. 호스트에서 별도 통합 테스트를 할 때는 공개한 로컬 포트를 사용한다. 같은 주소를 두 환경에서 그대로 복사하면 연결이 실패할 수 있다.

## 데이터의 수명

DB·Redis·업로드를 named volume에 둔다. 컨테이너를 새로 만든다고 데이터를 지우지 않는 구조지만, 볼륨 자체의 삭제·호스트 장애·백업 복구는 별개다. `docker compose down -v`는 데이터를 지울 수 있으므로 단순 종료 명령으로 안내하지 않는다. 일반 정지는 `docker compose down`을 사용한다.

Compose의 접속 비밀번호는 로컬 개발 전용 예시다. DB·Redis 호스트 포트도 127.0.0.1에만 바인딩한다. 운영에서는 비밀 주입·TLS·접근 제어·백업·보관 정책을 새로 설계한다. Compose 파일에 `MODE=production`이라고 적었다고 공개 서비스 준비가 끝난 것은 아니다.

## 실습과 관찰

Docker가 준비된 환경에서는 `docker compose config --quiet`로 구성을 확인한 뒤 `docker compose up --build -d`와 `npm run smoke`를 실행한다. 로그 확인은 `docker compose logs api worker`, 정지는 `docker compose down`이다.

이번 집필 환경은 Docker Desktop 엔진이 시작되지 않아 이미지 빌드·컨테이너 실행·볼륨 권한 검증을 수행하지 못했다. 문법 검사와 실제 실행 결과는 [검증 기록](../appendices/verification.md)에서 구분한다.

## 확인 문제

호스트 Node.js에서 설치한 node_modules를 Linux 컨테이너로 복사하면 항상 동일하게 실행되는가?

[해설 보기](../appendices/answers.md#장-30)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Node.js language-specific guide | Docker Docs](https://docs.docker.com/guides/nodejs/)
- [Control startup and shutdown order in Compose | Docker Docs](https://docs.docker.com/compose/how-tos/startup-order/)
- [Volumes | Docker Docs](https://docs.docker.com/engine/storage/volumes/)

---

[이전 장](../29-resilience/chapter.md) · [책 목차](../index.md) · [다음 장](../31-cicd/chapter.md)
