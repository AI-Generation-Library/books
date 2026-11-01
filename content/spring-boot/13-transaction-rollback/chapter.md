---
title: "13장. 롤백 규칙과 프록시 함정"
description: "RuntimeException·checked exception·rollbackFor·예외 삼키기·rollback-only·자기 호출을 실패 재현 테스트로 구분한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 13
part: 3
enableToc: true
---

> PART 3. 영속성과 트랜잭션

## 도입: 오류 메시지는 떴지만 데이터는 저장됐다

파일 저장 실패로 IOException이 발생했다. 호출자는 실패를 받았는데 앞서 작성한 DB 행은 남았다. 또 다른 코드에서는 RuntimeException이 발생했지만 catch 후 정상 DTO를 반환하자 commit됐다. “예외가 났다”는 사실만으로 롤백 결과를 예측할 수 없다. **어떤 예외가 어느 경계를 빠져나갔는가**를 봐야 한다.

## 13.1 기본 규칙과 명시적 변경

이 책의 기본 선언형 설정에서는 `RuntimeException`과 `Error`가 트랜잭션 경계 밖으로 전파되면 롤백 대상이고 checked exception은 기본적으로 롤백 대상이 아니다. Java의 checked/unchecked 구분은 실패의 중요도 순위가 아니다. 팀은 실제 업무 정책에 맞춰 규칙을 정해야 한다.

```java
@Transactional
public void checked() throws IOException {
    jdbc.update("INSERT INTO audit_log(message) VALUES (?)", "checked");
    throw new IOException("fail");
}

@Transactional(rollbackFor = IOException.class)
public void checkedRollback() throws IOException {
    jdbc.update("INSERT INTO audit_log(message) VALUES (?)", "checked");
    throw new IOException("fail");
}
```

외부에서 주입받은 빈을 호출하면 첫 번째는 예외가 나도 기본 정책상 행이 남고, 두 번째는 취소된다. 실제 테스트는 각 실행 전 audit_log를 비우고 종료 후 행 수를 검사한다. Framework는 전역 롤백 기본값을 바꾸는 구성도 지원하므로 프로젝트가 이미 그 정책을 바꿨는지 확인한다. 책의 결과를 모든 Spring 앱에 무조건 적용하지 않는다.

`rollbackFor`에는 타입을 명시하는 편이 안전하다. 클래스 이름 문자열 패턴은 예상보다 넓게 일치할 수 있다. `noRollbackFor`도 특정 예외를 업무상 정상 확정으로 볼 이유가 있을 때 사용한다. 넓은 Exception 규칙을 붙이기 전에 부분 성공을 허용하는 유스케이스가 없는지 검토한다.

## 13.2 catch는 서로 다른 두 상황을 만든다

### 같은 메서드 내부에서 잡은 경우

```java
@Transactional
public void swallow() {
    insert("swallowed");
    try {
        throw new IllegalStateException("fail");
    } catch (IllegalStateException ignored) {
        // 정상 반환하면 프록시가 이 예외를 보지 못한다.
    }
}
```

이 예제는 단순 Java 예외를 직접 던져 잡는다. 내부 자원이 별도로 rollback-only를 표시하지 않았으므로 행이 commit될 수 있다. 실제 DB 제약 오류나 JPA 예외는 이미 트랜잭션을 실패 상태로 만들 수 있으므로 “catch하면 언제나 commit된다”로 일반화하지 않는다.

### 다른 빈의 REQUIRED 경계를 빠져나온 예외를 잡은 경우

```text
Outer 프록시: 트랜잭션 T 시작
  Outer 실제 객체
    → Inner 프록시: T에 참여
      Inner 실제 객체: 예외 발생
    ← Inner 프록시: T를 rollback-only로 표시
  Outer가 예외를 catch하고 정상 반환
Outer 프록시: T를 commit할 수 없어 rollback, UnexpectedRollbackException
```

같은 물리 트랜잭션에 참여한 안쪽 경계가 취소해야 한다고 표시하면 바깥의 catch가 그 결정을 지우지 않는다. **rollback-only**는 “이 트랜잭션은 성공 확정할 수 없다”는 상태다. 호출자가 성공했다고 오인하지 않도록 종료 시 `UnexpectedRollbackException`이 드러날 수 있다.

