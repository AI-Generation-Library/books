---
title: "03장. IoC와 DI: 객체의 조립을 설계한다"
description: "생성자 주입을 직접 구현한 뒤 빈 후보 선택·Qualifier·Primary·순환 의존성과 테스트 대역을 다룬다."
tags: ["Spring Boot", "Java", "백엔드"]
created: "2026-11-01"
modified: "2026-11-01"
chapter: 3
part: 1
enableToc: true
---

> PART 1. Spring의 핵심 원리

## 도입: 운영 저장소를 바꾸려다 주문 규칙도 수정했다

서비스 생성자 안에 `new JdbcReservationRepository(...)`가 있고, 메서드 안에서 전역 설정을 읽는다고 해 보자. 저장소 교체와 주문 규칙의 변경이 같은 파일로 몰린다. 테스트를 위해 DB 비밀번호와 네트워크까지 준비해야 한다. DI의 출발점은 어노테이션이 아니라 **협력 객체를 밖에서 전달받게 바꾸는 일**이다.

## 3.1 의존성은 무엇인가

A가 일을 수행하기 위해 B의 기능을 사용하면 A는 B에 의존한다. 클래스 import뿐 아니라 생성, 호출, 설정, 시간, 파일 시스템도 의존성이다. “인터페이스를 사용했으니 의존성이 없어졌다”는 표현은 부정확하다. 구체 구현에 대한 결합을 인터페이스 계약에 대한 의존으로 바꾼 것이다.

다음은 컨테이너 없이 실행할 수 있는 설계 예제다. 실제 실행 테스트는 `DiTests`에 있다.

```java
interface FeePolicy { int fee(int price); }
record Checkout(FeePolicy policy) {
    int total(int price) { return price + policy.fee(price); }
}
// 조립 지점
var checkout = new Checkout(price -> 100);
int result = checkout.total(1000); // 1100
```

Checkout은 정책을 어디서 찾는지 알지 못한다. 테스트는 `price -> 0`을 전달해 배송비 없는 경우를 검증한다. 실제 코드에서는 금액 범위·통화·오버플로 같은 도메인 제약도 설계해야 하며 이 짧은 예제는 조립 관계만 보여준다.

## 3.2 IoC와 DI, Service Locator

IoC는 제어 책임의 이동이라는 넓은 관점이고 DI는 필요한 객체를 전달하는 방식이다. 컨테이너를 전역으로 가져와 `getBean()`을 호출하는 **Service Locator** 패턴은 서비스가 의존성을 직접 찾는다. 생성자 서명에 보이지 않는 의존성이 생겨 테스트와 구조 파악이 어려워질 수 있다.

Spring 컨테이너는 **빈 정의**를 읽어 객체를 만들고 관계를 연결한다. 빈은 컨테이너가 관리하는 객체다. Java의 모든 객체가 빈일 필요는 없다. 요청 DTO, 계산 결과, 엔티티마다 `@Component`를 붙이면 수명과 책임이 뒤섞인다.

## 3.3 생성자 주입을 기본으로 삼는 이유

```java
@Service
public class ReservationService {
    private final ReservationRepository repository;

    public ReservationService(ReservationRepository repository) {
        this.repository = repository;
    }
}
```

생성 시 필수 협력자가 드러나고 필드를 final로 유지할 수 있다. 단일 생성자는 보통 `@Autowired` 없이 주입할 수 있다. Lombok을 쓰면 생성자 코드가 감춰지므로 처음에는 생성자를 직접 써서 관계를 확인한다.

필드 주입은 `new Service()`가 겉으로 성공해도 필수 필드가 null인 객체를 만들 수 있다. Setter 주입은 생성 뒤 변경 가능성을 열어 두므로 선택적·가변 의존성이 필요한 경우에 의도를 명시한다. 모든 주입 방식이 같은 설계 의미를 갖지는 않는다. [Spring DI 문서](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)는 생성자·Setter 방식을 구분한다.

## 3.4 같은 타입의 빈이 두 개라면

예를 들어 `PaymentGateway` 구현이 실제 결제용과 샌드박스용으로 둘 다 등록되면 타입만으로 하나를 선택할 수 없다. `@Primary`는 기본 우선 후보를, `@Qualifier`는 특정 역할을 명시하는 데 사용한다. 다음은 후보 선택을 설명하는 부분 코드다.

```java
public CheckoutService(@Qualifier("sandbox") PaymentGateway gateway) {
    this.gateway = gateway;
}
```

