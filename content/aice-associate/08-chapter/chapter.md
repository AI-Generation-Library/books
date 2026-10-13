---
title: "08장. 시각화로 데이터 특성 파악하기"
description: "분포·범주·변수 관계를 목적에 맞는 그림으로 확인한다."
tags: ["AICE Associate", "Python", "데이터 분석", "머신러닝", "한국어"]
created: "2026-10-13"
modified: "2026-10-13"
enableToc: true
chapter: 8
part: 2
---

# 08장. 시각화로 데이터 특성 파악하기

그림은 질문에 맞는 형태로 선택한다. 숫자 분포는 히스토그램, 범주별 수는 막대그래프, 두 숫자의 관계는 산점도로 볼 수 있다. 보기 좋은 색보다 축의 단위·표본·결측과 비교 조건이 중요하다.

## 1. 분포와 범주

히스토그램의 구간 수에 따라 모양이 달라질 수 있다. 여러 구간 수를 보며 극단값과 집중 구간을 확인한다. 막대그래프에서는 개수인지 비율인지 표시한다. 전체 표본의 그룹 비율이 크게 다르면 평균만 비교하지 않는다.

```python
import matplotlib.pyplot as plt
import seaborn as sns
from lab import load_customers

df = load_customers()
fig, axes = plt.subplots(1, 2, figsize=(9, 3))
sns.histplot(data=df, x="tenure_months", bins=12, ax=axes[0])
sns.countplot(data=df, x="contract_type", ax=axes[1])
axes[0].set_title("Tenure distribution")
axes[1].set_title("Contract counts")
fig.tight_layout()
assert len(axes) == 2
plt.show()
plt.close(fig)
```

그림은 자체 제작 자료의 탐색이다. 정상적인 차이가 있어도 사업적 원인이나 효과로 해석하지 않는다. 결측 범주가 그림에서 제외되는지도 확인한다.

## 2. 관계를 보는 그림

산점도는 연속 변수의 관계와 예외를 보여준다. 점이 겹치면 투명도·작은 점·표본을 사용할 수 있지만 표본 선택 방식을 남긴다. 박스플롯은 중앙값과 사분위 범위를 요약하며 바깥 점을 자동 오류로 판정하는 도구가 아니다.

타깃별 분포를 비교할 때 그룹 수가 다른지 본다. 범주별 이탈률처럼 비율을 그릴 경우 분모가 너무 작은 그룹은 해석을 제한한다. 같은 축으로 비교하는지와 축을 잘라 차이를 과장하지 않았는지도 확인한다.

## 3. 그래프와 출력 조건

문제에서 산점도·축·제목·파일 이름을 지정하면 그대로 맞춘다. 화면에 그리는 것과 파일로 저장하는 것은 별개다. `savefig`를 사용할 때는 저장 경로, 확장자와 적절한 여백을 확인한다. 불필요한 절대 경로나 개인 폴더 경로를 공유 파일에 넣지 않는다.

반복 실행에서 그림이 쌓이지 않도록 `close`를 호출할 수 있다. 여러 그림에서 현재 축이 무엇인지 불명확하면 `fig, ax = plt.subplots()`로 명시적으로 전달한다. 실행 환경의 폰트에 따라 한글이 깨질 수 있으므로 이 책의 테스트 그림은 영어 레이블을 사용한다.

## 4. 그림에서 다음 행동 찾기

분포가 한쪽으로 치우치면 평균·중앙값과 변환의 필요를 검토한다. 극단값이 전체 축을 넓히면 원자료와 제한된 표시를 구분한다. 결측을 그림에서 숨긴 채 “문제 없음”으로 결론 내리지 않는다.

그림은 전처리·모델 선택의 근거 중 하나다. 정규분포처럼 보이게 만든다는 이유만으로 모든 변수에 같은 변환을 적용하지 않는다. 변환의 정의와 모델의 요구, 평가 결과를 함께 본다.

## 연습과 해설

1. 계약 유형별 고객 수와 평균 요금에 같은 막대그래프를 쓰더라도 무엇이 다른가? **해설:** 축의 값과 단위, 계산한 집계와 분모가 다르다.
2. 박스플롯 바깥 점은 반드시 삭제해야 하는가? **해설:** 드문 정상값일 수 있다. 자료 사전과 원인을 먼저 확인한다.

다음 장에서 변수 간 관계와 타깃의 분포를 해석한다. 참고: [Matplotlib 시작 안내](https://matplotlib.org/stable/users/explain/quick_start.html), [Seaborn 분포 안내](https://seaborn.pydata.org/tutorial/distributions.html).

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 07장 데이터 구성과 품질 점검하기](../07-chapter/chapter.md) · [09장 상관관계와 타깃 분석하기 →](../09-chapter/chapter.md)
