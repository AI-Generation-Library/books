---
title: "14장. TypeScript와 유지보수 가능한 프로젝트 구조"
description: "타입 검사와 런타임 검증의 책임을 구분한다. 외부 의존성을 교체할 수 있는 경계를 만든다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 14
part: 3
enableToc: true
---

# 14장. TypeScript와 유지보수 가능한 프로젝트 구조

## 학습 목표

- 타입 검사와 런타임 검증의 책임을 구분한다.
- 외부 의존성을 교체할 수 있는 경계를 만든다.

## 타입이 도와주는 범위

TypeScript는 개발 중 잘못된 속성 접근과 함수 계약 불일치를 찾는 데 도움을 준다. 네트워크에서 받은 JSON이 타입 선언과 일치하는지 자동으로 검사하지는 않는다. `as User`는 검증 함수가 아니므로 입력 경계에는 별도 검증이 필요하다.

```ts
export type JobState = 'queued' | 'processing' | 'completed' | 'failed';
export interface Job { id: string; ownerId: string; state: JobState }
export interface JobRepository { find(id: string): Promise<Job | null> }
export class JobService {
  constructor(private readonly repository: JobRepository) {}
  async ownedJob(id: string, userId: string): Promise<Job | null> {
    const job = await this.repository.find(id);
    return job?.ownerId === userId ? job : null;
  }
}
```

[실행 파일](../examples/typescript/job-service.ts)

서비스는 저장소 인터페이스만 안다. 실제 DB 드라이버와 메모리 Map 중 무엇을 쓰는지는 조립 단계에서 정한다. 인터페이스를 너무 잘게 나누거나 모든 함수 앞에 계층을 추가하면 오히려 읽기 어려워진다. 교체가 필요한 외부 자원과 업무 규칙의 경계부터 분리한다.

## 이 책의 JavaScript와 TypeScript 예제

종합 프로젝트는 Node.js 자체 실행을 쉽게 확인하도록 `.mjs`를 사용한다. 타입 설계는 `typescript/job-service.ts`에서 독립적으로 검증한다. `npm run typecheck`는 이 TypeScript 예제의 검사이며 종합 프로젝트 전체를 TypeScript로 검사했다고 주장하지 않는다.

Node.js 24에는 일부 TypeScript 구문을 제거해 실행하는 기능이 있지만 타입 검사와 동일하지 않다. 모든 TypeScript 변환 기능이나 `tsconfig`의 경로 별칭을 그대로 지원하는 것도 아니다. 예제의 생성자 parameter property처럼 변환이 필요한 구문을 타입 제거만으로 실행하는 흐름으로 설명하면 안 된다. 이 파일은 `tsc --noEmit` 검사 대상으로 제공한다.

## 의존 방향과 조립

```text
main → 설정·자원 생성 → createApp
                       ├─ 인증 정책
                       ├─ 파일 저장 함수
                       └─ 저장소 인터페이스 → memory 또는 PostgreSQL
dispatcher → outbox → queue → worker → 파일 분석 → 결과 저장
```

HTTP 상태 코드 선택은 전송 계층의 책임이고, 소유권과 상태 전이 규칙은 서비스 정책이다. SQL과 재시도는 저장소·작업 계층에 둔다. 예제는 크기를 줄이기 위해 일부 정책을 앱 함수 안에 두었다. 서비스가 커질 때는 테스트로 동작을 고정한 뒤 추출할 수 있다.

## 설정은 시작할 때 검증한다

설정 객체는 문자열 환경 변수를 파싱한 결과다. 필수 DB 주소가 없거나 포트가 숫자가 아니면 시작 단계에서 실패한다. 서버가 트래픽을 받기 시작한 뒤에야 설정 누락을 발견하는 것보다 복구와 진단이 쉽다. 비밀정보를 설정 오류 메시지 전체에 출력하지 않는다.

모듈 전역 싱글턴은 편하지만 테스트 간 상태를 공유하게 만들 수 있다. 테스트마다 새 저장소·새 임시 디렉터리·새 서버를 생성하고 종료한다. 전역 상태를 하나씩 초기화하는 방법보다 소유권이 명확하다.

## 실습과 관찰

`npm run typecheck`를 실행한다. `JobState`에 없는 문자열을 반환하도록 바꿔 타입 오류를 확인한 뒤 복구한다. 다음에는 `src/runtime.mjs`에서 모드별 저장소 선택을 찾는다.

메모리 저장소와 PostgreSQL 저장소가 같은 메서드를 제공하더라도 트랜잭션·경쟁·장애 특성은 다르다. 대체 구현 테스트가 실제 DB 통합 검증을 대신하지 않는다는 점을 17장과 검증 안내에서 확인한다.

## 확인 문제

JSON을 읽은 뒤 as Job을 붙였으므로 state가 올바르다고 믿을 수 있는가?

[해설 보기](../appendices/answers.md#장-14)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Modules: TypeScript | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/typescript.html)
- [TypeScript: Documentation - Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript: TSConfig Option: module](https://www.typescriptlang.org/tsconfig/module.html)

---

[이전 장](../13-rest-api/chapter.md) · [책 목차](../index.md) · [다음 장](../15-testing/chapter.md)
