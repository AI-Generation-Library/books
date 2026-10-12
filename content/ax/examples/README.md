---
title: "솔빛서비스 실습 자료"
tags: ["AX", "AI 전환", "업무 혁신", "AI 거버넌스", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
---

# 솔빛서비스 실습 자료

솔빛서비스는 이 책의 **가상 B2B 소프트웨어 회사**다. 모든 문서, 수치와 질문은 학습용으로 작성했다. 실제 회사의 정책·계약·지원 시간이나 관측 성과가 아니다. API 키·고객 개인정보·실제 비밀을 포함하지 않는다.

## 자료 구성

| 파일 | 내용 | 검증 가능한 범위 |
| --- | --- | --- |
| [가정 값](baseline-assumptions.json) | 8장의 계획 입력 | 형식·입력 조건 |
| [비용 계산기](roi_calculator.py) | 시간·경제적·현금 비교 | 산술·입력 검증 |
| [계산 테스트](test_roi.py) | 기본·음수·무현금화·오류 입력 | 계산 코드의 동작 |
| [문서 목록](document-index.json) | 다섯 문서의 버전·등급 | 참조·속성의 일관성 |
| [평가 사례](evaluation-cases.json) | Q001~Q024 기대 행동 | 사례의 구조, 모델은 미실행 |
| [자료 구조 테스트](test_fixtures.py) | ID·유형·문서 참조 | 구조와 선언된 제약 |

공개 자료: [FAQ](documents/faq.md), [지원 정책](documents/support-policy.md). 과거 자료: [과거 안내](documents/release-archived.md). 공개 답변 근거에서 제외하는 자료: [내부 보안](documents/security-internal.md), [제한 계약](documents/contract-restricted.md).

실습 파일은 실제 비밀이 없으므로 모두 공개 배포하지만, 파일 안의 등급은 **가상 시스템에서 구현할 권한**을 연습하기 위한 표시다. 파일이 공개되어 있다는 이유로 가상 고객 답변의 허용 근거로 삼지 않는다.

## API 없이 실행하기

다운로드 ZIP을 풀고 `examples` 디렉토리에서 실행한다. Python 3.10 이상, 표준 라이브러리만 필요하다.

```powershell
python roi_calculator.py baseline-assumptions.json
python -B -m unittest discover -s . -p "test_*.py" -v
```

`-B`는 테스트가 바이트코드 캐시를 남기지 않게 한다. 이 예제는 네트워크·모델 API를 호출하지 않는다. 기본 결과는 1440건·96시간·잠재 가치 240만원·경제적 차이 50만원·월 현금 변화 -30만원이다. 회수 기간은 `null`로 표시된다.

현금화 비율을 모르면 필드를 생략할 수 있으며 0으로 계산한다. 적용 후 시간이 늘어나면 음수 변화를 유지한다. 내부 운영 시간 가치가 실제 추가 지급이면 반복 현금비로 옮겨 중복 계산을 피한다. 모델은 금융·세금·매출·확률·물량 증가를 포함하지 않는다.

## 평가 사례의 사용

[가상 설계 예시](filled-project.md)에서 문제·자료·권한·평가·비용·다음 결정을 연결하는 방법을 볼 수 있다. 실제 승인이나 실험 결과는 포함하지 않는다.

일반 8, 부족·충돌 6, 권한 6, 악성 4개로 구성된다. `expected_action`은 answer·clarify·escalate·refuse 중 하나다. `allowed_evidence`는 현재 승인된 공개 근거이며 `required_constraint`는 보존할 경계다. 모든 사례의 `execution_status`는 `not-run`이다.

부서별 실제 정책이 다르면 기대 행동도 검토해 바꾼다. 권한과 공개 범위 검사는 서버에서 수행하며 자연어 지시만으로 보장하지 않는다. 실제 모델 평가를 진행할 경우 원본 사례를 보존하고 별도 결과 파일에 제공자·모델·날짜·설정·출력·판정·비용을 기록한다. 작은 세트를 통과해도 운영 안전을 입증한 것은 아니다.

[통합 실습 29장](../29-chapter/chapter.md)과 [워크시트](../appendices/workbook.md)에 자료를 연결해 사용할 수 있다.
