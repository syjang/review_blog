## 🤖 리뷰 활짝 - 자동화 시스템 (auto/)

LangGraph와 웹 검색을 이용해 블로그 리뷰를 자동 생성하는 시스템입니다.  
생성된 마크다운은 상위 프로젝트의 `app/posts/` 아래 저장해 블로그에서 바로 사용할 수 있습니다.

### 🚀 시작하기

#### 1. 가상환경 활성화

```bash
cd auto
source venv/bin/activate
```

#### 2. 환경변수 설정

루트(예: `/Users/leo/leo/review_blog/auto`)에 `.env` 파일을 만들고 API 키를 설정합니다.

```bash
cp .env.example .env  # 없다면 직접 .env 생성
# .env 파일을 열어서 OPENAI_API_KEY 또는 GOOGLE_API_KEY 입력
```

#### 3. 메인 워크플로우 실행 (`main_with_search.py`)

웹 검색 + 이미지 수집 + 마크다운 생성까지 한 번에 수행합니다.

```bash
python main_with_search.py
```

실행 후 콘솔에서:

- 제품명만 입력  
  예: `갤럭시 S24 울트라`

- **스타일 예시를 지정하고 싶을 때** (MX Master 4 리뷰 스타일 참고)  
  예: `갤럭시 S24 울트라 @review-mx-master-4-ddc17c.md (1-276)`

`@review-mx-master-4-ddc17c.md (1-276)` 부분은:

- 실제 파일 내용을 읽지는 않고,  
- `app/posts/review-mx-master-4-ddc17c.md` 글처럼  
  **구입 배경 → 사용 환경 → 장점/단점 → 비교 → 추천/비추천 → 총평** 흐름과  
  **사람이 쓴 실사용 후기 같은 톤**을 더 강하게 요구하는 힌트로만 사용됩니다.

### 📁 주요 파일 구조

```text
auto/
├── agents.py           # 리서치/작성/편집/SEO/마크다운 에이전트
├── main_with_search.py # 웹 검색 + 이미지 + 마크다운 통합 워크플로우 (주 사용 진입점)
├── workflows.py        # LangGraph 기반 다른 워크플로우 예제
├── search_tools.py     # 웹 검색 및 결과 포맷터
├── config.py           # 모델 선택/LLM 헬퍼
├── generated_reviews.json # 이미 생성된 리뷰 메타정보
├── requirements.txt
└── venv/
```

### 🎯 리뷰 스타일 (요약)

`main_with_search.py` 내부에 **MX Master 4 실사용 후기**를 기준으로 정리한 스타일 가이드가 포함되어 있습니다.

- 1인칭 시점(“저는…”, “제 기준에서는…”)의 **블로그 후기 톤**
- **구입 배경 → 사용 환경 → 장점/단점 → 비교 → 추천/비추천 → 총평** 흐름
- 스펙 나열보다 **어떤 상황에서 무엇이 어떻게 편/불편했는지**를 예시로 설명
- 가격, 무게, 휴대성, 손 크기/습관 등 **사람마다 갈릴 포인트**도 함께 언급
- 과장된 광고 문구 대신 **담백하고 솔직한 표현**
- 모델이 실제로 사용했다고 단정하지 않고  
  “여러 후기들을 보면…”, “실사용 후기를 종합하면…” 같은 표현 사용

CLI에서 `@review-mx-master-4-ddc17c.md (1-276)`를 붙이면  
해당 스타일 가이드를 특히 더 강하게 적용하도록 힌트를 주는 효과가 있습니다.