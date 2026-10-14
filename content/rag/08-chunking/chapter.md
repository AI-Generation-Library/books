---
title: "08장. 청킹 전략 설계와 비교"
description: "검색 단위와 답변에 필요한 문맥 단위를 구분한다. 경계·중첩·입력 제한을 실험으로 선택한다."
tags: ["RAG", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 8
part: 2
enableToc: true
---

# 08장. 청킹 전략 설계와 비교

## 학습 목표

- 검색 단위와 답변에 필요한 문맥 단위를 구분한다.
- 경계·중첩·입력 제한을 실험으로 선택한다.

## 청크 크기에 보편적인 정답은 없다

청크가 짧으면 주제를 잘 구분할 수 있지만 주어·조건·예외가 떨어질 수 있다. 길면 문맥을 보존하지만 서로 다른 주제가 섞이고 모델 입력에서 잘릴 수 있다. 문서 구조·질문 유형·임베딩 모델·생성 예산을 함께 고려한다.

고정 문자 수 분할은 재현하기 쉽고 기준선으로 좋다. 문장·문단·제목 구조를 이용하면 의미 경계를 보존하기 좋지만 파싱이 잘못되면 구조도 잘못된다. 의미 기반 분할은 추가 임베딩 계산과 임계값 평가가 필요하다. 최신이라는 이름만으로 더 낫다고 가정하지 않는다.

## 기본 구현과 위치

예제는 정규화 텍스트에서 size=320, overlap=40의 문자 윈도를 사용한다. start/end는 Python 문자열의 코드포인트 인덱스이며 end는 제외된다. 실제 모델의 토큰 윈도가 아니다. 각 청크가 원문의 해당 구간과 일치하고 마지막 문자가 빠지지 않는지 검사한다.

```python
from ragbook.data import Document, chunks, normalize
document = Document('guide', 'acme', ('reader',), '안내', 'fixture://guide', 'v1', '문서 내용 '*100)
parts = chunks(document, size=64, overlap=12)
text = normalize(document.text)
assert all(part.text == text[part.start:part.end] for part in parts)
```

중첩은 경계에서 근거가 잘리는 문제를 줄일 수 있지만 저장량과 검색 중복을 늘린다. 높은 Recall이 겹치는 청크 여러 개를 같은 근거처럼 센 결과인지 확인해야 한다. 문서 단위와 청크 단위 평가를 구분한다.

## 구조를 이용한 확장

제목 경로를 청크의 검색용 텍스트나 메타데이터에 넣으면 짧은 본문의 맥락을 보완할 수 있다. 다만 제목을 임의로 모델이 생성했다면 원문 제목과 구분한다. Parent-child 방식은 작은 청크로 찾고 큰 부모 구간을 생성에 제공한다. 17장에서 권한·버전·예산을 포함해 다룬다.

표·코드·규정의 예외 조항은 일반 문장 분할과 다르게 다룰 수 있다. 표의 단위와 머리글, 코드의 함수·주석, 규정의 적용 조건을 유지한다. 분할 규칙을 바꾸면 청크 ID와 평가 정답 연결도 달라질 수 있다.

## 비교 실험

문서 snapshot과 질문을 고정하고 크기·중첩만 바꾼다. 검색 Recall·순위·인용 가능성·입력 토큰·색인 시간·저장량을 함께 본다. 특정 질문 하나가 좋아졌다는 이유로 전체 전략을 선택하지 않는다. 실패한 질문의 원문 위치를 보면 분할 문제인지 검색 모델 문제인지 좁힐 수 있다.

## 실습과 평가

테스트에서 긴 한글 문서를 분할해 시작·끝·중첩·재현 ID를 확인한다. size와 overlap이 같거나 overlap이 음수면 거부되어야 한다.

새 실험용 DB를 만들어 크기를 바꿔 비교하되 설정을 기록한다. 실제 신경망 모델의 입력 절단 여부는 해당 tokenizer와 모델 제한으로 별도 검사한다.

## 확인 문제

오버랩을 크게 늘리면 검색 품질도 항상 좋아지는가?

[해설](../appendices/answers.md#장-08)

## 논문과 공식 자료

기준일: 2026-10-14. 원문을 대량 복제하지 않고 개념을 재구성하고 자체 예제를 작성했다.

- [Design and Develop a RAG Solution on Azure - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide)
- [Develop a RAG Solution on Azure - Chunking Phase - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-chunking-phase)

---

[이전 장](../07-normalization/chapter.md) · [책 목차](../index.md) · [다음 장](../09-metadata/chapter.md)
