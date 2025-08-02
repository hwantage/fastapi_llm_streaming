
# ChatOllama 스트리밍 채팅 시스템

ChatOllama를 활용한 **실시간 스트리밍 AI 채팅** 웹 애플리케이션입니다. 

## 주요 기능

### **실시간 스트리밍 응답**
- ChatOllama 모델을 통한 토큰 단위 실시간 응답 생성
- 사용자가 질문하는 즉시 AI가 실시간으로 답변을 스트리밍

### **대화 히스토리 관리**
- **서버**: 최근 4개 메시지 쌍을 메모리에 유지하여 컨텍스트 연속성 보장
- **클라이언트**: 전체 대화 내용을 시각적으로 표시 및 로컬 관리
- 메모리 효율적인 자동 히스토리 정리

### **추천 프롬프트 시스템**
- 응답 완료 후 LLM을 통해 추가적인 추천 프롬프트 생성 및 사용자에게 제공:
  - ex)
  - 어떤 정보를 원하시는지 예시를 들어 설명해주실 수 있나요?
  - 특정 주제나 분야가 있으신가요?
  - 궁금한 점을 조금 더 자세히 말씀해주시면 관련 내용을 상세하게 안내해드릴 수 있습니다


### **새 채팅 기능**
- "새 채팅" 버튼으로 서버와 클라이언트 대화 히스토리 동시 초기화
- 언제든지 새로운 주제로 대화 시작 가능

### **사용자 친화적 UI**
- 실시간 대화 상태 표시 (연결됨, 응답 생성 중, 오류 등)
- 총 메시지 개수 카운터
- 사용자/AI 메시지 색상 구분 표시
- 스크롤 가능한 대화 히스토리 영역

![screenshot](https://github.com/user-attachments/assets/b5db91e6-c6f3-4aed-aeae-37cf4a5a31e9)

## 시스템 구조

```
├── llm_stream_server.py    # FastAPI 백엔드 서버
├── llm_stream_client.html  # 웹 클라이언트 인터페이스
└── README.md              # 프로젝트 문서
```

### **기술 스택**

**백엔드 (llm_stream_server.py)**
- **FastAPI**: 고성능 웹 프레임워크
- **ChatOllama**: LangChain 기반 Ollama 채팅 모델
- **Streaming Response**: 실시간 토큰 스트리밍
- **CORS 미들웨어**: 웹 브라우저 접근 허용

**프론트엔드 (llm_stream_client.html)**
- **Vanilla JavaScript**: 순수 자바스크립트 (프레임워크 없음)
- **Fetch API**: 서버 통신
- **ReadableStream**: 실시간 스트리밍 데이터 처리
- **로컬 히스토리 관리**: 클라이언트 사이드 대화 기록

## 사전 요구사항

### 1. **Ollama 설치 및 설정**
```bash
# Ollama 설치 (https://ollama.ai/)
curl -fsSL https://ollama.ai/install.sh | sh

# Llama-3-Korean-Bllossom 모델 다운로드
ollama pull hf.co/MLP-KTLim/llama-3-Korean-Bllossom-8B-gguf-Q4_K_M:Q4_K_M
```

### 2. **uv 설치 및 프로젝트 설정**
```bash
# uv 설치 (https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 또는 pip를 사용하여 설치
pip install uv

# 프로젝트 의존성 설치
uv sync
```

## 설치 및 실행

### 1. **저장소 클론**
```bash
git clone https://github.com/hwantage/fastapi_llm_streaming.git
cd fastapi_llm_streaming
```

### 2. **서버 실행**
```bash
uv run python llm_stream_server.py
```
- 서버가 `http://localhost:8001`에서 실행됩니다.

### 3. **클라이언트 실행**
- 웹 브라우저에서 `llm_stream_client.html` 파일을 직접 열어 테스트합니다.

## 개발 도구

### **uv 명령어**
```bash
uv sync            # 의존성 동기화
uv sync --dev      # 개발 의존성 포함 동기화
uv run python      # 가상환경에서 Python 실행
uv add package     # 새 패키지 추가
uv add --dev package  # 새 개발 패키지 추가
uv lock --upgrade  # 의존성 업그레이드
```


## 라이선스

MIT
