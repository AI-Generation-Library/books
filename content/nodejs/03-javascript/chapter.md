---
title: "03장. 서버 개발에 필요한 JavaScript"
description: "클로저와 객체 참조가 서버 상태에 미치는 영향을 이해한다. 데이터 변환과 예외 처리를 명시적으로 작성한다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 3
part: 1
enableToc: true
---

# 03장. 서버 개발에 필요한 JavaScript

## 학습 목표

- 클로저와 객체 참조가 서버 상태에 미치는 영향을 이해한다.
- 데이터 변환과 예외 처리를 명시적으로 작성한다.

## 값과 참조, const의 의미

`const`는 변수의 재할당을 막는다. 그 변수가 가리키는 객체 내부를 불변으로 만들지는 않는다. 요청마다 같은 전역 객체를 수정하면 서로 다른 사용자의 처리가 영향을 줄 수 있다. 객체 펼침 문법도 얕은 복사이므로 중첩된 배열과 객체는 여전히 공유될 수 있다.

```js
const original = { options: { retries: 2 } };
const copy = { ...original };
copy.options.retries = 9;
console.log(original.options.retries); // 9
```

JSON 데이터처럼 지원 범위가 분명한 값은 `structuredClone`을 검토할 수 있지만 함수나 모든 클래스 인스턴스를 일반적으로 복제해 주는 것은 아니다. 더 좋은 해결은 요청별 값과 애플리케이션 공통 설정의 소유권을 처음부터 구분하는 것이다.

## 스코프와 클로저

함수는 자신이 만들어진 환경의 변수를 참조할 수 있다. 클로저는 카운터·설정 주입·테스트 더블을 만드는 데 유용하다. 동시에 이벤트 리스너나 타이머가 오래 살아 있으면 클로저를 통해 큰 객체가 계속 참조될 수도 있다. 스코프가 끝났다는 사실만으로 객체가 즉시 회수되는 것은 아니다.

```js
function counter() { let n = 0; return () => ++n; }
const next = counter();
console.log(next(), next());
const input = [{ name: 'A', size: 2 }, { name: 'B', size: 3 }];
console.log(input.filter(x => x.size > 2).map(({ name }) => name));
try { JSON.parse('{'); } catch (error) { console.log(error.name); }
```

[실행 파일](../examples/fundamentals/03-javascript.mjs)

`counter()`를 호출할 때마다 별도의 `n`이 만들어진다. 같은 반환 함수를 여러 요청이 공유하면 같은 카운터를 사용한다. 프로세스 내부 카운터는 서버 인스턴스를 늘리면 인스턴스마다 별개가 되므로 전체 서비스의 요청 수로 사용할 수 없다.

## 함수와 데이터 변환

`map`은 새 배열을 만들고, `filter`는 조건을 만족하는 항목을 고른다. 배열 메서드 자체가 비동기 작업을 기다리는 것은 아니다. `array.forEach(async ...)`는 모든 작업이 끝나는 시점을 호출자에게 반환하지 않는다. 비동기 순회는 6장에서 `for...of`와 Promise 조합으로 다시 다룬다.

화살표 함수는 자체 `this`를 만들지 않는다. 클래스 메서드를 콜백으로 넘기면 호출 방식에 따라 `this`가 달라질 수 있다. 상태가 필요한 함수를 객체 메서드로 둘지, 의존성을 받는 일반 함수로 둘지는 사용 방식과 테스트 편의에 따라 정한다.

## 실패를 값으로 숨기지 않기

문자열에서 객체를 만드는 `JSON.parse`는 잘못된 JSON에 예외를 던진다. 이를 모두 잡아 빈 객체로 바꾸면 입력 오류가 뒤늦게 DB 오류로 보일 수 있다. 경계에서 입력을 검증하고, 실패 이유를 호출자에게 일관되게 전달한다. 오류 문자열 전체를 비교하기보다는 직접 정한 오류 코드나 오류 타입을 사용한다.

`catch`는 잡은 오류를 반드시 해결했다는 뜻이 아니다. 처리할 수 없다면 문맥을 추가해 다시 던지거나 상위 계층에 전달해야 한다. `finally`는 성공·실패와 관계없이 자원을 정리할 때 쓰지만, 그 안에서 새 값을 반환하면 이전 결과를 덮어쓸 수 있어 주의한다.

## 실습과 관찰

`node fundamentals/03-javascript.mjs`를 실행하면 카운터 `1 2`, 필터링 결과 `B`, 파싱 실패의 `SyntaxError`를 볼 수 있다. 카운터 함수를 하나 더 만들어 두 카운터가 상태를 공유하는지 확인한다.

객체 복사 예제의 `options`를 별도로 복사하도록 바꾸고 원본이 유지되는지 `node:assert/strict`로 검사한다. 문자열 크기를 `length`로 제한하는 것과 UTF-8 바이트 수로 제한하는 것의 차이는 9장에서 확인한다.

## 확인 문제

전역 배열에 요청 데이터를 넣고 응답 후 함수가 끝났다. 그 데이터는 자동으로 제거되는가?

[해설 보기](../appendices/answers.md#장-03)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Closures - JavaScript | MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [try...catch - JavaScript | MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch)

---

[이전 장](../02-environment/chapter.md) · [책 목차](../index.md) · [다음 장](../04-npm-project/chapter.md)
