# AI Generation Library에 기여하기

원고 오류 수정, 설명 개선, 실행 예제 보완, 새 책 추가를 환영합니다. 원고는 `content/<책 id>/`에 있고, 모든 책은 공통 Quartz 사이트를 공유합니다.

## 기존 책 수정

1. 저장소를 fork하고 작업 브랜치를 만듭니다.
2. 해당 책의 Markdown 또는 실습 코드를 수정합니다. 설명을 바꿀 때 근거가 되는 공식 자료를 함께 링크합니다.
3. 실제로 실행한 검사와 결과는 책의 검증 안내에 기록합니다. `book.json`의 `provenance.updated`와 검증 범위도 필요한 경우 갱신합니다.
4. `npm run build`와 `python scripts/check-output.py --base-path /books/`를 실행합니다.
5. 문제, 변경 후 동작, 확인한 결과를 적어 PR을 제출합니다. PR CI 결과가 통과하는지 확인합니다.

Markdown 본문만 고칠 때 장 목록을 다시 가져올 필요는 없습니다. 외부 원고 importer는 같은 파일을 덮어쓰므로 직접 편집한 책에 무심코 실행하지 마세요.

## 새 책 추가

저장소 루트에서 다음을 실행합니다.

```powershell
python scripts/new-book.py --slug python-basics --title "Python 기초"
```

책 id는 소문자 영문·숫자·하이픈을 사용하며 `book.json`의 `id`와 폴더명이 같아야 합니다. 화면에 표시되는 제목은 한국어를 포함해 자유롭게 작성할 수 있습니다. 같은 id의 책이 있으면 생성기는 종료합니다.

생성된 첫 장과 검증 안내를 실제 내용으로 채우세요. 추가 장은 `02-.../chapter.md`처럼 폴더별로 작성하거나 원하는 Markdown 경로를 사용할 수 있습니다. 각 장의 frontmatter에는 `title`, `description`, `chapter`, `part`를 넣습니다. 폴더 안내의 `index.md`를 두면 사이드바에 읽기 좋은 제목을 표시할 수 있습니다. 책의 목차 `index.md`에 자체 hero 제목을 넣는 경우 `bookHome: true`를 유지합니다.

책 안에서는 `../index.md`, `./chapter.md`처럼 상대 링크를 사용합니다. 장의 예제는 같은 책 폴더 안에 두고 설치 버전, 실행 명령, 예상 결과를 적습니다. 책 밖의 공통 페이지와 다른 책은 필요한 경우에만 상대 링크로 연결합니다.

## 책 정보와 등록 목록

`book.json`이 장 목록과 출처 정보의 원본입니다. 구조의 축약 예는 다음과 같습니다.

```json
{
  "id": "python-basics",
  "title": "Python 기초",
  "description": "책의 대상 독자와 배울 내용을 설명합니다.",
  "status": "draft",
  "tags": ["Python", "한국어"],
  "provenance": {
    "generator": "사용한 AI 도구",
    "model": null,
    "created": "2026-10-11",
    "updated": "2026-10-11",
    "source": "입력 목차, 사용 자료와 생성 방법을 기록합니다.",
    "review": {
      "status": "unreviewed",
      "scope": [],
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

`chapters[].href`와 검증 안내 경로는 책 폴더 상대 경로이며 `.md`를 생략합니다. 장 목록은 1장부터 전체 장 수까지 연속 번호 순서로 작성하고, `parts`의 시작·끝 번호는 그 파트의 실제 장 범위에 맞춥니다. 장 수나 파트 수는 제한하지 않습니다. `status`는 `draft`, `published`, `reviewed`처럼 실제 상태를 적으세요. 등록된 초안도 사이트에 표시되므로 PR 전에 독자가 읽을 내용을 준비합니다.

다운로드를 제공하면 `downloads`에 `title`, `href`, `type`을 추가합니다. 예를 들어 `{"title":"실습 코드","href":"downloads/examples.zip","type":"example-code"}`입니다. 등록한 파일은 실제로 있어야 합니다. 종류와 개수는 고정되어 있지 않습니다.

`npm run build`가 `scripts/index-library.py`를 실행해 각 책의 `static/book-manifest.json`, `content/static/library-manifest.json`, 공통 홈의 책 카드와 책·장 수를 갱신합니다. 생성 결과는 커밋에 포함하되 직접 수정하지 마세요. 책 본문과 책 목차는 자동으로 바꾸지 않습니다. 새 장을 등록하면 책의 목차 링크도 직접 추가하세요.

## AI 출처와 검증 기록

생성 도구와 확인된 모델명을 기록합니다. 확인할 수 없는 상세 모델은 추측하지 말고 `null`로 둡니다. 생성에 사용한 목차, 직접 제공한 자료, 주요 작성 지시와 생성 시기를 남기세요. 출처 링크와 인용은 독자가 원문을 확인할 수 있도록 표시합니다.

검증 안내에는 다음을 구체적으로 적습니다.

- 사용한 OS·언어·의존성 버전, 실행 명령과 결과.
- 문법 검사, 로컬 실행, 실제 외부 환경 검증 중 어디까지 했는지.
- 사람이 검토한 범위와 자동 검사한 범위.
- 아직 실행하지 않은 코드나 외부 서비스 구성.

성공 결과를 실제로 확인한 경우에만 실행 성공을 기록합니다. API·법규·가격처럼 바뀔 수 있는 내용은 출처와 기준 날짜를 남기세요. 템플릿의 미확인 표를 확인된 결과로 채우고, `book.json`의 검증 범위와 일치시킵니다.

## PR에 포함할 내용

새 책 PR에는 대상 독자, 책의 범위, AI 생성 정보, 참고 자료, 검증 결과를 적습니다. 기존 책 수정 PR에는 잘못된 설명이나 실패하는 구체적인 상황과 수정 후 결과를 적습니다. 빌드·링크 검사 외에 코드를 바꿨다면 그 예제에 맞는 실행 검사도 적으세요. 비밀 키, 개인 데이터와 실행 중 만들어진 DB·캐시·가상환경은 포함하지 않습니다.

기존 CC0 `LICENSE`와 Quartz MIT `LICENSE.txt`는 보존합니다. 포함한 제삼자 자료와 코드의 출처·라이선스를 유지하세요.
