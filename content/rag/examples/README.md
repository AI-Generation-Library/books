# RAG 완전 정복 · 실행 예제

Python 3.12를 기준으로 한다. 문서·평가 질문은 저자가 만든 가상 데이터다. 규정·수치는 실제 회사나 법률 정보가 아니다. 명령은 이 디렉터리에서 실행한다. [실제 검증 기록](../appendices/verification.md)과 [구현 범위](ARCHITECTURE.md)를 함께 확인한다.

## 설치

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

이후의 `python`은 이 가상환경의 Python을 뜻한다. PowerShell 활성화가 제한되면 `.venv\Scripts\python.exe`를 직접 사용한다. Windows 출력 인코딩이 맞지 않으면 `python -X utf8 ...`로 실행한다. 전이 의존성까지 고정한 집필 환경 snapshot은 requirements-lock.txt다. 선택형 모델·프레임워크 의존성도 포함한다. 다른 OS와 Python 버전에서 동일 동작을 검증했다고 표시하지 않는다.

```powershell
python -m unittest discover -s tests -v
python -m ragbook.cli index
python -m ragbook.cli query "연차 휴가는 연간 며칠인가요?"
python -m ragbook.cli evaluate --split dev --mode bm25
python -m ragbook.cli evaluate --split test --mode hybrid
python -m demos.metrics
```

기본 모드는 문자 2-gram 해시 벡터와 원문 발췌다. **학습된 의미 임베딩·LLM 생성으로 표시하지 않는다.** 응답의 generator는 extractive-demo-not-llm이다. BM25·RRF·MMR·벡터 수학·SQLite·인용 검사는 핵심 코드에서 읽을 수 있다. 전체 테스트는 API·PDF 파서 때문에 기본 의존성이 필요하다.

## 실제 다국어 임베딩

```powershell
python -m pip install -r requirements-models.txt
python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 index
python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 query "연차 휴가는 연간 며칠인가요?"
python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 evaluate --split dev --mode dense
```

처음 실행할 때 FastEmbed가 공개 ONNX 모델을 model-cache에 내려받는다. 기본 선택은 sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2다. 모델 캐시와 가중치는 Git/ZIP에 포함하지 않는다. 다운로드·CPU·메모리가 필요하며 오프라인에서는 미리 준비한 같은 캐시가 있어야 한다.

signature는 모델명·FastEmbed 버전·ONNX/토크나이저 파일 해시를 포함한다. 같은 캐시에는 해당 embedding 모델만 두고, 파일이나 모델이 바뀌면 새 DB를 만든다. 기본 DB를 neural 모드로 억지로 열지 않는다. source/offset은 정규화 문자 기준이며 PDF 화면 좌표가 아니다.

## 선택형 다국어 리랭커

```powershell
python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 --rerank query "연차 휴가는 연간 며칠인가요?"
```

BAAI/bge-reranker-v2-m3-int8 ONNX 모델을 별도 cache 경로에 내려받는다. 후보 최대 20개를 재정렬한다. 점수는 확률이 아니다. 실제 실행 결과·모델 파일 해시는 검증 자료를 따른다. 기본 경로에서는 리랭커를 자동 다운로드하지 않는다.

## 실제 로컬 LLM 생성

Ollama와 지원되는 로컬 모델을 별도로 준비한다. 집필 환경에 이미 설치되어 있던 qwen3.5:4b로 확인했다. 이 예제는 Ollama나 생성 가중치를 자동 설치하지 않는다.

```powershell
python -m ragbook.cli --embedding neural --db var/index-neural.sqlite3 --model qwen3.5:4b --rerank query "연차 휴가는 연간 며칠인가요?"
```

localhost Ollama API만 허용하며 외부 유료 모델을 자동 호출하지 않는다. think=false, temperature=0, num_predict=768, num_ctx=4096을 전달하고 JSON claims를 검증한다. 다른 모델이 같은 필드·출력 계약을 지원하는지는 다시 확인한다. quote 부분 문자열·출처 검사만으로 주장 전체의 의미적 정확성이 증명되지 않는다.

## API와 화면

```powershell
python serve.py
```

127.0.0.1:8000에 학습용 화면과 /docs가 열린다. reader-local-token·admin-local-token은 **가상 문서 localhost 학습용** 값이다. 실제 인증 제공자·운영 비밀·TLS·요청 바이트 제한을 대체하지 않는다. UI는 토큰을 브라우저 저장소에 보관하지 않는다.

실제 모델 API 모드는 별도 터미널에 설정한다.

```powershell
$env:RAG_EMBEDDING = 'neural'
$env:RAG_DB = 'var/index-neural.sqlite3'
$env:RAG_OLLAMA_MODEL = 'qwen3.5:4b'
$env:RAG_RERANK = '1'
python serve.py
```

사용 후 해당 터미널을 닫거나 관련 환경 변수를 정리한다. RAG_MODEL_CACHE는 embedding 캐시 경로, PORT는 HTTP 포트다. API가 쓰는 DB·embedding·cache는 색인 명령과 같아야 한다. RAG_DEMO_TOKENS를 지정하면 JSON token→tenant/roles 매핑으로 바꾸지만 여전히 학습용 인증 구현이다.

POST /search와 /query는 bearer 인증을 요구한다. PUT /documents와 DELETE /documents/:id는 admin이며 tenant는 인증에서 정한다. /query/stream은 retrieving 상태와 검증 후 완성 답변의 SSE이며 실시간 모델 토큰 전달이 아니다. 브라우저가 요청을 중단해도 모델 추론의 즉시 취소를 보장하지 않는다.

## 프레임워크 어댑터

```powershell
python -m pip install -r requirements-frameworks.txt
python -m demos.frameworks
```

먼저 기본 문자 모드 index를 만든다. LangChain과 LlamaIndex retriever를 같은 서버 Principal과 engine.search에 연결한다. 검색 반환과 비인가 자료 제외를 확인하는 예제이며 프레임워크 기본 LLM을 자동 호출하지 않는다. 데모는 외부 tracing을 비활성화한다.

## 검증 범위와 데이터 정리

기본 테스트는 실제 DB 파일·API TestClient·생성한 PDF를 사용한다. 실제 localhost HTTP 서버 smoke, 다국어 embedding, 리랭커, 로컬 생성 모델, 프레임워크 어댑터의 실행 결과는 별도 기록했다. 작은 합성 질문의 점수와 모델 smoke를 실서비스 정확도·부하·보안 인증으로 일반화하지 않는다.

var/에는 학습용 DB가 생성된다. 모델 캐시는 별도 크기를 가진다. 실습 데이터 경로를 직접 확인한 뒤 필요한 범위만 정리한다. 운영 DB나 다른 사용자 자료를 삭제하는 명령을 예제 기본 절차로 제공하지 않는다.

원고·창작 코드와 가상 데이터는 books 저장소의 CC0 조건을 따른다. 외부 패키지·모델은 각 라이선스를 따르며 가중치는 배포 파일에 포함하지 않는다.
