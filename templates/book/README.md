# 새 책 템플릿

저장소 루트에서 다음을 실행하면 이 템플릿으로 책 한 권의 폴더가 만들어집니다.

```powershell
python scripts/new-book.py --slug python-basics --title "Python 기초"
```

`content/python-basics/book.json`의 출처·검증 정보와 실제 원고를 작성하세요. 장을 추가하면 `chapters`와 `parts`도 갱신하세요. 파일명이 `chapter.md`여야 하는 것은 아니지만 `href`는 책 폴더 상대 경로이며 `.md`를 생략합니다.

`python scripts/validate-books.py`로 등록 정보와 경로를 확인합니다. 검사는 원고나 목차를 변경하지 않습니다. 임시 설명·출처를 실제 정보로 채운 뒤 PR을 제출하세요. 서재 목록·검색·웹 manifest는 별도 `library` 저장소의 빌드에서 생성합니다.
