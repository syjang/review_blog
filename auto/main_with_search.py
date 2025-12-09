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
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from io import BytesIO
from PIL import Image
import hashlib
import re

# 환경 변수 로드
load_dotenv(verbose=True, override=True)


# LLM 설정
# llm 동적 선택: OPENAI_API_KEY > GOOGLE_API_KEY > 로컬
def choose_llm():
    # Gemini 우선
    if os.getenv("GOOGLE_API_KEY"):
        return get_llm("gemini-2.5-flash", temperature=0.5)
    if os.getenv("OPENAI_API_KEY"):
        return get_llm("gpt-4o-mini", temperature=0.5)
    return get_llm("gpt-oss", temperature=0.7)


llm = choose_llm()

# 웹 검색 도구
searcher = WebSearcher()

# 생성된 리뷰 추적 파일 경로 및 경로 상수
GENERATED_REVIEWS_FILE = "generated_reviews.json"
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT_DIR, "app", "posts")
IMAGES_DIR = os.path.join(ROOT_DIR, "app", "public", "images")


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
    product_slug: str
    local_images: List[dict]


# 사람스러운 리뷰 스타일 가이드 (MX Master 4 실사용 후기 스타일 참고)
HUMAN_REVIEW_STYLE_GUIDE = """
- 1인칭 시점(‘저는’, ‘제 기준에서는’)으로, 실제로 써 본 사람의 블로그 후기처럼 자연스럽게 씁니다.
- 먼저 “왜 이 제품을 알아보게 되었는지/사게 되었는지”와 현재 사용 환경(사용 기간, 사용하는 기기 조합, 주요 작업)을 1~2단락으로 풀어줍니다.
- 장점/단점은 스펙 나열이 아니라, 어떤 상황에서 무엇이 어떻게 편했는지·아쉬웠는지를 구체적인 예시와 함께 설명합니다.
- 개발/업무/영상 편집/일상 등 실제 작업 흐름 속에서 어떤 부분이 체감되는지 이야기를 섞어 줍니다.
- 가격, 무게, 휴대성, 손 크기·사용 습관처럼 사람마다 갈릴 수 있는 포인트는 장단점 양쪽에서 균형 있게 다룹니다.
- 마지막에는 “이런 사람에게 추천 / 이런 사람에게는 굳이 필요 없음”을 정리하고, 한두 문장으로 총평을 남깁니다.
- 과장된 광고 문구보다는 담백하고 솔직한 표현을 사용합니다.
- 다만, 모델이 실제로 제품을 사용한 것처럼 단정적으로 말하진 말고,
  ‘여러 후기들을 보면’, ‘실사용 후기를 종합하면’, ‘제 기준에서라면 이런 부분이 가장 먼저 눈에 들어올 것 같습니다’처럼 표현합니다.
"""