Qualifier는 클래스의 모든 후보를 무조건 이름으로 바꾸는 기능이라기보다 주입 후보를 좁히는 조건이다. 환경별 구현 하나만 필요하면 `@Profile`이나 조건부 빈 구성으로 처음부터 후보를 제한할 수도 있다. 후보가 없을 때와 후보가 여러 개일 때를 다른 오류로 읽는다.

여러 구현을 모두 실행해야 한다면 `List<Rule>` 같은 컬렉션 주입이 목적에 맞을 수 있다. 이때 규칙 순서가 비즈니스 의미를 가진다면 `@Order` 또는 명시적인 정렬·조립으로 드러낸다. 우연한 스캔 순서에 기대지 않는다.

## 3.5 @Bean과 @Component

자신이 작성한 서비스는 `@Service`나 `@Component`로 스캔되게 만들기 쉽다. 외부 라이브러리 객체, 복잡한 생성 절차, 서로 다른 설정을 갖는 인스턴스는 `@Bean` 메서드로 조립 지점을 드러내는 편이 좋다.

```java
@Configuration(proxyBeanMethods = false)
class CheckoutConfig {
    @Bean
    FeePolicy feePolicy() { return price -> 100; }

    @Bean
    Checkout checkout(FeePolicy feePolicy) {
        return new Checkout(feePolicy);
    }
}
```

여기서는 메서드 인자로 다른 빈을 받는다. `proxyBeanMethods=false` 상태에서 `checkout()` 안에서 `feePolicy()`를 직접 호출하면 평범한 Java 호출이므로 새 객체를 만들 수 있다. 설정 메서드 직접 호출과 컨테이너에서 빈을 받는 일을 혼동하지 않는다.

## 3.6 순환 의존성은 설계 신호다

`OrderService → PaymentService → OrderService`처럼 생성자 관계가 원을 그리면 완성할 첫 객체가 없다. `@Lazy`나 Setter로 기동만 통과시키기 전에 각 서비스가 너무 많은 책임을 갖는지 본다. 상위 `CheckoutUseCase`가 두 서비스를 조율하거나, 필요한 조회 인터페이스를 분리하면 의존 방향을 정리할 수 있다.

이벤트로 바꿀 때도 주의한다. 동기 이벤트라면 호출 결합이 여전히 남고, 비동기 이벤트라면 원자성과 실패 처리 요구가 바뀐다. 순환 의존을 없애기 위해 거래 보장을 무심코 약화시키면 안 된다.

## 실습: DI를 눈으로 확인한다

예제 폴더에서 `mvn -Dtest=DiTests test`를 실행한다. 첫 테스트는 Spring 없이 대역 정책을 주입하고, 두 번째는 `AnnotationConfigApplicationContext`로 설정을 읽는다. 같은 Checkout 빈을 두 번 조회했을 때 `assertSame`이 성립하는지 확인한다.

확장 실습에서는 `FeePolicy` 빈을 하나 더 등록하고 실패 메시지를 읽는다. 그런 다음 `@Primary`를 지정해 해결하고, 특정 생성자에는 `@Qualifier`를 사용한다. 예상 결과는 “후보가 두 개라 실패 → 기본 후보 지정으로 성공 → 명시 후보로 다른 결과”다. 이 변형은 독자가 수행하는 연습이며 첨부 테스트의 실행 범위와 구분한다.

## 확인 문제와 해설

**Q1. 인터페이스가 없으면 DI를 할 수 없는가?** 구체 클래스도 주입할 수 있다. 인터페이스는 교체·계약 분리의 필요성에 따라 선택한다.

**Q2. 빈이 singleton이면 정책 객체가 불변인가?** 아니다. 스코프는 인스턴스 공유 범위이고 객체의 가변성과 스레드 안전성은 별도다.

**Q3. 생성자 인자에 `Clock`을 받는 이유는?** 현재 시각도 외부 의존성이다. 고정 Clock을 전달하면 만료 시점 테스트가 실제 시간에 의존하지 않는다.

## 참고자료

- [Qualifier](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html)
- [Primary](https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-primary.html)
- [Java 기반 구성](https://docs.spring.io/spring-framework/reference/core/beans/java/basic-concepts.html)

---

[전체 목차](../index.md) · [← 이전 장](../02-environment/chapter.md) · [다음 장 →](../04-container-lifecycle/chapter.md)
