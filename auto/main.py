"""
리뷰 블로그 자동화 시스템
LangGraph를 사용한 블로그 관리 자동화
"""

import os
from typing import TypedDict, Annotated, List
from datetime import datetime
from dotenv import load_dotenv

from langgraph.graph import Graph, StateGraph, END
from langgraph.checkpoint import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from config import get_llm

# 환경 변수 로드
load_dotenv()

# LLM 설정
llm = get_llm("gpt-oss", temperature=0.1)


# 상태 정의
class BlogState(TypedDict):
    task: str
    posts: List[dict]
    current_post: dict
    feedback: str
    completed: bool


# 노드 함수들
def analyze_task(state: BlogState) -> BlogState:
    """작업 분석 노드"""
    task = state.get("task", "")

    print(f"📋 작업 분석 중: {task}")

    # 작업 유형 분석
    if "리뷰" in task or "포스트" in task:
        state["current_post"] = {"type": "review", "status": "analyzing"}
    elif "수정" in task or "업데이트" in task:
        state["current_post"] = {"type": "update", "status": "analyzing"}
    else:
        state["current_post"] = {"type": "general", "status": "analyzing"}

    return state


def generate_content(state: BlogState) -> BlogState:
    """컨텐츠 생성 노드"""
    task = state.get("task", "")
    post_type = state.get("current_post", {}).get("type", "general")

    print(f"✍️ 컨텐츠 생성 중...")

    # LLM을 사용해 컨텐츠 생성
    system_prompt = """
    당신은 리뷰 블로그 '리뷰 활짝'의 컨텐츠 작성자입니다.
    솔직하고 상세한 제품 리뷰를 작성해주세요.
    """

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"다음 작업을 수행하세요: {task}"),
        ]
    )

    state["current_post"]["content"] = response.content
    state["current_post"]["status"] = "generated"
    state["current_post"]["created_at"] = datetime.now().isoformat()

    return state


def create_markdown(state: BlogState) -> BlogState:
    """마크다운 파일 생성 노드"""
    current_post = state.get("current_post", {})
    content = current_post.get("content", "")

    print(f"📝 마크다운 파일 생성 중...")

    # 마크다운 포맷으로 변환
    markdown_template = f"""---
title: '자동 생성된 리뷰 포스트'
date: '{datetime.now().strftime("%Y-%m-%d")}'
excerpt: '자동으로 생성된 리뷰입니다.'
tags: ['자동생성']
---

{content}
"""

    state["current_post"]["markdown"] = markdown_template
    state["current_post"]["status"] = "markdown_created"

    return state


def save_post(state: BlogState) -> BlogState:
    """포스트 저장 노드"""
    current_post = state.get("current_post", {})
    markdown = current_post.get("markdown", "")

    print(f"💾 포스트 저장 중...")

    # 파일명 생성
    filename = f"auto_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = f"../app/posts/{filename}"

    # 실제 저장 (데모이므로 출력만)
    print(f"파일 경로: {filepath}")
    print(f"내용:\n{markdown[:200]}...")

    state["current_post"]["filename"] = filename
    state["current_post"]["status"] = "saved"
    state["completed"] = True

    return state


def review_content(state: BlogState) -> BlogState:
    """컨텐츠 검토 노드"""
    content = state.get("current_post", {}).get("content", "")

    print(f"🔍 컨텐츠 검토 중...")

    # 간단한 검토 로직
    if len(content) < 100:
        state["feedback"] = "컨텐츠가 너무 짧습니다. 더 자세한 내용이 필요합니다."
        state["current_post"]["needs_revision"] = True
    else:
        state["feedback"] = "컨텐츠가 적절합니다."
        state["current_post"]["needs_revision"] = False

    return state


# 조건부 엣지 함수
def should_revise(state: BlogState) -> str:
    """수정이 필요한지 판단"""
    if state.get("current_post", {}).get("needs_revision", False):
        return "revise"
    return "continue"


# 그래프 구축
def create_workflow():
    """워크플로우 그래프 생성"""

    workflow = StateGraph(BlogState)

    # 노드 추가
    workflow.add_node("analyze", analyze_task)
    workflow.add_node("generate", generate_content)
    workflow.add_node("review", review_content)
    workflow.add_node("markdown", create_markdown)
    workflow.add_node("save", save_post)

    # 엣지 설정
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("generate", "review")

    # 조건부 엣지
    workflow.add_conditional_edges(
        "review", should_revise, {"revise": "generate", "continue": "markdown"}
    )

    workflow.add_edge("markdown", "save")
    workflow.add_edge("save", END)

    # 체크포인트 설정
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app


# 메인 실행 함수
def main():
    """메인 실행 함수"""
    print("🚀 리뷰 블로그 자동화 시스템 시작")
    print("-" * 50)

    # 워크플로우 생성
    app = create_workflow()

    # 테스트 작업
    initial_state = {
        "task": "애플 에어팟 프로 2세대에 대한 간단한 리뷰를 작성해주세요",
        "posts": [],
        "current_post": {},
        "feedback": "",
        "completed": False,
    }

    # 워크플로우 실행
    config = {"configurable": {"thread_id": "test_thread"}}

    print(f"📌 작업: {initial_state['task']}")
    print("-" * 50)

    # 스트리밍으로 실행
    for output in app.stream(initial_state, config):
        for key, value in output.items():
            print(f"✅ {key} 노드 완료")

    print("-" * 50)
    print("✨ 자동화 작업 완료!")


if __name__ == "__main__":
    main()
