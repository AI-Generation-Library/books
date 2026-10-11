# AI Generation Library

AI로 생성한 책을 Markdown 원고와 실습 코드로 공개하고, 함께 읽으며 개선하는 오픈소스 서재입니다. 책마다 생성 출처와 실제 검증 범위를 기록합니다.

[서재](https://ai-generation-library.github.io/books/) · [FastAPI 완전 정복](https://ai-generation-library.github.io/books/fastapi/) · [기여 안내](CONTRIBUTING.md)

첫 번째 책은 **FastAPI 완전 정복**입니다. 7부·30장으로 Python 비동기, API 설계, 데이터베이스, 인증, 성능 측정, 운영, RAG와 Agent 서버를 다룹니다. 장별 예제와 Knowledge Hub 통합 실습을 제공합니다.

## 저장소 구조

```text
content/
├── index.md                     # 공통 서재 홈
├── static/library-manifest.json  # 생성된 전체 책 등록 목록
└── fastapi/
    ├── book.json                # 책 정보·출처·장 목록의 원본
    ├── index.md                 # 책 목차와 안내
    ├── 01-fastapi-introduction/
    │   ├── index.md             # 폴더 안내
    │   └── chapter.md           # 직접 수정하는 원고
    ├── …
    ├── appendices/
    ├── downloads/
    └── static/book-manifest.json # 생성된 책별 읽기 진도 목록
scripts/                         # 등록·가져오기·검증 도구
templates/book/                  # 새 책의 장·검증 안내 템플릿
quartz/                          # 공통 사이트 코드와 테마
.github/workflows/               # PR 검증 및 GitHub Pages 배포
```

책마다 `content/<slug>/` 폴더를 사용합니다. 사이트 디자인, 전체 검색, 코드 복사, Mermaid, 다크 모드와 배포 구성을 공유하고, 읽기 진도와 이어서 읽기는 책별로 저장합니다. 진도는 현재 브라우저의 localStorage에 보관됩니다.

## 로컬 실행

Node.js 22 이상, npm 10.9.2 이상, Python 3.10 이상을 사용합니다. CI는 Node 24와 Python 3.12를 사용합니다.

```powershell
npm ci
npm run dev
```

`http://localhost:8080`에서 서재를 볼 수 있습니다. 정적 파일 빌드와 링크 검사는 다음과 같습니다.

```powershell
npm run build
python scripts/check-output.py --base-path /books/
```

출력 폴더는 `dist/`입니다. 빌드가 다시 생성하는 폴더이므로 개인 파일을 넣지 않습니다. `npm run dev`와 `npm run build`는 `book.json`을 확인해 책별 manifest, 전체 등록 목록과 서재의 책 카드만 갱신합니다. 장 원고와 책의 `index.md`는 직접 작성한 내용을 유지합니다.

## 글 수정과 새 책 추가

원고는 `content/<slug>/`의 Markdown을 직접 수정합니다. 기존 FastAPI 글의 예는 `content/fastapi/06-asyncio-event-loop/chapter.md`입니다. 제목·설명·장 번호는 파일 앞의 frontmatter에 있고, 장 목록과 파트 범위는 `book.json`에 있습니다.

```powershell
python scripts/new-book.py --slug python-basics --title "Python 기초"
```

새 책의 목차, 첫 장, 출처·검증 안내가 만들어집니다. 기존 책 폴더가 있으면 덮어쓰지 않습니다. 생성된 원고를 작성하고 `book.json`의 출처와 장 목록을 수정한 뒤 `npm run build`하면 서재에 자동으로 등록됩니다. 여러 책의 장 수는 서로 달라도 됩니다.

이미 별도로 작성한 원고를 가져오려면 **명시적으로** 다음 명령을 실행합니다.

```powershell
python scripts/sync-book.py --source "../my-python-manuscript" --slug python-basics --title "Python 기초"
```

이 명령은 지정한 책 폴더의 같은 파일, 책 목차와 원고 ZIP을 원본으로 갱신합니다. 해당 폴더를 직접 편집했다면 먼저 변경을 커밋하세요. 다른 책의 원고와 가져온 원본은 변경하지 않습니다. 가져오기 명령은 빌드에 포함되지 않습니다. 원고에 `book.json`이 있으면 그 장 목록을 사용하고, 없으면 README의 번호가 있는 Markdown 링크 또는 각 폴더의 `chapter.md`로 장을 찾습니다. 외부 원고에서 삭제된 파일은 대상 폴더에서 자동 삭제하지 않습니다.

## 기여와 배포

오류 수정, 설명 개선과 새 책 추가는 PR로 받습니다. 작성 형식, 생성 정보와 검증 결과 기록 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있습니다. PR CI는 등록 정보, 정적 빌드, 모든 책의 장·다운로드와 내부 링크를 검사합니다.

`main`에 push하면 GitHub Actions가 빌드하고 GitHub Pages로 배포합니다. [Pages 설정](https://github.com/AI-Generation-Library/books/settings/pages)의 **Source**는 **GitHub Actions**를 사용합니다. 워크플로가 실제 Pages 주소를 Quartz `baseUrl`에 반영합니다.

## 출처와 라이선스

각 책의 `book.json`에는 AI 생성 도구, 확인된 모델, 날짜, 입력 자료와 검증 범위가 있습니다. 알 수 없는 모델은 `null`로 표시합니다. 공개된 원고의 존재와 모든 예제의 운영 환경 검증 완료는 구분합니다. 첫 책의 자세한 실행 환경과 확인한 범위는 [FastAPI 검증 안내](content/fastapi/appendices/verification.md)에 있습니다.

이 저장소에 처음 있던 CC0 1.0 Universal [LICENSE](LICENSE)를 그대로 보존했습니다. 공통 사이트는 `study-log`에서 사용하던 Quartz 구성을 기반으로 합니다. Quartz와 재사용 코드의 MIT [LICENSE.txt](LICENSE.txt)를 별도로 유지하며, 개별 의존성은 각각의 라이선스를 따릅니다.