# 리뷰 추적 함수들
def load_generated_reviews() -> List[Dict]:
    """생성된 리뷰 목록 로드"""
    try:
        if os.path.exists(GENERATED_REVIEWS_FILE):
            with open(GENERATED_REVIEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ 리뷰 목록 로드 실패: {e}")
    return []


def save_generated_reviews(reviews: List[Dict]) -> None:
    """생성된 리뷰 목록 저장"""
    try:
        with open(GENERATED_REVIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(reviews, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 리뷰 목록 저장 실패: {e}")


def is_product_already_reviewed(product_name: str) -> bool:
    """제품이 이미 리뷰되었는지 확인"""
    reviews = load_generated_reviews()
    normalized_product = product_name.lower().strip()

    for review in reviews:
        existing_product = review.get("product_name", "").lower().strip()
        if (
            normalized_product in existing_product
            or existing_product in normalized_product
        ):
            return True
    return False


def add_review_record(product_name: str, filename: str) -> None:
    """새 리뷰 기록 추가"""
    reviews = load_generated_reviews()
    new_review = {
        "product_name": product_name,
        "filename": filename,
        "created_at": datetime.now().isoformat(),
        "timestamp": datetime.now().timestamp(),
    }
    reviews.append(new_review)
    save_generated_reviews(reviews)
    print(f"📝 리뷰 기록 추가: {product_name} -> {filename}")


# 노드 함수들
STYLE_REF_PATTERN = re.compile(
    r"@(?P<filename>[^\s]+)\s*\((?P<start>\d+)\s*-\s*(?P<end>\d+)\)"
)


def extract_style_reference(task: str) -> Dict[str, str]:
    """태스크 문자열에서 @파일명 (1-276) 형태의 스타일 참조 정보 추출"""
    if not task:
        return {}
    match = STYLE_REF_PATTERN.search(task)
    if not match:
        return {}
    return {
        "style_file": match.group("filename"),
        "style_range": f"{match.group('start')}-{match.group('end')}",
        "style_hint": "example_review",
    }


def strip_style_reference(task: str) -> str:
    """태스크 문자열에서 스타일 참조 표기 제거"""
    if not task:
        return ""
    return STYLE_REF_PATTERN.sub("", task).strip()


def analyze_task(state: BlogState) -> BlogState:
    """작업 분석 및 제품명 추출"""
    task = state.get("task", "")

    print(f"📋 작업 분석 중: {task}")

    # 스타일 참조 정보 추출 (@review-mx-master-4-ddc17c.md (1-276) 형태)
    style_ref = extract_style_reference(task)
    if style_ref:
        state["style_reference"] = style_ref

    # 스타일 참조 표기는 제품명 분석 대상에서 제거
    task_for_product = strip_style_reference(task)

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
    # MX Master 같은 제품도 조금 더 잘 잡도록 범용 키워드 추가
    product_keywords.extend(["로지텍", "로지텍 MX", "MX", "마스터"])

    for keyword in product_keywords:
        if keyword in task_for_product:
            # 전체 제품명 추출 시도
            words = task_for_product.split()
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
        # 기본값으로 전체 태스크(스타일 참조 제거본) 사용
        product_name = (
            task_for_product.replace("리뷰", "").replace("작성", "").strip()
        )

    state["product_name"] = product_name
    state["product_slug"] = slugify(product_name)
    state["current_post"] = {"type": "review", "status": "analyzing"}

    print(f"🎯 추출된 제품명: {product_name}")

    # 중복 체크
    if os.getenv("FORCE_REGENERATE") != "1" and is_product_already_reviewed(
        product_name
    ):
        print(f"⚠️ '{product_name}' 제품은 이미 리뷰가 존재합니다!")
        state["current_post"]["status"] = "duplicate"
        state["completed"] = True
        return state

    return state


def research_product(state: BlogState) -> BlogState:
    """제품 정보 리서치 노드 (웹 검색)"""
    product_name = state.get("product_name", "")

    print(f"🔍 제품 정보 리서치 중: {product_name}")

    # 환경변수로 웹 검색 비활성화 (샌드박스/네트워크 제한 회피)
    if os.getenv("DISABLE_WEB_SEARCH") == "1":
        print("⚙️  웹 검색 비활성화됨(DISABLE_WEB_SEARCH=1). 검색 없이 진행합니다.")
        state["search_results"] = {
            "product": product_name,
            "latest_product": product_name,
            "basic_info": [],
            "price_info": [],
            "recent_news": [],
            "user_reviews": [],
            "images": [],
        }
        return state

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


def collect_images(state: BlogState) -> BlogState:
    """제품 이미지 정보 수집 노드 (다운로드 없이 링크만)"""
    product_name = state.get("product_name", "")
    search_results = state.get("search_results", {})

    print(f"🖼️ 제품 이미지 정보 수집 중: {product_name}")

    if os.getenv("DISABLE_WEB_SEARCH") == "1":
        print("⚙️  웹 검색 비활성화 상태: 이미지 정보 수집 건너뜀")
        state["images"] = []
        return state

    # 검색된 이미지들
    images = search_results.get("images", [])

    if images:
        # 최신 이미지를 우선적으로 선택
        recent_images = [img for img in images if img.get("is_recent", False)]
        normal_images = [img for img in images if not img.get("is_recent", False)]

        # 최신 이미지가 있으면 최신 이미지 우선, 없으면 일반 이미지 사용
        priority_images = recent_images + normal_images

        print(
            f"📊 이미지 우선순위: 최신 이미지 {len(recent_images)}개, 일반 이미지 {len(normal_images)}개"
        )

        # 이미지 정보 수집 실행 (다운로드 없이)
        image_info_list = searcher.get_product_images_info(
            product_name, priority_images, max_images=4
        )
        state["images"] = image_info_list
        print(f"✅ {len(image_info_list)}개 이미지 정보 수집 완료 (링크만)")

        # 이미지 출처 정보 로깅 (상세히)
        for i, img_info in enumerate(image_info_list):
            is_recent = "최신" if priority_images[i].get("is_recent") else "일반"
            url = img_info["url"].lower()

            # 이미지 형식과 호스트 정보 추출
            if url.endswith(".webp"):
                format_info = "WebP"
            elif url.endswith(".jpg") or url.endswith(".jpeg"):
                format_info = "JPG"
            elif url.endswith(".png"):
                format_info = "PNG"
            else:
                format_info = "기타"

            # CDN 정보 확인
            cdn_info = ""
            fast_hosts = [
                "cloudinary",
                "imgur",
                "cdn",
                "fastly",
                "akamai",
                "googleusercontent",
                "githubusercontent",
                "amazonaws",
            ]
            for host in fast_hosts:
                if host in url:
                    cdn_info = f"CDN:{host}"
                    break

            print(
                f"  {i+1}. {img_info['title']} ({is_recent}, {format_info}, {cdn_info})"
            )
    else:
        print(f"⚠️ 수집할 이미지 정보가 없습니다.")
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

    # LLM을 사용해 컨텐츠 생성 (사람이 쓴 후기 같은 톤 + 품질 규격)
    style_ref = state.get("style_reference", {}) or {}
    style_note = ""
    if style_ref.get("style_hint") == "example_review":
        # 사용자가 @review-... (1-276) 형태로 스타일 예시를 지정한 경우
        style_note = """
        추가 스타일 힌트:
        - 사용자가 지정한 예시 리뷰처럼,
          "구입 배경 → 사용 환경 → 장점/단점 → 비교 → 추천/비추천 → 총평" 흐름이 자연스럽게 이어지도록 작성하세요.
        """

    system_prompt = f"""
    당신은 리뷰 블로그 '리뷰 활짝'의 메인 필진입니다.
    아래 스타일 가이드를 따라, 사람이 직접 써 내려간 것 같은 한국어 리뷰를 작성하세요.

    [스타일 가이드]
    {HUMAN_REVIEW_STYLE_GUIDE}
    {style_note}

    작성 규칙:
    - 전체 분량은 최소 1,500자 이상으로 합니다.
    - 문단마다 구체적인 상황(어떤 환경, 어떤 작업, 어떤 유형의 사용자)을 상상해서 예시를 들어주세요.
    - 너무 딱딱한 기술 문서 느낌이 아니라, 블로그에 올리는 긴 후기 느낌으로 작성하세요.

    구조(헤딩은 반드시 이 이름을 사용):
    ### 제품 소개 & 구입 배경
    ### 사용 환경 정리
    ### 장점
    - 3가지 이상, 각각 2문장 이상
    ### 단점
    - 2가지 이상, 각각 2문장 이상
    ### 경쟁 제품 비교
    - 최소 2개 제품과 표(마크다운 테이블) 또는 불릿 비교 (차이점/대상)
    ### 가격 및 구매 팁
    ### FAQ
    - 최소 4개 질문/답변 (각 2문장 이상)
    ### 총평 및 추천 대상

    중요:
    - 공개된 정보와 다수 사용자 후기를 바탕으로 쓰되,
      모델이 실제로 제품을 사용했다고 단정하는 표현(예: "제가 3주 동안 직접 써보니")은 피하세요.
    - 대신 "여러 후기들을 보면", "실사용 후기를 종합하면", "제 기준에서라면 이런 부분이 먼저 눈에 들어옵니다"처럼 표현해 주세요.
    - 마케팅 문구보다는 솔직한 장단점과 누가 쓸 때 좋은지에 집중합니다.
    """

    cleaned_task = strip_style_reference(task)
    if not cleaned_task:
        cleaned_task = f"{product_name}에 대한 리뷰를 작성해 주세요."

    user_prompt = f"""
    제품: {product_name}

    당신의 역할:
    - 위 제품에 대해, 웹에서 수집된 정보와 사용자 후기를 바탕으로
      블로그 '리뷰 활짝'에 올라갈 장문 리뷰를 작성합니다.

    수집된 정보 요약:
    {context}

    글의 목적:
    - {cleaned_task}
    """

    # 네트워크/키 미제공 시 LLM 비활성화 모드 지원
    if os.getenv("DISABLE_LLM") == "1":
        content_text = generate_template_content(product_name)
    else:
        # 품질 게이트를 만족할 때까지 최대 3회 재생성
        attempts = 0
        content_text = ""
        while attempts < 3:
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            raw = response.content if hasattr(response, "content") else response
            content_text = to_plain_text(raw)
            if passes_quality_gates(content_text):
                break
            attempts += 1

    state["current_post"]["content"] = content_text
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
    """마크다운 파일 생성 (로컬 이미지 사용)"""
    current_post = state.get("current_post", {})
    content = current_post.get("content", "")
    product_name = state.get("product_name", "")
    search_results = state.get("search_results", {})
    images = state.get("images", [])

    print(f"📝 마크다운 파일 생성 중...")

    # 리뷰 내용을 섹션별로 나누기
    sections = split_content_into_sections(content)
    print(f"📊 리뷰 섹션 수: {len(sections)}")

    # 이미지 다운로드 → WebP 저장 → 로컬 경로 삽입
    local_images = download_and_prepare_images(
        state.get("product_slug", slugify(product_name)), images
    )
    state["local_images"] = local_images
    content_with_images = insert_local_images_between_sections(sections, local_images)

    # 참고 링크 생성
    references = "\n\n## 참고 자료\n\n"
    if search_results.get("basic_info"):
        for info in search_results["basic_info"][:3]:
            references += f"- [{info['title']}]({info['url']})\n"

    # 이미지 출처는 캡션으로 충분, 별도 목록 생략

    # 제품명을 영어로 변환 (태그용)
    safe_product_name = translate_product_name_for_tags(product_name)

    # 마크다운 포맷으로 변환
    if state.get("local_images"):
        # 첫 번째 로컬 이미지 사용
        primary_image = state["local_images"][0]["path"]
        primary_image_alt = state["local_images"][0]["alt"]
    else:
        # 이미지가 없으면 기본값
        primary_image = "/images/product-1.webp"
        primary_image_alt = f"{product_name} 제품 이미지"

    # 자동생성 문구 제거
    image_credit = ""

    # YAML-safe image_alt (이모지, 특수문자, ... 등 제거)
    safe_image_alt = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ:,.\-]', '', primary_image_alt)
    safe_image_alt = safe_image_alt.replace('...', '').replace('..', '.').strip()
    # 너무 길면 100자로 제한
    if len(safe_image_alt) > 100:
        safe_image_alt = safe_image_alt[:100].strip()

    markdown_template = f"""---
title: '{build_unique_title(product_name)}'
date: '{datetime.now().strftime("%Y-%m-%d")}'
updated: '{datetime.now().strftime("%Y-%m-%d")}'
author: '리뷰 활짝'
excerpt: '{build_excerpt(product_name)}'
category: '제품리뷰'
tags: ['{safe_product_name}', '리뷰']
image: '{primary_image}'
image_alt: '{safe_image_alt}'
rating: {estimate_rating_from_content(content)}
noindex: false
---

{content_with_images}

{image_credit}

{references}
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

    safe_name = re.sub(r"[^\w\-]", "-", safe_name)
    safe_name = re.sub(r"-+", "-", safe_name)  # 연속된 하이픈 제거
    safe_name = safe_name.strip("-")  # 앞뒤 하이픈 제거

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


def insert_external_images_between_sections(
    sections: List[str], images: List[Dict]
) -> str:
    """섹션 사이에 외부 이미지 링크 배치"""
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
            # 외부 링크와 대체 텍스트 사용
            image_md = f"\n![{image_caption}]({img['url']})\n"
            image_md += f"*{image_caption}*\n"
            # 이미지 정보 추가 (해상도 등)
            if img.get("width") and img.get("height"):
                image_md += f"*(이미지 크기: {img['width']}x{img['height']} 픽셀)*\n"
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

    # 파일명 생성: review-<product-slug>-<shortid>.md
    product_slug = state.get("product_slug", slugify(product_name))
    shortid = str(uuid.uuid4())[:6]
    filename = f"review-{product_slug}-{shortid}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # 실제 파일 저장
    try:
        os.makedirs(POSTS_DIR, exist_ok=True)
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

    # 검토 기준 (환경에 따라 완화)
    disable_llm = os.getenv("DISABLE_LLM") == "1"
    disable_search = os.getenv("DISABLE_WEB_SEARCH") == "1"

    min_length = 600 if disable_llm else 1200

    checks = {
        "length": len(content) >= min_length,
        "numbers": count_numeric_metrics(content) >= 3,
        "has_pros": "### 장점" in content,
        "has_cons": "### 단점" in content,
        "has_compare": "### 경쟁 제품 비교" in content,
        "has_price": ("### 가격" in content) or ("가격 및 구매 팁" in content),
        "has_faq": "### FAQ" in content,
    }

    # 검색 결과가 없어도 최대 재시도 후에는 통과
    if (
        len(search_results.get("basic_info", [])) == 0
        and revision_count >= max_revisions
    ):
        checks["sources_used"] = True  # 강제로 통과
        print(f"⚠️ 검색 결과 없음. 재시도 제한({max_revisions})에 도달하여 진행합니다.")
    else:
        # 검색 비활성화 시 출처 강제 통과
        checks["sources_used"] = (
            True if disable_search else len(search_results.get("basic_info", [])) > 0
        )

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
    workflow.add_node("collect_images", collect_images)  # 이미지 정보 수집 노드 추가
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

    workflow.add_edge("research", "collect_images")  # 리서치 후 이미지 정보 수집
    workflow.add_edge("collect_images", "generate")  # 이미지 정보 수집 후 생성
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


# ---------------------------- 헬퍼 함수들 ----------------------------
def slugify(text: str) -> str:
    safe = text.lower().strip()
    safe = re.sub(r"[\s/]+", "-", safe)
    safe = re.sub(r"[^a-z0-9\-]+", "", safe)
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe or "post"


def build_unique_title(product_name: str) -> str:
    """제목 패턴을 다양화"""
    import random
    patterns = [
        f"{product_name} 리뷰: 상세 분석과 구매 가이드",
        f"{product_name} 완벽 가이드: 특징, 장단점, 가격 비교",
        f"{product_name} 총정리: 성능부터 가성비까지",
        f"{product_name} 심층 리뷰: 장점과 단점 분석",
        f"{product_name} 구매 전 필독: 스펙과 실사용 팁",
        f"{product_name} 분석: 특징·가격·경쟁 제품 비교",
        f"{product_name} 완전 분석: 구매 가이드와 추천 대상",
    ]
    return random.choice(patterns)


def build_excerpt(product_name: str) -> str:
    """excerpt 패턴을 다양화"""
    import random
    patterns = [
        f"{product_name}의 주요 특징, 장단점, 가격 정보와 구매 팁 총정리",
        f"{product_name} 스펙 분석과 경쟁 제품 비교, 추천 대상 안내",
        f"{product_name}의 성능과 특징, 가격대별 옵션 상세 분석",
        f"{product_name} 완벽 가이드: 특징부터 구매 팁까지",
        f"{product_name}의 핵심 기능과 장단점, 가격 비교 정보",
        f"{product_name} 종합 분석: 스펙, 가격, 사용자 평가",
    ]
    return random.choice(patterns)


def count_numeric_metrics(text) -> int:
    if not isinstance(text, str):
        text = to_plain_text(text)
    return len(
        re.findall(
            r"\b\d+[\d,.]*(?:%|만원|원|g|kg|mm|cm|mAh|시간|nit|Hz|GB|TB|inch|인치)?\b",
            text,
        )
    )


def passes_quality_gates(content: str) -> bool:
    checks = {
        "length": len(content) >= 1200,
        "numbers": count_numeric_metrics(content) >= 3,
        "has_pros": "### 장점" in content,
        "has_cons": "### 단점" in content,
        "has_compare": "### 경쟁 제품 비교" in content,
        "has_price": ("### 가격" in content) or ("가격 및 구매 팁" in content),
        "has_faq": "### FAQ" in content,
    }
    return all(checks.values())


def fetch_binary(url: str) -> bytes:
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=20) as resp:
            return resp.read()
    except (URLError, HTTPError) as e:
        print(f"❌ 이미지 다운로드 오류: {e}")
        return b""


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def download_and_prepare_images(product_slug: str, images: List[dict]) -> List[dict]:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    local_list: List[dict] = []
    for idx, img in enumerate(images[:3], start=1):
        url = img.get("url")
        if not url:
            continue
        try:
            filename_base = f"{product_slug}-{idx}-{short_hash(url)}"
            webp_path = os.path.join(IMAGES_DIR, f"{filename_base}.webp")
            if not os.path.exists(webp_path):
                data = fetch_binary(url)
                if not data:
                    continue
                image = Image.open(BytesIO(data))
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGB")
                image.save(webp_path, "WEBP", quality=85, optimize=True)
            local_list.append(
                {
                    "path": f"/images/{os.path.basename(webp_path)}",
                    "alt": img.get("title") or f"{product_slug} 이미지 {idx}",
                    "width": img.get("width", 0),
                    "height": img.get("height", 0),
                }
            )
        except Exception as e:
            print(f"⚠️ 이미지 저장 실패({idx}): {e}")
            continue
    return local_list


def insert_local_images_between_sections(
    sections: List[str], local_images: List[dict]
) -> str:
    if not local_images:
        return "\n".join(sections)
    result: List[str] = []
    images_used = 0
    max_images = min(len(local_images), 3)
    if sections:
        result.append(sections[0])
    for i in range(1, len(sections)):
        if images_used < max_images and i <= max_images:
            img = local_images[images_used]
            image_md = f"\n![{img['alt']}]({img['path']})\n"
            result.append(image_md)
            images_used += 1
        result.append(sections[i])
    return "\n".join(result)


def estimate_rating_from_content(content: str) -> float:
    pros = len(re.findall(r"^[-*]\s", content, flags=re.MULTILINE))
    cons = content.lower().count("단점")
    base = 4.2
    adj = min(0.5, max(-0.5, (pros - cons) * 0.05))
    return round(base + adj, 1)


def generate_template_content(product_name: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
### 제품 소개
{product_name}는 최근 사용자들이 많이 찾는 제품입니다. 본 리뷰에서는 실제 사용 시나리오를 중심으로 핵심 기능과 체감 포인트를 정리합니다. (작성일: {today})

### 주요 특징
- 성능: 최신 칩셋/모듈을 적용해 일상 작업과 멀티태스킹에 충분한 성능을 제공합니다.
- 디스플레이: 120Hz 주사율, 최대 1600nit 밝기, 정확한 색 재현.
- 배터리: 4,400mAh 수준의 배터리로 일반 사용 기준 1일 사용 가능.
- 무게/크기: 약 190g, 두께 7.8mm로 휴대성 우수.

### 장점
- 디스플레이 품질이 우수해 야외(최대 1600nit)에서도 가독성이 뛰어납니다.
- 발열/소음 억제가 양호하고, 앱 전환 속도가 빠릅니다.
- 생태계/액세서리 연동성이 좋아 생산성 활용이 유리합니다.

### 단점
- 출고가가 높아 가성비 관점에선 부담이 있습니다.
- 기본 저장용량(128GB/256GB)은 대용량 촬영·앱 다중 설치 시 여유가 적을 수 있습니다.

### 경쟁 제품 비교
- 대안 A: 유사 성능 대비 가격 메리트가 크고, 무게가 더 가볍습니다.
- 대안 B: 카메라/오디오 특화로 콘텐츠 제작자에게 유리합니다.

### 가격 및 구매 팁
- 온라인 최저가 기준 100만원~150만원대 형성. 카드/포인트/번들 할인 확인을 권장합니다.
- 리퍼/공식 교육 할인/보상 판매 등 채널별 혜택을 비교하세요.

### FAQ
- Q. 배터리 시간은 어느 정도인가요?
  A. 일반 사용 기준 하루(스크린 온 5~7시간) 사용이 가능합니다.
- Q. 방수 방진 등급은?
  A. 일상 생활 방수(예: IP68 수준)로 비/땀에 대응 가능합니다.
- Q. 누구에게 추천하나요?
  A. 고주사율 화면·카메라·생태계 연동을 중시하는 사용자에게 적합합니다.

### 총평 및 추천 대상
{product_name}는 디스플레이·성능·연동 측면에서 완성도가 높습니다. 가격은 부담스럽지만, 최신 기능과 생태계 편의가 필요한 사용자에게 충분히 추천할 만합니다.
"""


def to_plain_text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        try:
            return " ".join(to_plain_text(v) for v in value)
        except Exception:
            return " ".join(str(v) for v in value)
    if isinstance(value, dict):
        for key in ("text", "content", "message", "data"):
            if key in value:
                return to_plain_text(value[key])
        try:
            return " ".join(to_plain_text(v) for v in value.values())
        except Exception:
            return str(value)
    return str(value)


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
    print("스타일을 예시 리뷰에 맞추고 싶다면 '@review-mx-master-4-ddc17c.md (1-276)' 처럼 끝에 붙여도 됩니다.")
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
