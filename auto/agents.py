"""
특화된 에이전트들
각 에이전트는 특정 작업에 특화되어 있음
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os


class ResearchAgent:
    """리서치 에이전트 - 제품 정보 수집"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def research_product(self, product_name: str) -> Dict[str, Any]:
        """제품 정보 리서치"""
        prompt = f"""
        {product_name}에 대한 다음 정보를 조사해주세요:
        1. 주요 특징
        2. 장점과 단점
        3. 가격대
        4. 경쟁 제품
        5. 사용자 평가 요약
        """

        response = self.llm.invoke([
            SystemMessage(content="당신은 제품 리서치 전문가입니다."),
            HumanMessage(content=prompt)
        ])

        return {
            "product": product_name,
            "research": response.content
        }


class WriterAgent:
    """작성 에이전트 - 리뷰 컨텐츠 생성"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def write_review(self, research_data: Dict[str, Any]) -> str:
        """리뷰 작성"""
        style_guide = """
        - 1인칭 시점(‘저는’, ‘제 기준에서는’)으로, 사람이 직접 써 내려간 블로그 후기처럼 자연스럽게 씁니다.
        - 먼저 왜 이 제품을 알아보게 되었는지/구매하게 되었는지, 그리고 어떤 사용 환경을 기준으로 이야기하는지(사용 기간, 사용하는 기기, 주요 작업 등)를 짧게 소개합니다.
        - 장점/단점은 스펙 나열이 아니라, 어떤 상황에서 무엇이 어떻게 편했는지·아쉬웠는지를 구체적인 예시와 함께 설명합니다.
        - 가격·무게·휴대성·손 크기·사용 습관처럼 사람마다 갈릴 수 있는 포인트는 장단점 양쪽에서 균형 있게 다룹니다.
        - 마지막에는 어떤 사람에게 추천/비추천할지, 한두 문장으로 총평을 정리합니다.
        - 과장된 광고 문구 대신 담백하고 솔직한 표현을 사용합니다.
        - 다만, 모델이 실제로 제품을 사용했다고 단정하는 표현(예: \"제가 한 달 동안 직접 써봤는데\")은 피하고,
          \"여러 후기들을 보면\", \"실사용 후기를 종합하면\", \"제 기준에서라면\"처럼 표현합니다.
        """

        prompt = f"""
        아래 정보를 바탕으로, 사람 손으로 쓴 것 같은 자연스러운 한국어 제품 리뷰를 작성해주세요.

        [제품/리서치 데이터]
        {research_data}

        [스타일 가이드]
        {style_guide}

        [리뷰 구조]
        ### 제품 소개 & 구입 배경
        ### 사용 환경 정리
        ### 장점
        - 최소 3가지, 각각 2문장 이상
        ### 단점
        - 최소 2가지, 각각 2문장 이상
        ### 경쟁 제품/이전 세대 비교
        ### 가격 및 구매 팁
        ### 총평 및 추천 대상
        """

        response = self.llm.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 '리뷰 활짝' 블로그의 전문 리뷰어입니다. "
                        "실제 사용 후기를 참고해, 자연스럽고 솔직한 톤으로 글을 씁니다."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )

        return response.content


class EditorAgent:
    """편집 에이전트 - 컨텐츠 검토 및 개선"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def edit_content(self, content: str) -> Dict[str, Any]:
        """컨텐츠 편집 및 개선"""
        prompt = f"""
        다음 리뷰를 검토하고 개선해주세요:

        {content}

        체크 포인트:
        1. 문법 오류
        2. 정보의 정확성
        3. 가독성
        4. SEO 최적화
        5. 이모지 사용 (적절한 곳에)
        """

        response = self.llm.invoke([
            SystemMessage(content="당신은 전문 편집자입니다."),
            HumanMessage(content=prompt)
        ])

        return {
            "edited_content": response.content,
            "suggestions": "편집 완료"
        }


class SEOAgent:
    """SEO 에이전트 - SEO 최적화"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    def optimize_seo(self, content: str, product: str) -> Dict[str, Any]:
        """SEO 최적화"""
        prompt = f"""
        제품: {product}
        컨텐츠: {content[:500]}...

        다음을 생성해주세요:
        1. SEO 최적화된 제목
        2. 메타 설명 (150자 이내)
        3. 키워드 5개
        4. 태그 5개
        """

        response = self.llm.invoke([
            SystemMessage(content="당신은 SEO 전문가입니다."),
            HumanMessage(content=prompt)
        ])

        return {
            "seo_data": response.content
        }


class MarkdownAgent:
    """마크다운 에이전트 - 마크다운 포맷 생성"""

    def generate_markdown(self, content: str, metadata: Dict[str, Any]) -> str:
        """마크다운 파일 생성"""
        from datetime import datetime

        markdown = f"""---
title: '{metadata.get('title', '제목 없음')}'
date: '{datetime.now().strftime('%Y-%m-%d')}'
excerpt: '{metadata.get('excerpt', '요약 없음')}'
tags: {metadata.get('tags', [])}
coverImage: '/images/{metadata.get('image', 'default.jpg')}'
rating: {metadata.get('rating', 4.0)}
---

{content}
"""
        return markdown