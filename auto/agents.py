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
        prompt = f"""
        다음 정보를 바탕으로 솔직하고 상세한 제품 리뷰를 작성해주세요:

        {research_data}

        리뷰 구조:
        - 구매 동기
        - 장점 (3개 이상)
        - 단점 (2개 이상)
        - 실사용 경험
        - 총평
        - 추천/비추천 대상
        """

        response = self.llm.invoke([
            SystemMessage(content="당신은 '리뷰 활짝' 블로그의 전문 리뷰어입니다. 솔직하고 실용적인 리뷰를 작성합니다."),
            HumanMessage(content=prompt)
        ])

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