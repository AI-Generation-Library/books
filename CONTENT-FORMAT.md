# 책 콘텐츠 형식

`content/<id>/book.json`과 해당 폴더의 원고가 콘텐츠 계약입니다. 서비스는 원본을 읽고 별도의 작업 공간에서 웹용 자료를 생성합니다. `scripts/book_metadata.py`가 아래 규칙을 검사하며 `python scripts/validate-books.py`는 모든 등록 책을 읽기 전용으로 검증합니다.

## 디렉토리와 링크

id는 소문자 영문·숫자·하이픈을 사용합니다. 예: `fastapi`, `python-basics`. `book.json.id`는 폴더명과 같아야 합니다. `index.md`는 책 목차·소개이며 자동 빌드가 덮어쓰지 않습니다. 원고, 부록, 예제와 다운로드는 책 폴더 안에 둡니다.

등록된 Markdown `href`는 책 폴더 상대 경로이고 `.md`를 생략합니다. 다운로드는 확장자를 포함합니다. 절대 경로, `.`·`..` 경로 조각, 역슬래시, URL query·fragment·scheme·percent encoding을 사용하지 않습니다. 등록 파일과 symlink의 실제 대상도 책 내부에 있어야 합니다. 본문의 외부 웹 링크는 이 메타데이터 규칙과 별개입니다.

## book.json 예시

```json
{
  "id": "python-basics",
  "title": "Python 기초",
  "description": "대상 독자와 배울 내용을 설명합니다.",
  "status": "draft",
  "tags": ["Python", "한국어"],
  "provenance": {
    "generator": "사용한 AI 도구",
    "model": null,
    "created": "2026-10-11",
    "updated": "2026-10-11",
    "source": "입력 목차, 작성 지시와 참고 자료를 기록합니다.",
    "review": {
      "status": "unreviewed",
      "scope": [],
      "notVerified": ["실습 실행과 전체 사람 검수"],
      "verification": "appendices/verification"
    }
  },
  "chapters": [
    {"number": 1, "title": "시작하기", "href": "01-introduction/chapter", "part": 1}
  ],
  "parts": [
    {"number": 1, "title": "첫 번째 파트", "first": 1, "last": 1}
  ],
  "downloads": []
}
```

## 필수 정보

| 필드 | 규칙 |
| --- | --- |
| `id` | 폴더명과 같은 안전한 id |
| `title`, `description`, `status` | 비어 있지 않은 문자열. 상태는 `draft`, `published`, `reviewed` 등 실제 상태 기록 |
| `tags` | 비어 있지 않은 문자열 배열. 빈 배열 허용 |
| `provenance.generator`, `source` | 생성 도구와 입력·자료를 설명하는 문자열 |
| `provenance.model` | 확인된 모델명 또는 `null`. 필드를 생략하지 않음 |
| `provenance.created`, `updated` | 실제 달력 날짜 `YYYY-MM-DD`. 갱신일은 생성일 이후 또는 같은 날 |
| `provenance.review.status` | 검토 상태 문자열 |
| `provenance.review.scope` | 확인한 범위의 문자열 배열. 미검증은 빈 배열 |
| `provenance.review.notVerified` | 선택 사항. 미확인 범위의 문자열 배열 |
| `provenance.review.verification` | 선택 사항. 기존 검증 안내 Markdown의 상대 경로 또는 `null` |
| `chapters` | 적어도 한 장. `number`, `title`, `href`, `part` 필요 |
| `parts` | 적어도 한 파트. `number`, `title`, `first`, `last` 필요 |
| `downloads` | 선택 사항. 각 항목에 `title`, `href`, `type`과 실제 파일 필요 |

`chapters`는 1부터 전체 장 수까지 연속 번호 순서로 작성합니다. 각 `href`는 고유하고 실제 Markdown 파일이어야 합니다. `parts`도 1부터 연속 순서이며 장 전체를 중복이나 빈 구간 없이 나눕니다. 각 장의 `part`는 그 범위와 같아야 합니다. 장 수·파트 수·다운로드 수는 책마다 다를 수 있습니다.

`topicCount`, `practiceSummary`, `review.humanReview` 같은 추가 설명을 기록할 수 있습니다. 콘텐츠 검사 통과는 실제 실습이나 전체 설명 검수 완료를 뜻하지 않습니다.

## Markdown frontmatter

```yaml
---
title: "01장. 시작하기"
description: "이 장에서 배울 내용"
tags: ["Python"]
created: "2026-10-11"
modified: "2026-10-11"
chapter: 1
part: 1
enableToc: true
---
```

장 원고는 frontmatter 뒤에 일반 Markdown으로 작성합니다. 책 목차와 폴더 안내는 `chapter`·`part`를 생략할 수 있습니다. 이전 원고의 Quartz 표시 옵션과 HTML은 호환성을 위해 보존하지만 새 원고가 사이트 코드를 포함할 필요는 없습니다.

## 저작 도구와 서비스 경계

`new-book.py`는 없는 책 폴더에 템플릿을 생성하고 `sync-book.py`는 요청한 외부 원고 한 권을 가져옵니다. 두 도구는 저자가 명시적으로 실행하며 목차·메타데이터를 작성할 수 있습니다. 가져오기는 준비한 책을 검증한 뒤 대상에 적용합니다.

`validate-books.py`와 `book_metadata.load_books(root)`는 원고·목차·메타데이터에 쓰기를 수행하지 않습니다. `library`는 원본 확인 후 자신의 빌드 작업 공간에서 manifest·카드·검색 인덱스를 만듭니다. 원고 저장소에는 생성 웹 목록을 커밋하지 않습니다.
