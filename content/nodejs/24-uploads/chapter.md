---
title: "24장. 파일 업로드와 대용량 데이터 처리"
description: "전송 형식·바이트 상한·저장 이름·내용 검증을 분리한다. 파일 저장과 DB 기록 사이의 장애를 다룬다."
tags: ["Node.js", "한국어"]
created: "2026-10-14"
modified: "2026-10-14"
chapter: 24
part: 5
enableToc: true
---

# 24장. 파일 업로드와 대용량 데이터 처리

## 학습 목표

- 전송 형식·바이트 상한·저장 이름·내용 검증을 분리한다.
- 파일 저장과 DB 기록 사이의 장애를 다룬다.

## 원시 업로드와 멀티파트

API 클라이언트가 파일 하나를 보내면 `application/octet-stream` 원시 본문으로 계약을 단순하게 만들 수 있다. 브라우저 폼처럼 파일과 여러 필드를 함께 보내려면 multipart/form-data를 사용한다. 멀티파트의 경계 문자열과 스트림 상태를 직접 split하는 방식은 바이너리·청크 경계에서 오류가 나기 쉬우므로 검증된 파서를 사용한다.

종합 프로젝트는 UTF-8 텍스트 파일 하나를 원시 업로드로 받는다. 멀티파트는 본문 설명 범위이며 실행 프로젝트에 구현했다고 기록하지 않는다. 멀티파트 파서를 도입할 때는 전체 요청·파일별 크기·파일 개수·필드 개수 제한을 각각 설정하고 중단된 스트림도 처리한다.

## 파일을 메모리에 모으지 않기

업로드 함수는 요청 스트림 → 바이트 제한 Transform → 파일 쓰기를 `pipeline`으로 연결한다. 서버가 생성한 UUID를 저장 이름으로 사용하고 `wx`로 새 파일만 만든다. 실제 구현은 [files.mjs](../examples/src/files.mjs)에 있다.

```js
let received = 0;
const limit = new Transform({
  transform(chunk, encoding, done) {
    received += chunk.length;
    done(received > maxBytes ? new Error('too large') : null, chunk);
  }
});
```

Content-Length를 사전 검사하더라도 실제 수신량 제한은 유지한다. 헤더가 없을 수 있고, 프록시·청크 전송·악의적 입력이 개입할 수 있다. 수신 기한과 동시에 진행되는 업로드 수도 별도로 제한한다. 파일당 1MiB여도 수십만 파일을 저장하면 디스크를 채울 수 있다.

## 이름·내용·권한의 경계

클라이언트 파일명을 저장 경로로 쓰지 않는다. 확장자와 요청 MIME만으로 안전한 내용이라고 믿지 않는다. 이 예제는 worker의 엄격한 UTF-8 디코딩으로 텍스트 계약을 확인하며 HTML 렌더링이나 사용자 파일 공개 기능을 제공하지 않는다.

파일을 직접 웹에서 제공한다면 전용 출처·다운로드 헤더·허용 형식·악성코드 검사·권한 확인 등을 요구사항에 맞춰 추가한다. 압축 해제 기능은 압축 폭탄·경로 탈출·해제 크기·파일 수의 새로운 경계를 만든다. 단순 업로드 예제에 조용히 섞지 않는다.

## 두 저장소 사이의 실패

파일이 쓰인 뒤 DB 접수가 실패하면 파일은 남을 수 있다. 예제는 전송 실패 시 부분 파일을 지우고 작업을 failed로 바꾸지만, DB 장애와 프로세스 크래시를 포함한 모든 시점의 정리를 원자적으로 보장하지는 않는다. uploading 상태의 기한, 고아 파일 점검, 보관 기간과 삭제 작업이 필요하다.

서로 다른 호스트의 API와 worker가 같은 로컬 경로를 읽을 수는 없다. Compose는 같은 호스트의 공유 볼륨을 사용한다. 여러 호스트로 확장하려면 객체 저장소와 권한·업로드 완료 확인·내용 해시·수명 정책을 설계한다. 공유 볼륨을 객체 저장소와 같은 것으로 설명하지 않는다.

## 실습과 관찰

기본 테스트는 초과 업로드의 부분 파일 삭제, 경로 조작 거부, 잘못된 UTF-8 실패를 확인한다. Content-Length가 없는 chunked 요청에서 연결이 종료될 수 있는 점은 스트림 수명과 함께 해석한다.

다음 단계 실습으로 파일별 제한 외에 사용자별 보관 바이트 합과 동시 업로드 개수를 추가할 수 있다. DB 기록과 파일 삭제가 실패할 때 재실행에 안전한지도 설계한다.

## 확인 문제

파일당 크기를 제한했으니 디스크 고갈 문제도 해결되었는가?

[해설 보기](../appendices/answers.md#장-24)

## 공식 자료

기준일: 2026-10-14. 원문을 복제하지 않고 개념을 설명하고 예제를 새로 작성했다.

- [Stream | Node.js v24.21.0 Documentation](https://nodejs.org/docs/latest-v24.x/api/stream.html)
- [File Upload - OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [GitHub - mscdex/busboy: A streaming parser for HTML form data for node.js · GitHub](https://github.com/mscdex/busboy#api)

---

[이전 장](../23-realtime/chapter.md) · [책 목차](../index.md) · [다음 장](../25-threads-processes/chapter.md)
