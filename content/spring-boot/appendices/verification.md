---
title: "검증 결과와 제한"
enableToc: true
---

## 기준과 실제 결과

검증일은 2026-11-01(Asia/Seoul)이다. Codex가 자동 실행과 원고 대조를 수행했으며 독립적인 사람의 전체 검수를 주장하지 않는다. 원고 상태는 draft, 검토 상태는 automated-checked다.

- Windows 11 / Temurin OpenJDK 21.0.11 / Maven 3.9.11 / Spring Boot 4.1.2.
- `mvn verify`: Java main 9개·test 4개 컴파일, 테스트 23개 통과. 실패 0·오류 0·skip 0. 실행 JAR 패키징 성공.
- DiTests 2개, ReservationTests 7개, TransactionTests 8개, HttpTests 6개.
- 실제 패키징 JAR를 별도 프로세스로 실행해 HTTP 시나리오 10건 통과: 생성·재시도·키 충돌·품절·입력 오류·없는 SKU·소유권·역할 거절·마지막 재고·추가 품절.
- 재고 5에서 12건 동시 요청: 성공 5·OUT_OF_STOCK 7·최종 재고 0·예약 5행·Outbox 5행을 테스트에서 확인.
- checked exception 기본 commit, rollbackFor에 의한 취소, RuntimeException rollback, 같은 메서드 catch의 commit, 내부 REQUIRED 실패 후 rollback-only, REQUIRES_NEW 독립 commit, 외부 호출/자기 호출의 활성 상태를 확인.

테스트 이름·해석된 실행 라이브러리·실제 HTTP 상태는 [구조화된 검증 결과](verification-results.json)에 기록했다. 공식 참고 URL 74개는 읽기 전용 접속에서 모두 HTTP 200을 확인했다. 링크가 열리는 것과 그 문서의 모든 설명을 검증하는 것은 다른 범위다.

테스트 실행에는 공개 Maven 의존성 다운로드와 localhost 서버 바인딩이 필요했다. 제한 실행 환경에서는 DNS·서버 바인딩 때문에 실패했고, 네트워크와 로컬 포트 사용이 가능한 실행 환경에서 위 결과를 확인했다. 이 환경 오류를 제품 코드 실패나 테스트 skip으로 숨기지 않았다.

## 실행 명령

```powershell
cd examples/reservation-api
java -version
mvn -version
mvn verify
$env:APP_DEMO_PASSWORD = 'local-practice-change-me'
java -jar target/reservation-api-1.0.0.jar
```

실제 HTTP 재현은 [예제 README](../examples/reservation-api/README.md)의 CSRF 쿠키·헤더 명령을 따른다. 인메모리 H2 초기값을 전제로 하므로 별도 프로세스에서 새로 실행한다. Windows의 테스트 프로세스 종료는 Linux SIGTERM graceful shutdown 검증으로 간주하지 않는다.

## 원고·패키지 검사

`books/scripts/validate-books.py`로 최신 main의 기존 5권과 신규 Spring Boot를 합친 총 6권의 메타데이터 검사를 통과했다. 별도로 26장 frontmatter·목차 경로·장 순서·상대 링크 대상·코드 펜스와 ZIP의 CRC·원본 바이트 일치를 확인했다. library의 콘텐츠 준비와 전체 정적 사이트 빌드도 완료했다. 콘텐츠 검사 성공을 기술 내용 전체 검수로 확대하지 않는다.

ZIP에는 원고·예제 소스·설정·메타데이터만 넣는다. target·Maven 캐시·실행 로그·개인 경로·비밀 키·실제 DB·실행 JAR은 포함하지 않는다. 다운로드 ZIP 안의 downloads 링크는 웹 원고를 위한 것이며 ZIP을 재귀적으로 중첩하지 않는다.

## 확인하지 않은 범위

- PostgreSQL/MySQL의 실제 격리·락·교착·쿼리 계획·마이그레이션. H2 성공을 목표 DB 결과로 주장하지 않는다.
- 본문의 JPA·EntityGraph·OSIV·NESTED 등 별도 확장 예제 전체 실행과 모든 부분 코드의 독립 컴파일.
- Redis 캐시, JWT IdP, 실제 결제, 브로커·Outbox 발행/소비·CDC·다중 작업자·재전달.
- Docker 이미지 빌드와 실행, Linux 종료 신호, 클라우드·TLS·운영 부하·백업 복원·네트워크 분할.
- 전체 사람 검수, 실제 서비스의 보안 심사와 성능 보장.

통합 예제는 루프백용 메모리 DB·데모 계정이다. 원고가 외부 시스템 설계를 설명한다는 사실과 그 인프라를 구현·검증했다는 사실을 구분한다. 미래 패치 버전의 동작도 다시 확인해야 한다.

[책 목차](../index.md)
