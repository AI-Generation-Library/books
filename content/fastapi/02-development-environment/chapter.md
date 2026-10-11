---
title: "02장. 개발 환경 구성"
description: "이 장에서는 Python 실행 파일과 패키지 설치 위치를 일치시키고, 독립된 개발 환경을 만들고, 서버 실행과 디버깅을 재현한다. 설치에 성공했다는 메시지보다 실제 어느 인터프리터가 어떤 패키지를 가져오는지가 중요하다."
tags: ["FastAPI"]
created: "2026-10-10"
modified: "2026-10-11"
enableToc: true
chapter: 2
part: 1
---

> PART 1. FastAPI 시작하기

## 학습 목표와 도입 사례

이 장에서는 Python 실행 파일과 패키지 설치 위치를 일치시키고, 독립된 개발 환경을 만들고, 서버 실행과 디버깅을 재현한다. 설치에 성공했다는 메시지보다 실제 어느 인터프리터가 어떤 패키지를 가져오는지가 중요하다.

팀원 한 명의 컴퓨터에서는 서버가 실행되는데 다른 컴퓨터에서는 `ImportError`가 발생한다고 생각해 보자. 소스 코드가 같아도 인터프리터, 패키지 버전, 현재 디렉터리, 환경변수가 다르면 프로그램은 다르다. 개발 환경 설정은 이런 숨은 입력을 명시하는 과정이다.

## 2.1 Python 버전과 패키지 관리

이 책은 Python 3.12 문법을 기준으로 한다. Python의 마이너 버전이 바뀌면 언어 기능뿐 아니라 네이티브 확장용 wheel의 지원 여부도 달라질 수 있다. “가장 새 버전”보다 프로젝트가 검증한 버전을 먼저 선택한다. 실제 설치 버전은 다음으로 확인한다.

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
```

세 명령이 가리키는 환경이 일치해야 한다. `pip`만 실행하면 PATH에 먼저 잡힌 다른 Python의 도구를 사용할 수 있다. `python -m pip`는 선택한 Python으로 pip 모듈을 실행하므로 이 혼동을 줄인다. Windows에 여러 Python이 설치되어 있다면 `py -3.12`로 버전을 선택할 수도 있다. 이는 Python Launcher가 설치된 경우에 해당한다.

직접 의존성은 소스에서 사용한 패키지다. 전이 의존성은 그 패키지가 요구하는 패키지다. FastAPI를 설치하면 웹 기반 처리와 데이터 모델에 필요한 의존성도 해결된다. 전이 의존성을 모두 수동으로 고정하기 전에 공식 호환 범위를 확인한다.

## 2.2 venv와 가상환경의 필요성

가상환경은 프로젝트가 사용할 인터프리터 설정과 패키지 설치 경로를 분리한다. 프로젝트 A가 쓰는 라이브러리와 B가 쓰는 라이브러리가 전역 환경에서 서로 덮어쓰는 일을 줄인다. 가상환경은 운영체제나 네트워크까지 격리하는 컨테이너가 아니다. 파일과 환경변수는 여전히 같은 컴퓨터의 규칙을 따른다.

**완전 실행 절차.** PowerShell에서 다음을 실행한다.

```powershell
New-Item -ItemType Directory knowledge-hub
Set-Location knowledge-hub
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "fastapi>=0.121,<1" "uvicorn>=0.30,<1" "pydantic>=2,<3"
```

환경 활성화 없이 실행 파일의 전체 상대 경로를 사용했다. PowerShell 실행 정책 때문에 활성화 스크립트가 막혀도 이 방식으로 실습할 수 있다. 활성화를 원하면 현재 조직의 정책에 맞게 `.\.venv\Scripts\Activate.ps1`을 실행한다. 설치를 위해 보안 정책을 무조건 전역 완화하지 않는다.

Linux/macOS의 대응 명령은 다음과 같다.

```bash
mkdir knowledge-hub
cd knowledge-hub
python3.12 -m venv .venv
.venv/bin/python -m pip install "fastapi>=0.121,<1" "uvicorn>=0.30,<1" "pydantic>=2,<3"
```

`venv`의 구조와 동작은 [Python 공식 문서](https://docs.python.org/3.12/library/venv.html)에서 확인할 수 있다. 환경 폴더는 소스 관리에 넣지 않고 다른 환경에서는 의존성 파일로 다시 만든다.

## 2.3 pip, uv, Poetry 비교

pip는 패키지 설치의 기본 도구이며 단순한 실습에 충분하다. venv와 함께 쓰면 실행 환경도 분리할 수 있다. 하지만 범위만 적은 requirements 파일은 미래 설치 결과가 달라질 수 있다. 검증한 환경을 기록하려면 잠금 정책이 추가로 필요하다.

uv는 환경·패키지·프로젝트 작업을 통합해서 다루는 도구이고, Poetry는 프로젝트 메타데이터와 의존성 해결·잠금을 중심으로 구성할 수 있다. 어느 도구를 쓰든 팀이 한 방식을 정하고 잠금 파일을 커밋하는 것이 중요하다. 설치 속도만 비교하고 업데이트·보안 패치·CI 재현 과정을 빼면 전체 비용을 놓친다.

| 상황 | 이 책의 기본 선택 | 판단 이유 |
|---|---|---|
| 처음 배우는 작은 실습 | venv + pip | 실행 파일과 설치 위치를 직접 관찰하기 쉽다 |
| 여러 개발자·CI가 공유하는 프로젝트 | 프로젝트 도구 + 잠금 파일 | 의존성 해결 결과를 공유한다 |
| 라이브러리 배포 | pyproject.toml 중심 메타데이터 | 설치 계약과 배포 설정을 명시한다 |

uv와 Poetry의 명령은 도구 버전에 따라 달라질 수 있으므로 [uv 프로젝트 문서](https://docs.astral.sh/uv/guides/projects/)와 [Poetry 기본 사용법](https://python-poetry.org/docs/basic-usage/)을 확인한다. 이미 팀이 쓰는 도구가 있다면 실습 때문에 별도 도구를 섞을 필요는 없다.

## 2.4 FastAPI 프로젝트 생성

초기 프로젝트를 다음과 같이 구성한다. `.env`에는 비밀이 들어갈 수 있어 Git에서 제외하고, `.env.example`에는 변수 이름과 안전한 예시만 넣는다.

```text
knowledge-hub/
├── app/
│   ├── __init__.py
│   └── main.py
├── requirements.in
├── requirements.lock.txt
├── .env.example
└── .gitignore
```

**완전 실행 예제.** `app` 폴더와 빈 `app/__init__.py`를 만든 뒤 `app/main.py`를 저장한다.

```python
from fastapi import FastAPI

