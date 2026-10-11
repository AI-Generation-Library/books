# 새 책 템플릿

저장소 루트에서 다음을 실행하면 이 템플릿으로 책 한 권의 폴더가 만들어집니다.

```powershell
python scripts/new-book.py --slug python-basics --title "Python 기초"
```

`content/python-basics/book.json`의 출처·검증 정보와 실제 원고를 작성하세요. 장을 추가하면 `chapters`와 `parts`도 갱신하세요. 파일명이 `chapter.md`여야 하는 것은 아니지만 `href`는 책 폴더 상대 경로이며 `.md`를 생략합니다.

`npm run build`는 등록 목록과 서재 카드만 갱신하며 직접 작성한 장이나 책 목차를 덮어쓰지 않습니다. 생성된 임시 템플릿도 공개 빌드에 포함되므로 실제 원고로 채운 뒤 PR을 제출하세요.
