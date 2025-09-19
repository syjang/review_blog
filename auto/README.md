# 🤖 리뷰 활짝 - 자동화 시스템

LangGraph를 사용한 블로그 리뷰 자동 생성 시스템입니다.

## 🚀 시작하기

### 1. 가상환경 활성화
```bash
source venv/bin/activate
```

### 2. 환경변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:
```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY 입력
```

### 3. 실행
```bash
python run_example.py
```

## 📁 프로젝트 구조

```
auto/
├── venv/               # Python 가상환경
├── requirements.txt    # 패키지 의존성
├── .env               # 환경변수 (API 키)
├── main.py            # 기본 워크플로우
├── agents.py          # 특화된 에이전트들
├── workflows.py       # 다양한 워크플로우
├── run_example.py     # 실행 예제
└── outputs/           # 생성된 마크다운 파일
```

## 🎯 기능

### 1. 전체 리뷰 워크플로우
- 제품 리서치
- 리뷰 작성
- 편집 및 개선
- SEO 최적화
- 마크다운 생성

### 2. 빠른 리뷰 워크플로우
- 간단한 리뷰 작성
- 마크다운 생성

### 3. 에이전트들
- **ResearchAgent**: 제품 정보 리서치
- **WriterAgent**: 리뷰 컨텐츠 작성
- **EditorAgent**: 컨텐츠 편집 및 개선
- **SEOAgent**: SEO 최적화
- **MarkdownAgent**: 마크다운 포맷 생성

## 💡 사용 예제

### Python에서 직접 사용
```python
from workflows import run_review_workflow

# 리뷰 생성
result = run_review_workflow("애플 에어팟 프로 2")

# 결과 확인
if result.get("status") == "completed":
    markdown = result.get("markdown")
    print(markdown)
```

### 대화형 모드
```bash
python run_example.py
# 옵션 3 선택 -> 대화형 모드
```

## 🔧 커스터마이징

### 새로운 에이전트 추가
`agents.py`에 새로운 에이전트 클래스를 추가하세요:

```python
class CustomAgent:
    def __init__(self):
        self.llm = ChatOpenAI(...)

    def custom_task(self, data):
        # 커스텀 작업
        return result
```

### 새로운 워크플로우 생성
`workflows.py`에 새로운 워크플로우를 정의하세요:

```python
class CustomWorkflow:
    def create_graph(self):
        workflow = StateGraph(...)
        # 노드와 엣지 정의
        return workflow.compile()
```

## 📝 생성된 파일

생성된 마크다운 파일은 `outputs/` 폴더에 저장됩니다.
블로그에 게시하려면 `../app/posts/` 폴더로 복사하세요.

## 🛠️ 문제 해결

### API 키 오류
`.env` 파일에 올바른 OpenAI API 키가 설정되어 있는지 확인하세요.

### 패키지 오류
```bash
pip install -r requirements.txt
```

## 📚 추가 개발 아이디어

1. **이미지 생성**: DALL-E API로 제품 이미지 생성
2. **데이터베이스 연동**: 리뷰 히스토리 저장
3. **스케줄링**: 정기적인 리뷰 자동 생성
4. **웹 크롤링**: 실제 제품 정보 수집
5. **다국어 지원**: 영어, 일본어 등 리뷰 생성