app = FastAPI(title="Knowledge Hub", version="0.1.0")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

`requirements.in`은 의도한 직접 의존성을 적는 교육용 입력 파일이다.

```text
fastapi>=0.121,<1
uvicorn>=0.30,<1
pydantic>=2,<3
```

`.gitignore`의 예시는 다음과 같다.

```gitignore
.venv/
__pycache__/
.pytest_cache/
.env
*.db
```

현재 설치 상태는 `.\.venv\Scripts\python.exe -m pip freeze`로 확인한다. 다음처럼 파일에 저장할 수 있다.

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 requirements.lock.txt
```

`pip freeze` 결과는 현재 설치 상태의 스냅샷이다. 플랫폼별 조건과 패키지 해시까지 보장하는 정교한 잠금 파일은 아니다. 실무에서는 잠금 도구, 업데이트 절차, 취약점 검사, CI 검증을 연결한다. “버전을 고정하면 영원히 안전하다”는 뜻도 아니다.

## 2.5 Uvicorn으로 개발 서버 실행

프로젝트 루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`app.main:app`의 앞부분은 Python 모듈 경로이고 뒷부분은 그 모듈에서 가져올 객체 이름이다. `app/main.py`라는 파일 경로를 그대로 넘기는 문법이 아니다. 현재 디렉터리가 달라지면 모듈 검색 경로가 달라질 수 있다. 서버가 시작되지 않으면 우선 프로젝트 루트와 `__init__.py`, 인터프리터를 확인한다.

`127.0.0.1`은 로컬 접근에 적합한 바인딩이다. `0.0.0.0`은 모든 인터페이스에 바인딩하므로 컨테이너 배포에 자주 쓰지만 네트워크 접근 범위가 달라진다. 접속 URL에 `0.0.0.0`을 쓰는 것과 바인딩 설정은 구분한다. 포트가 사용 중이면 다른 프로세스를 확인하거나 포트를 바꾼다.

`http://127.0.0.1:8000/health`를 요청하면 `{"status":"ok"}`가 나온다. `/docs`는 API 실험 화면, `/openapi.json`은 기계가 읽는 계약이다. 서버 로그에 요청이 찍히지 않으면 앱 내부 오류보다 URL·포트·프록시를 먼저 확인한다.

## 2.6 자동 리로드와 개발 환경 설정

리로드는 소스 변경을 감지해 서버 프로세스를 다시 실행한다. 메모리 데이터가 유지된다는 보장이 없다. 시작 때 등록한 모델이나 연결도 다시 생성된다. 파일을 저장할 때마다 비싼 작업을 수행한다면 개발 체감 속도가 느려지는 이유가 된다.

