"""
리뷰 블로그 자동화 시스템 (웹 검색 기능 포함)
LangGraph와 웹 검색을 사용한 블로그 관리 자동화
"""

import os
from typing import TypedDict, List, Dict
from datetime import datetime
from dotenv import load_dotenv
import uuid
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from config import get_llm
from search_tools import WebSearcher, format_search_results

# 환경 변수 로드
load_dotenv(verbose=True, override=True)

# LLM 설정
# llm = get_llm("gpt-oss", temperature=0.7)
llm = get_llm("gemini-2.5-flash", temperature=0.5)

# 웹 검색 도구
searcher = WebSearcher()

# 생성된 리뷰 추적 파일 경로
GENERATED_REVIEWS_FILE = "generated_reviews.json"


# 상태 정의
class BlogState(TypedDict):
    task: str
    product_name: str
    search_results: Dict
    posts: List[dict]
    current_post: dict
    feedback: str
    completed: bool
    images: List[dict]


# 리뷰 추적 함수들
def load_generated_reviews() -> List[Dict]:
    """생성된 리뷰 목록 로드"""
    try:
        if os.path.exists(GENERATED_REVIEWS_FILE):
            with open(GENERATED_REVIEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 리뷰 목록 로드 실패: {e}")
    return []

def save_generated_reviews(reviews: List[Dict]) -> None:
    """생성된 리뷰 목록 저장"""
    try:
        with open(GENERATED_REVIEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 리뷰 목록 저장 실패: {e}")

def is_product_already_reviewed(product_name: str) -> bool:
    """제품이 이미 리뷰되었는지 확인"""
    reviews = load_generated_reviews()
    normalized_product = product_name.lower().strip()

    for review in reviews:
        existing_product = review.get('product_name', '').lower().strip()
        if normalized_product in existing_product or existing_product in normalized_product:
            return True
    return False

def add_review_record(product_name: str, filename: str) -> None:
    """새 리뷰 기록 추가"""
    reviews = load_generated_reviews()
    new_review = {
        'product_name': product_name,
        'filename': filename,
        'created_at': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp()
    }
    reviews.append(new_review)
    save_generated_reviews(reviews)
    print(f"📝 리뷰 기록 추가: {product_name} -> {filename}")

# 노드 함수들
def analyze_task(state: BlogState) -> BlogState:
    """작업 분석 및 제품명 추출"""
    task = state.get("task", "")

    print(f"📋 작업 분석 중: {task}")

    # 제품명 추출 (간단한 방법)
    # 실제로는 더 정교한 NER이나 패턴 매칭 사용
    product_keywords = [
        "에어팟",
        "갤럭시",
        "아이폰",
        "맥북",
        "애플워치",
        "다이슨",
        "LG",
        "삼성",
    ]

    product_name = ""
    for keyword in product_keywords:
        if keyword in task:
            # 전체 제품명 추출 시도
            words = task.split()
            for i, word in enumerate(words):
                if keyword in word:
                    # 주변 단어들도 포함
                    start = max(0, i - 1)
                    end = min(len(words), i + 3)
                    product_name = " ".join(words[start:end])
                    break
            if product_name:
                break

    if not product_name:
        # 기본값으로 전체 태스크 사용
        product_name = task.replace("리뷰", "").replace("작성", "").strip()

    state["product_name"] = product_name
    state["current_post"] = {"type": "review", "status": "analyzing"}

    print(f"🎯 추출된 제품명: {product_name}")

    # 중복 체크
    if is_product_already_reviewed(product_name):
        print(f"⚠️ '{product_name}' 제품은 이미 리뷰가 존재합니다!")
        state["current_post"]["status"] = "duplicate"
        state["completed"] = True
        return state

    return state


def research_product(state: BlogState) -> BlogState:
    """제품 정보 리서치 노드 (웹 검색)"""
    product_name = state.get("product_name", "")

    print(f"🔍 제품 정보 리서치 중: {product_name}")

    # 웹 검색 실행
    search_results = searcher.get_comprehensive_info(product_name)
    state["search_results"] = search_results

    # 검색 결과 요약
    total_results = (
        len(search_results.get("basic_info", []))
        + len(search_results.get("price_info", []))
        + len(search_results.get("recent_news", []))
        + len(search_results.get("user_reviews", []))
        + len(search_results.get("images", []))
    )

    print(f"✅ 총 {total_results}개의 정보 수집 완료")

    return state


def download_images(state: BlogState) -> BlogState:
    """제품 이미지 다운로드 노드 (최신 이미지 우선)"""
    product_name = state.get("product_name", "")
    search_results = state.get("search_results", {})

    print(f"🖼️ 제품 이미지 다운로드 중: {product_name}")

    # 검색된 이미지들
    images = search_results.get("images", [])

    if images:
        # 최신 이미지를 우선적으로 선택
        recent_images = [img for img in images if img.get("is_recent", False)]
        normal_images = [img for img in images if not img.get("is_recent", False)]

        # 최신 이미지가 있으면 최신 이미지 우선, 없으면 일반 이미지 사용
        priority_images = recent_images + normal_images

        print(f"📊 이미지 우선순위: 최신 이미지 {len(recent_images)}개, 일반 이미지 {len(normal_images)}개")

        # 이미지 다운로드 실행 (우선순위대로)
        downloaded_images = searcher.download_product_images(
            product_name, priority_images, max_downloads=3
        )
        state["images"] = downloaded_images
        print(f"✅ {len(downloaded_images)}개 이미지 다운로드 완료 (최신 우선)")

        # 이미지 출처 정보 로깅
        for i, img in enumerate(downloaded_images):
            is_recent = "최신" if priority_images[i].get("is_recent") else "일반"
            print(f"  {i+1}. {img['filename']} ({is_recent} 이미지)")
    else:
        print(f"⚠️ 다운로드할 이미지가 없습니다.")
        state["images"] = []

    return state


def generate_content(state: BlogState) -> BlogState:
    """검색 결과를 바탕으로 컨텐츠 생성"""
    task = state.get("task", "")
    product_name = state.get("product_name", "")
    search_results = state.get("search_results", {})

    print(f"✍️ 검색 기반 컨텐츠 생성 중...")

    # 검색 결과를 컨텍스트로 정리
    context = format_search_context(search_results)

    # 검색 결과가 없을 때의 처리
    if not context.strip():
        print(f"⚠️ 검색 결과가 없습니다. 일반적인 정보로 컨텐츠를 생성합니다.")
        context = f"""
        검색 결과를 수집할 수 없었지만, {product_name}에 대한 일반적인 리뷰를 작성합니다.
        제품의 일반적인 특징과 사용자들이 자주 언급하는 내용을 바탕으로 리뷰를 구성하세요.
        """

    # LLM을 사용해 컨텐츠 생성
    system_prompt = """
    당신은 리뷰 블로그 '리뷰 활짝'의 컨텐츠 작성자입니다.
    제공된 검색 결과를 바탕으로 솔직하고 상세한 제품 리뷰를 작성해주세요.
    최소 1000자이상 작성해주세요.

    리뷰 구조:
    1. 제품 소개
    2. 주요 특징
    3. 장점 (최소 3가지)
    4. 단점 (최소 2가지)
    5. 가격 정보
    6. 총평 및 추천 대상

    검색 결과가 없더라도 제품에 대한 일반적이고 유용한 리뷰를 작성하세요.
    """

    user_prompt = f"""
    제품: {product_name}

    수집된 정보:
    {context}

    위 정보를 바탕으로 {task}
    """

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    state["current_post"]["content"] = (
        response.content if hasattr(response, "content") else str(response)
    )
    state["current_post"]["status"] = "generated"
    state["current_post"]["created_at"] = datetime.now().isoformat()
    state["current_post"]["sources"] = search_results  # 출처 저장

    return state


def format_search_context(search_results: Dict) -> str:
    """검색 결과를 LLM 컨텍스트로 포맷팅"""
    context = ""

    # 기본 정보
    if search_results.get("basic_info"):
        context += "### 제품 정보:\n"
        for info in search_results["basic_info"][:3]:
            context += f"- {info['title']}: {info['body'][:200]}\n"

    # 가격 정보
    if search_results.get("price_info"):
        context += "\n### 가격 정보:\n"
        for price in search_results["price_info"]:
            context += f"- {price['description'][:100]}\n"

    # 사용자 리뷰
    if search_results.get("user_reviews"):
        context += "\n### 사용자 의견:\n"
        for review in search_results["user_reviews"][:3]:
            context += f"- {review['summary'][:150]}\n"

    # 최신 뉴스
    if search_results.get("recent_news"):
        context += "\n### 최근 소식:\n"
        for news in search_results["recent_news"][:2]:
            context += f"- {news['title']}: {news['body'][:100]}\n"

    return context


def create_markdown(state: BlogState) -> BlogState:
    """마크다운 파일 생성 (이미지 리뷰 중간 배치)"""
    current_post = state.get("current_post", {})
    content = current_post.get("content", "")
    product_name = state.get("product_name", "")
    search_results = state.get("search_results", {})
    images = state.get("images", [])

    print(f"📝 마크다운 파일 생성 중...")

    # 리뷰 내용을 섹션별로 나누기
    sections = split_content_into_sections(content)
    print(f"📊 리뷰 섹션 수: {len(sections)}")

    # 이미지들을 섹션 사이에 배치
    content_with_images = insert_images_between_sections(sections, images)

    # 참고 링크 생성
    references = "\n\n## 참고 자료\n\n"
    if search_results.get("basic_info"):
        for info in search_results["basic_info"][:3]:
            references += f"- [{info['title']}]({info['url']})\n"

    # 이미지 출처 정보
    if images:
        references += f"\n### 이미지 출처\n"
        for img in images:
            references += f"- [이미지 {images.index(img)+1}]({img['original_url']})\n"

    # 제품명을 영어로 변환 (태그용)
    safe_product_name = translate_product_name_for_tags(product_name)

    # 마크다운 포맷으로 변환
    if images and images[0].get("filename"):
        # 첫 번째 이미지의 실제 파일명 사용
        primary_image = f"/images/{images[0]['filename']}"
    else:
        # 고유번호 기반 기본값
        unique_id = str(uuid.uuid4())[:8]
        primary_image = f"/images/review-{unique_id}-1.jpg"

    markdown_template = f"""---
title: '{product_name} 리뷰 - 실사용 후기와 장단점'
date: '{datetime.now().strftime("%Y-%m-%d")}'
excerpt: '{product_name}에 대한 상세한 리뷰와 구매 가이드'
category: '제품리뷰'
tags: ['{safe_product_name}', '리뷰', '실사용후기']
image: '{primary_image}'
---

{content_with_images}

{references}

---
*이 리뷰는 웹 검색 결과를 바탕으로 작성되었습니다.*
*작성일: {datetime.now().strftime("%Y년 %m월 %d일")}*
"""

    state["current_post"]["markdown"] = markdown_template
    state["current_post"]["status"] = "markdown_created"

    return state


def translate_product_name_for_tags(product_name: str) -> str:
    """
    제품명을 태그용 영어로 변환

    Args:
        product_name: 한글 제품명

    Returns:
        영어 태그명
    """
    # 한글 제품명을 영어로 매핑하는 딕셔너리
    korean_to_english = {
        # 삼성 제품
        "갤럭시": "galaxy",
        "갤럭시 s": "galaxy-s",
        "갤럭시s": "galaxy-s",
        "갤럭시 s24": "galaxy-s24",
        "갤럭시s24": "galaxy-s24",
        "갤럭시 s25": "galaxy-s25",
        "갤럭시s25": "galaxy-s25",
        "갤럭 폴드": "galaxy-fold",
        "갤럭폴드": "galaxy-fold",
        "갤럭폴드7": "galaxy-fold7",
        "버즈 프로": "buds-pro",
        "버즈프로": "buds-pro",
        "버즈프로3": "buds-pro3",

        # 애플 제품
        "아이폰": "iphone",
        "아이폰 16": "iphone-16",
        "아이폰16": "iphone-16",
        "아이폰 16 프로": "iphone-16-pro",
        "아이폰16프로": "iphone-16-pro",
        "아이폰 16 프로 맥스": "iphone-16-pro-max",
        "아이폰16프로맥스": "iphone-16-pro-max",
        "에어팟": "airpods",
        "에어팟 프로": "airpods-pro",
        "에어팟프로": "airpods-pro",
        "애플 매직 키보드": "apple-magic-keyboard",
        "애플매직키보드": "apple-magic-keyboard",
        "매직 키보드": "magic-keyboard",
        "매직키보드": "magic-keyboard",
        "맥북": "macbook",
        "아이패드": "ipad",
        "애플워치": "apple-watch",

        # 기타 브랜드
        "소니": "sony",
        "소니 무선 헤드폰": "sony-headphone",
        "소니무선헤드폰": "sony-headphone",
        "다이슨": "dyson",
    }

    # 제품명을 소문자로 변환
    safe_name = product_name.lower()

    # 한글을 영어로 변환
    for korean, english in korean_to_english.items():
        safe_name = safe_name.replace(korean, english)

    # 공백과 특수문자를 하이픈으로 변환
    import re
    safe_name = re.sub(r'[^\w\-]', '-', safe_name)
    safe_name = re.sub(r'-+', '-', safe_name)  # 연속된 하이픈 제거
    safe_name = safe_name.strip('-')  # 앞뒤 하이픈 제거

    # 빈 문자열이면 원본 반환
    if not safe_name:
        safe_name = product_name

    return safe_name


def split_content_into_sections(content: str) -> List[str]:
    """리뷰 내용을 섹션별로 나누기"""
    sections = []
    current_section = ""
    lines = content.split("\n")

    for line in lines:
        if line.startswith("### ") and current_section.strip():
            # 새로운 섹션이 시작되면 이전 섹션 저장
            sections.append(current_section.strip())
            current_section = line + "\n"
        else:
            current_section += line + "\n"

    # 마지막 섹션 추가
    if current_section.strip():
        sections.append(current_section.strip())

    return sections


def insert_images_between_sections(sections: List[str], images: List[Dict]) -> str:
    """섹션 사이에 이미지 배치"""
    if not images:
        return "\n".join(sections)

    result = []
    images_used = 0
    max_images = min(len(images), 3)  # 최대 3개 이미지 사용

    # 첫 번째 섹션은 이미지 없이 추가
    if sections:
        result.append(sections[0])

    # 나머지 섹션들 사이에 이미지 배치
    for i in range(1, len(sections)):
        # 이미지 추가 (사용 가능한 이미지 수 내에서)
        if images_used < max_images and i <= max_images:
            img = images[images_used]
            image_caption = img.get("title", f"제품 이미지 {images_used + 1}")
            image_md = f"\n![{image_caption}]({img['local_path']})\n"
            if img.get("title"):
                image_md += f"*{img['title']}*\n"
            result.append(image_md)
            images_used += 1

        # 다음 섹션 추가
        result.append(sections[i])

    return "\n".join(result)


def save_post(state: BlogState) -> BlogState:
    """포스트 저장"""
    current_post = state.get("current_post", {})
    markdown = current_post.get("markdown", "")
    product_name = state.get("product_name", "")

    print(f"💾 포스트 저장 중...")

    # 파일명 생성 (고유번호 기반)
    unique_id = str(uuid.uuid4())[:8]  # UUID 앞 8자리 사용
    filename = f"review-{unique_id}.md"
    filepath = f"../app/posts/{filename}"

    # 실제 파일 저장
    try:
        os.makedirs("../app/posts", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✅ 파일 저장 완료: {filepath}")
    except Exception as e:
        print(f"❌ 저장 실패: {e}")
        print(f"📄 내용 미리보기:\n{markdown[:500]}...")

    state["current_post"]["filename"] = filename
    state["current_post"]["status"] = "saved"
    state["completed"] = True

    # 생성된 리뷰 기록에 추가
    add_review_record(product_name, filename)

    return state


def review_content(state: BlogState) -> BlogState:
    """컨텐츠 검토"""
    content = state.get("current_post", {}).get("content", "")
    search_results = state.get("search_results", {})

    print(f"🔍 컨텐츠 검토 중...")

    # 재시도 횟수 추적
    revision_count = state.get("revision_count", 0)
    max_revisions = 2  # 최대 재시도 횟수

    # 검토 기준
    checks = {
        "length": len(content) > 500,
        "has_pros": "장점" in content or "좋은" in content,
        "has_cons": "단점" in content or "아쉬운" in content,
        "has_price": "가격" in content or "원" in content,
    }

    # 검색 결과가 없어도 최대 재시도 후에는 통과
    if (
        len(search_results.get("basic_info", [])) == 0
        and revision_count >= max_revisions
    ):
        checks["sources_used"] = True  # 강제로 통과
        print(f"⚠️ 검색 결과 없음. 재시도 제한({max_revisions})에 도달하여 진행합니다.")
    else:
        checks["sources_used"] = len(search_results.get("basic_info", [])) > 0

    failed_checks = [k for k, v in checks.items() if not v]

    if failed_checks and revision_count < max_revisions:
        state["feedback"] = f"개선 필요: {', '.join(failed_checks)}"
        state["current_post"]["needs_revision"] = True
        state["revision_count"] = revision_count + 1
    else:
        if revision_count >= max_revisions:
            state["feedback"] = (
                f"최대 재시도 횟수({max_revisions}) 도달 - 현재 상태로 진행"
            )
        else:
            state["feedback"] = "검토 통과 - 품질 기준 충족"
        state["current_post"]["needs_revision"] = False

    print(f"📊 검토 결과: {state['feedback']}")
    if revision_count > 0:
        print(f"📈 재시도 횟수: {revision_count}/{max_revisions}")

    return state


# 조건부 엣지 함수
def should_revise(state: BlogState) -> str:
    """수정 필요 여부 판단"""
    if state.get("current_post", {}).get("needs_revision", False):
        return "revise"
    return "continue"

def should_continue_after_analyze(state: BlogState) -> str:
    """분석 후 계속 진행 여부 판단"""
    current_post = state.get("current_post", {})
    if current_post.get("status") == "duplicate":
        return "end"
    return "research"


# 워크플로우 생성
def create_workflow():
    """웹 검색이 포함된 워크플로우 생성"""

    workflow = StateGraph(BlogState)

    # 노드 추가
    workflow.add_node("analyze", analyze_task)
    workflow.add_node("research", research_product)  # 웹 검색 노드 추가
    workflow.add_node("download_images", download_images)  # 이미지 다운로드 노드 추가
    workflow.add_node("generate", generate_content)
    workflow.add_node("review", review_content)
    workflow.add_node("markdown", create_markdown)
    workflow.add_node("save", save_post)

    # 엣지 설정
    workflow.set_entry_point("analyze")

    # 분석 후 중복 체크 조건부 엣지
    workflow.add_conditional_edges(
        "analyze", should_continue_after_analyze, {"end": END, "research": "research"}
    )

    workflow.add_edge("research", "download_images")  # 리서치 후 이미지 다운로드
    workflow.add_edge("download_images", "generate")  # 이미지 다운로드 후 생성
    workflow.add_edge("generate", "review")

    # 조건부 엣지
    workflow.add_conditional_edges(
        "review", should_revise, {"revise": "generate", "continue": "markdown"}
    )

    workflow.add_edge("markdown", "save")
    workflow.add_edge("save", END)

    # 체크포인터 설정
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# 메인 실행
def main():
    """메인 실행 함수"""
    print("🚀 리뷰 블로그 자동화 시스템 (웹 검색 버전)")
    print("=" * 60)

    # 워크플로우 생성
    app = create_workflow()

    # 기존 리뷰 목록 표시
    existing_reviews = load_generated_reviews()
    if existing_reviews:
        print(f"\n📚 기존 생성된 리뷰 목록 ({len(existing_reviews)}개):")
        for i, review in enumerate(existing_reviews[-5:], 1):  # 최근 5개만 표시
            print(f"  {i}. {review['product_name']} ({review['created_at'][:10]})")
        if len(existing_reviews) > 5:
            print(f"  ... 외 {len(existing_reviews) - 5}개 더")
        print()

    # 사용자 입력 받기
    print("제품 리뷰를 작성할 제품을 입력하세요.")
    print("예시: 갤럭시 S24 울트라, 에어팟 프로 2, 다이슨 V15")
    product_input = input("\n제품명: ").strip()

    if not product_input:
        product_input = "갤럭시 S24 울트라"
        print(f"기본값 사용: {product_input}")

    # 초기 상태
    initial_state = {
        "task": f"{product_input} 리뷰 작성",
        "product_name": "",
        "search_results": {},
        "posts": [],
        "current_post": {},
        "feedback": "",
        "completed": False,
        "images": [],
    }

    # 워크플로우 실행
    config = {"configurable": {"thread_id": f"review_{datetime.now().timestamp()}"}}

    print(f"\n📌 작업: {initial_state['task']}")
    print("=" * 60)

    # 실행
    for output in app.stream(initial_state, config):
        for key, value in output.items():
            print(f"✅ {key} 노드 완료")

    print("=" * 60)
    print("✨ 리뷰 작성 완료!")


if __name__ == "__main__":
    main()