## 13.3 트랜잭션 어노테이션이 안 먹는 다섯 경로

| 점검 항목 | 실패 상황 | 확인 방법 |
| --- | --- | --- |
| 관리 객체 | 직접 new한 서비스를 사용 | 주입 경로와 실제 빈 확인 |
| 프록시 통과 | this 내부 호출 | 호출자→프록시→대상 그림 |
| 메서드 제약 | private·클래스 프록시의 final | 가로채기 가능한 경계 확인 |
| 예외 정책 | checked exception 정상 commit | 경계 밖의 예외 타입 확인 |
| 자원 참여 | 직접 생성한 별도 Connection | 사용한 매니저·DataSource 확인 |

`@Transactional`이 붙은 테스트가 앱 트랜잭션을 대신 만들어주면 첫 두 문제가 가려질 수 있다. 예제의 TransactionTests에는 테스트 메서드 자체의 트랜잭션을 두지 않았다.

## 13.4 응답 변환 위치와 실패 상태

업무 예외를 서비스 밖으로 전달하고 Advice에서 HTTP로 변환하면 롤백 판단과 응답 변환 경계가 분명하다. 반면 Repository에서 모든 예외를 잡아 null을 반환하면 “없음”과 “DB 장애”가 섞인다. 로그 한 줄 남기는 것만으로 실패 의미를 보존한 것은 아니다.

수동으로 rollback-only를 표시할 수도 있지만 비즈니스 코드가 트랜잭션 인프라에 결합한다. 값 기반 결과 모델을 택했을 때 필요한지 판단하고, 실패 값을 반환했는데 commit된 경우와 성공 값을 반환했는데 rollback된 경우를 모두 테스트한다.

## 실습: 예상 행 수를 먼저 적는다

`mvn -Dtest=TransactionTests test`를 실행하기 전에 다음 표의 결과를 예상한다.

| 테스트 | 최종 audit_log 행 수 | 호출 결과 |
| --- | --- | --- |
| uncheckedExceptionRollsBack | 0 | IllegalStateException |
| checkedExceptionCommitsByDefault | 1 | IOException |
| rollbackForIncludesCheckedException | 0 | IOException |
| catchingLocallyCanCommit | 1 | 정상 반환 |
| catchingInnerRequiredCannotUndoRollbackOnly | 0 | UnexpectedRollbackException |

마지막 행에서 단순히 “catch했는데 왜 실패?”라고 묻기보다 어떤 프록시가 먼저 예외를 보았는지 설명한다. 테스트는 H2와 Spring의 해당 구성에서 확인한 결과이며 다른 매니저·전역 롤백 설정은 별도 확인한다.

## 장애 조사 순서

고객이 실패를 받았다고 말하면 먼저 요청 ID와 업무 키로 DB의 최종 상태를 확인한다. 그다음 프록시 호출, 실제 예외 타입, catch 위치, rollback-only 로그, 매니저·자원을 조사한다. 재시도를 먼저 시키면 이미 commit된 주문을 중복 생성할 수 있다.

## 확인 문제와 해설

**Q1. checked exception은 무조건 commit인가?** 기본 규칙일 뿐이며 rollbackFor·전역 정책·자원의 실패 상태로 결과가 달라질 수 있다.

**Q2. 예외를 RuntimeException으로 감싸면 해결인가?** 롤백 정책에 영향을 주지만 업무 의미·원인 보존·재시도 가능성을 함께 설계해야 한다.

**Q3. 오류를 catch하고 재시도하면 같은 트랜잭션을 복구할 수 있는가?** 이미 rollback-only인 트랜잭션은 새 시도로 되살리지 못한다. 바깥 경계에서 새 트랜잭션으로 재시도한다.

## 참고자료

- [롤백 규칙](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html)
- [Transactional 설정](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)

---

[전체 목차](../index.md) · [← 이전 장](../12-transaction-acid/chapter.md) · [다음 장 →](../14-transaction-propagation/chapter.md)