리로드와 여러 워커를 동시에 운영 설정처럼 조합하지 않는다. 개발은 빠른 피드백, 운영은 예측 가능한 프로세스 수명과 종료를 목표로 한다. Uvicorn 옵션의 호환 관계는 [공식 설정](https://www.uvicorn.org/settings/)을 기준으로 확인한다.

환경변수는 프로세스 시작 때 읽는 외부 입력이다. 셸에서 값을 바꾸어도 이미 실행 중인 프로세스의 설정이 자동 갱신되는 것은 아니다. `.env` 파일도 그 파일을 읽는 코드나 도구가 있어야 적용된다. 9장에서 `pydantic-settings`를 사용해 타입 있는 설정을 만든다.

## 2.7 VS Code 디버깅 환경 구성

VS Code에서 프로젝트 폴더를 열고 Python 인터프리터로 `.venv`를 선택한다. 편집기의 선택과 터미널의 PATH는 따로 움직일 수 있으므로 터미널에서도 `sys.executable`을 확인한다. 자동완성이 정상이라고 실제 실행 환경도 정상이라는 뜻은 아니다.

**설정 예제.** Python 디버거 확장이 설치된 환경에서 `.vscode/launch.json`을 다음처럼 작성한다.

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Knowledge Hub: Uvicorn",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--host", "127.0.0.1", "--port", "8000"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

처음 디버깅할 때는 리로드를 빼서 자식 프로세스와 중단점의 혼동을 줄인다. `health`의 반환 줄에 중단점을 걸고 요청해 보자. 매개변수와 호출 스택을 확인한 다음 계속 실행한다. 중단점에서 이벤트 루프를 멈추면 다른 요청도 지연될 수 있다. 디버거 아래에서 얻은 시간을 성능 측정값으로 사용하지 않는다.

## 실무 적용: 환경 재현의 네 가지 입력

코드 커밋, Python 버전, 의존성 잠금, 설정 변수 목록을 함께 기록한다. 여기에 DB 스키마 버전이 더해지면 서버의 실행 조건을 비교할 수 있다. 장애를 “내 컴퓨터에서는 된다”로 닫지 말고 이 입력 중 무엇이 다른지 찾는다.

CI에서는 깨끗한 환경을 만들고 의존성을 설치한 뒤 테스트를 실행한다. 개발자 개인 환경에 우연히 설치된 패키지가 테스트를 통과시키지 않도록 한다. 운영 배포에서는 리로드를 제거하고 설정 유효성 실패가 시작 시 명확히 드러나게 만든다.

## 성능 및 흔한 함정

패키지 설치는 요청 처리 경로에 넣지 않는다. 모듈 import 시 외부 API를 호출하면 테스트·리로드·워커 시작이 네트워크에 종속된다. 리소스 초기화가 필요한 경우 5장의 lifespan으로 옮긴다. 시작 실패를 숨기고 반쯤 준비된 서버를 띄우는 것보다 준비 상태를 명시하는 편이 운영하기 쉽다.

가상환경 폴더를 다른 컴퓨터로 복사하면 절대 경로나 플랫폼 차이 때문에 깨질 수 있다. 소스와 잠금 정보를 전달해 다시 만드는 것이 기본이다. `main.py`와 같은 이름뿐 아니라 `fastapi.py`, `typing.py`, `jwt.py` 등 라이브러리를 가리는 파일명도 피한다.

## 확인 문제와 해설

1. 패키지를 설치했는데 `ModuleNotFoundError`가 난다. 가장 먼저 비교할 경로는?
2. 리로드 후 메모리 문서 목록이 사라지는 이유는?
3. `requirements.in`의 버전 범위만으로 같은 환경을 재현하기 어려운 이유는?
4. 실습: 포트를 8001로 바꾸고 디버거에서 건강 검사 중단점을 확인하라.

**해설.** 1번은 실행 Python의 `sys.executable`과 설치 pip 경로를 비교한다. 2번은 프로세스가 다시 만들어지기 때문이다. 3번은 같은 범위 안에 새 버전과 다른 전이 의존성이 선택될 수 있기 때문이다. 4번은 요청 URL도 8001로 바꾸고 리로드 없이 디버깅한다. 서버 로그, 중단점, JSON 응답을 모두 확인하면 완료다.

## 요약과 다음 장

환경은 프로그램의 입력이다. 인터프리터와 패키지 설치 위치를 일치시키고, 프로젝트 환경을 분리하고, 검증한 의존성을 기록해야 실행 결과를 비교할 수 있다. 다음 장에서는 HTTP 메서드와 입력 위치를 실제 API로 구현한다.

## 공식 참고자료

- [Python venv](https://docs.python.org/3.12/library/venv.html)
- [pip 사용자 가이드](https://pip.pypa.io/en/stable/user_guide/)
- [Uvicorn 설정](https://www.uvicorn.org/settings/)
- [VS Code Python 디버깅](https://code.visualstudio.com/docs/python/debugging)
- [uv 프로젝트 가이드](https://docs.astral.sh/uv/guides/projects/)
- [Poetry 기본 사용법](https://python-poetry.org/docs/basic-usage/)

<!-- book-navigation -->

---

[전체 목차](../index.md) · [← 01장 FastAPI란 무엇인가?](../01-fastapi-introduction/chapter.md) · [03장 첫 번째 REST API 개발 →](../03-first-rest-api/chapter.md)
