# AI Generation Library · books

AI로 생성한 책의 **원고, 목차, 생성 출처, 검증 기록과 실습 코드**를 보관하는 콘텐츠 저장소입니다. 누구나 PR로 책을 추가하거나 오류를 수정할 수 있습니다. 검색·카테고리·웹 뷰어와 배포는 별도 [library 저장소](https://github.com/AI-Generation-Library/library)에서 관리합니다.

[온라인 서재](https://ai-generation-library.github.io/library/) · [책 생성기](https://github.com/AI-Generation-Library/book-generator) · [기여 안내](CONTRIBUTING.md) · [콘텐츠 형식](CONTENT-FORMAT.md)

책 목록은 [온라인 서재](https://ai-generation-library.github.io/library/)에서 확인하세요. 목록·장 수·카드는 각 책의 메타데이터에서 생성하므로, 책이 추가되어도 이 README의 목록을 관리할 필요가 없습니다.

## 저장소 구조

```text
content/
└── <book-id>/
    ├── book.json                 # 책 정보·AI 출처·장 목록의 원본
    ├── index.md                  # 사람이 작성하는 목차와 책 안내
    ├── 01-chapter/
    │   └── chapter.md            # 장 원고
    ├── …
    ├── appendices/               # 용어·검증 기록·참고 자료
    ├── downloads/                # 원고 ZIP과 실습 코드
    └── examples/                # 실습 코드 (선택)
scripts/
├── book_metadata.py              # 공통 메타데이터·경로 검증
├── validate-books.py             # 전체 책 읽기 전용 검사
├── new-book.py                   # 새 책 저작 템플릿
└── sync-book.py                  # 외부 원고 명시적 가져오기
templates/book/                  # 장·검증 안내 템플릿
.github/workflows/               # 콘텐츠 PR 검사
```

각 책은 `content/<id>/`에 독립적으로 들어갑니다. `book.json`이 장 순서와 생성 출처의 원본이고, `index.md`와 각 장은 기여자가 직접 편집합니다. 원고를 읽고 검증할 때 Node.js나 웹사이트 빌드가 필요하지 않습니다.

## 원고 검증

Python 3.10 이상을 사용합니다. 기본 검사에는 외부 Python 패키지가 필요하지 않으며 CI는 Python 3.12를 사용합니다.

```powershell
python scripts/validate-books.py
```

검사기는 등록된 모든 책의 필수 정보, 생성·갱신 날짜, 모델 기록, 검증 범위, 연속된 장 번호와 파트 범위, 장·검증 안내·다운로드 파일 경로를 확인합니다. 원고, 목차와 메타데이터를 변경하지 않습니다. 책의 기술적 설명과 실습 실행 결과는 별도로 검토하고 해당 책의 검증 안내에 기록합니다.

## 수정과 새 책 추가

기존 글은 `content/<id>/`의 Markdown을 직접 수정하세요. 장을 추가하거나 순서를 바꾸면 `book.json`과 책 목차도 함께 수정합니다.

```powershell
python scripts/new-book.py --slug python-basics --title "Python 기초"
python scripts/validate-books.py
```

첫 장, 목차, `book.json`과 검증 안내가 생성됩니다. 같은 id의 폴더가 있으면 종료합니다. 템플릿의 임시 출처·설명을 실제 생성 정보·원고로 채운 뒤 PR을 제출하세요.

[book-generator](https://github.com/AI-Generation-Library/book-generator)는 자신의 OpenAI·Claude·Gemini API 키로 목차와 장별 원고를 작성하는 로컬 웹 화면·CLI입니다. 생성 후 내용을 검토하고 `book-generator export "<run-directory>" --books "<books-checkout>"`로 새 책을 가져올 수 있습니다. 기존 id를 덮어쓰지 않으며 [생성기 사용 안내](https://github.com/AI-Generation-Library/book-generator#books에-기여하기)에 전체 흐름이 있습니다.

외부에 작성한 원고를 가져올 때만 다음 명령을 사용합니다.

```powershell
python scripts/sync-book.py --source "../my-python-manuscript" --slug python-basics --title "Python 기초"
```

가져오기는 지정한 책의 같은 파일, 목차와 원고 ZIP을 갱신하는 저작 도구입니다. 먼저 변경을 커밋한 뒤 실행하세요. 임시 작업 공간에서 책 전체를 검증한 다음 대상에 적용하므로 잘못된 메타데이터는 기존 원고에 반영되지 않습니다. 원본과 다른 책을 수정하지 않으며, 원본에서 삭제된 파일을 자동으로 삭제하지 않습니다. CI와 웹사이트 빌드는 이 명령을 실행하지 않습니다.

## 온라인 서재에 반영되는 흐름

콘텐츠 PR 검사와 리뷰를 거쳐 `books/main`에 반영합니다. `library`는 별도 체크아웃한 이 저장소에서 `content/`와 검증 모듈을 읽고, 자신의 작업 공간에 복사한 콘텐츠로 목록·검색·진도용 manifest를 생성합니다. 생성된 웹 파일은 이 저장소에 커밋하지 않습니다. 저장소 역할과 연동은 [ARCHITECTURE.md](ARCHITECTURE.md)에 있습니다.

## 출처와 라이선스

각 책은 `book.json`에 생성 도구, 확인된 모델, 날짜, 입력 자료와 실제 검증 범위를 남깁니다. 확인할 수 없는 모델명은 `null`로 기록합니다. 실행 환경과 확인 범위는 해당 책의 검증 안내를 참고하세요.

기존 CC0 1.0 Universal [LICENSE](LICENSE)를 그대로 보존합니다. 포함한 제삼자 자료와 예제의 출처·라이선스 표시는 해당 파일과 함께 유지해야 합니다. Quartz·웹 테마의 MIT 라이선스 및 의존성은 `library`에서 관리합니다.
