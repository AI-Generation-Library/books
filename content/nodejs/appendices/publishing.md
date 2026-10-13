---
title: "npm 패키지 제작과 배포"
description: "공개 API·포장 내용·권한을 확인한 뒤 실제 배포합니다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
enableToc: true
---

# npm 패키지 제작과 배포

## 예제와 배포 패키지를 구분한다

이 책의 예제는 private:true이며 배포하지 않는다. 재사용 라이브러리를 별도 패키지로 만들려면 이름·라이선스·지원 런타임·공개 API·타입 선언·문서·변경 정책을 먼저 정한다. 서버 실행과 외부 연결을 import 부수 효과로 만들지 않는다.

exports로 공개 진입점을 제한하고 files로 배포할 파일을 명시한다. 소스·빌드 결과 중 무엇을 제공할지 정하고, 타입 경로가 실제 파일을 가리키는지 확인한다. ESM과 CommonJS를 함께 지원한다면 두 소비 환경과 상태 공유 방식을 각각 검사한다.

## 공개될 파일 확인

```sh
npm pack --dry-run
```

실제 배포 전에 파일 목록을 확인한다. .env·테스트 비밀·개인 자료·진단 파일이 섞이지 않았는지 보고, 새 임시 소비 프로젝트에 패키지 tarball을 설치해 README 예제가 동작하는지 확인한다. 레포의 테스트 통과와 포장된 패키지 사용 성공은 다르다.

## 버전과 권한

호환성을 깨는 공개 API 변경은 버전 정책에 반영한다. 이름만 같은 수정이라도 오류 타입·반환값·기본 동작이 달라지면 소비자에게 영향이 있다. 변경 기록과 마이그레이션 안내를 제공한다.

실제 publish는 공개 상태를 바꾸는 별도 행위다. 이 책을 작성하면서 npm에 배포하지 않았다. 패키지 소유권·현재 npm 인증 정책·2단계 인증·trusted publishing 지원을 공식 안내로 확인하고 최소 권한으로 수행한다. 자동화 토큰을 소스에 넣지 않는다.

[공식 package.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-json) · [npm pack](https://docs.npmjs.com/cli/v11/commands/npm-pack) · [trusted publishing](https://docs.npmjs.com/trusted-publishers)
