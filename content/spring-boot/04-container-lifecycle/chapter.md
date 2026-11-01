---
title: "04장. 빈 컨테이너·스코프·생명주기"
description: "ApplicationContext와 빈 정의·후처리·스코프의 차이를 이해하고 singleton 상태 공유와 초기화·종료 문제를 추적한다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 4
part: 1
enableToc: true
---

> PART 1. Spring의 핵심 원리

## 도입: 사용자 A의 장바구니가 B에게 보인다

서비스 필드에 `currentUser`와 `currentCart`를 저장했더니 동시에 들어온 요청에서 데이터가 섞였다. 컨트롤러와 서비스가 기본적으로 공유되는 빈이라는 사실을 잊은 결과다. 요청마다 메서드가 호출된다고 객체도 요청마다 새로 생기는 것은 아니다.

## 4.1 컨테이너는 객체 저장소 이상이다

`BeanFactory`는 빈 생성과 조회의 기반 계약이다. `ApplicationContext`는 이 기반에 환경·이벤트·리소스 등의 애플리케이션 기능을 더한다. **BeanDefinition**은 아직 객체 그 자체가 아니라 클래스·생성 방식·스코프·의존 관계를 담는 생성 명세다.

빈 정의를 읽는 시점과 실제 객체를 만드는 시점은 다를 수 있다. 지연 생성 빈은 처음 필요해질 때 만들어질 수 있고, 기본 singleton 빈 중 다수는 컨텍스트 초기화 중 준비된다. 따라서 “애플리케이션이 시작했으니 모든 지연 연결이 정상이다”라고 단정할 수 없다.

## 4.2 생명주기의 핵심 구간

```text
빈 정의 등록
 → 생성자 실행·의존성 주입
 → 초기화 전 후처리
 → @PostConstruct 등 초기화 콜백
 → 초기화 후 후처리, 필요한 경우 프록시 제공
 → 사용
 → 컨텍스트 종료 시 @PreDestroy 등 정리
```

이는 읽기 위한 단순화다. 실제 확장점은 더 많다. **BeanFactoryPostProcessor**는 주로 빈 정의를 다루고, **BeanPostProcessor**는 빈 인스턴스의 생성·초기화 과정에 관여한다. 프록시가 만들어지는 것도 이런 인프라와 연결된다.

`@PostConstruct` 안에서 같은 객체의 `@Transactional` 메서드를 부르면 정상 서비스 호출 때의 프록시 동작을 기대하기 어렵다. 초기화 시 DB 수정이 필요하다면 별도 실행 컴포넌트에서 완성된 서비스 빈을 호출하고, 반복 실행·실패·재기동 시의 정책까지 정한다. 모든 서버 인스턴스가 동시에 초기 데이터를 넣을 수도 있다.

## 4.3 스코프는 공유 범위다

| 스코프 | 의미 | 주의점 |
| --- | --- | --- |
| singleton | 한 컨테이너의 해당 빈 정의당 공유 인스턴스 | 프로세스 전체 단 하나라는 절대 규칙 아님 |
| prototype | 컨테이너에 새 인스턴스를 요청할 때 생성 | 사용 후 정리를 컨테이너가 모두 책임지지 않음 |
| request | 웹 요청 범위의 인스턴스 | 웹 컨텍스트와 요청 문맥이 필요 |
| session | HTTP 세션 범위 | 여러 탭·동시 요청이 같은 세션을 쓸 수 있음 |

singleton 서비스에 prototype 빈을 생성자로 주입하면 **주입 시 얻은 한 인스턴스**를 계속 보관한다. 매 호출마다 새 prototype이 필요하면 `ObjectProvider<T>`로 조회하거나 설계를 바꾼다. request 빈을 singleton에서 참조하는 경우에는 scoped proxy 등 수명 차이를 중개하는 방법이 필요하다.

이 규칙을 [빈 스코프 문서](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)와 대조한다. 스코프 이름은 스레드 안전성 인증서가 아니다.

## 4.4 상태를 어디에 둘 것인가

잘못된 부분 코드를 보자.

```java
@Service
class BadCheckout {
    private String currentOwner;
    void reserve(String owner) {
        currentOwner = owner;
        // 여기서 다른 요청이 currentOwner를 덮어쓸 수 있다.
    }
}
```

요청 입력은 매개변수와 지역 변수로 전달한다. 공유 서비스에는 불변 설정이나 공유 가능한 협력 객체를 둔다. `final List`는 참조 교체만 막으며 내부 수정까지 금지하지 않으므로 불변 컬렉션인지 확인한다. `ConcurrentHashMap`을 썼더라도 “조회 후 검사 후 갱신”이라는 여러 단계 전체가 원자적이라는 보장은 별도다.

JDBC Connection과 JPA EntityManager의 작업 상태를 일반 singleton 필드에 직접 저장하지 않는다. 프레임워크가 제공하는 주입 프록시·템플릿이 적절한 문맥의 자원을 찾게 한다. DataSource와 작업별 Connection은 다른 수명이다.

## 4.5 자원 정리와 정상 종료

파일·스레드 풀·외부 클라이언트를 직접 만들었다면 누가 닫는지 지정한다. `@Bean`으로 등록한 AutoCloseable 자원은 적절한 destroy method 추론을 활용할 수 있지만 라이브러리의 종료 계약을 확인해야 한다. 모든 객체가 closeable은 아니며 prototype의 정리는 사용자가 책임질 수 있다.

종료 콜백은 강제 프로세스 종료나 머신 장애에서 실행 보장이 없다. 반드시 완료돼야 하는 업무를 메모리에만 두고 `@PreDestroy`에서 저장하는 설계는 장애에 약하다. 지속성이 필요한 작업은 처리 전에 DB나 브로커에 기록한다.

## 실습: 수명과 동시 요청을 구분한다

`DiTests`의 `assertSame`을 통해 singleton 재사용을 확인한다. 다음 연습에서는 테스트 전용 빈에 생성 카운터를 추가하고 singleton과 prototype을 각각 두 번 조회한다. 예상 생성 횟수는 singleton 한 번, prototype 두 번이다. 이어 prototype을 singleton에 생성자 주입한 뒤 그 singleton을 여러 번 호출해 횟수가 늘지 않는지 관찰한다.

이 연습은 횟수 확인용이며 실제 요청 데이터를 singleton 카운터에 저장하는 설계를 권장하지 않는다. 동시성 실험에서는 원자적 카운터와 일반 int의 차이도 별도로 검토한다.

## 확인 문제와 해설

**Q1. 서버를 세 대 띄웠는데 singleton은 몇 개인가?** 일반적인 독립 컨텍스트 세 개라면 각 컨텍스트에 별도로 존재한다. 전역 중복 방지는 DB 등의 공유 저장소가 필요하다.

**Q2. session 스코프이면 스레드 안전한가?** 같은 세션에서 동시 요청이 가능하므로 아니다.

**Q3. 종료 콜백으로 결제 내역의 유실을 막을 수 있는가?** 정상 종료 보조 수단일 뿐이다. 결제 확정과 지속성은 업무 처리 시점에 확보해야 한다.

## 참고자료

- [빈 생명주기 콜백](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html)
- [컨테이너 확장점](https://docs.spring.io/spring-framework/reference/core/beans/factory-extension.html)

---

[전체 목차](../index.md) · [← 이전 장](../03-dependency-injection/chapter.md) · [다음 장 →](../05-aop-proxy/chapter.md)
