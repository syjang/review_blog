"""
다양한 워크플로우 정의
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MemorySaver
from agents import ResearchAgent, WriterAgent, EditorAgent, SEOAgent, MarkdownAgent
import json


class ReviewState(TypedDict):
    """리뷰 작성 워크플로우 상태"""
    product_name: str
    research_data: Dict[str, Any]
    raw_content: str
    edited_content: str
    seo_data: Dict[str, Any]
    markdown: str
    status: str
    error: str


class ReviewWorkflow:
    """리뷰 작성 자동화 워크플로우"""

    def __init__(self):
        self.research_agent = ResearchAgent()
        self.writer_agent = WriterAgent()
        self.editor_agent = EditorAgent()
        self.seo_agent = SEOAgent()
        self.markdown_agent = MarkdownAgent()

    def research_node(self, state: ReviewState) -> ReviewState:
        """제품 리서치"""
        print(f"🔍 {state['product_name']} 리서치 중...")
        try:
            research_data = self.research_agent.research_product(state["product_name"])
            state["research_data"] = research_data
            state["status"] = "research_completed"
        except Exception as e:
            state["error"] = f"리서치 오류: {str(e)}"
            state["status"] = "error"
        return state

    def write_node(self, state: ReviewState) -> ReviewState:
        """리뷰 작성"""
        print(f"✍️ 리뷰 작성 중...")
        try:
            content = self.writer_agent.write_review(state["research_data"])
            state["raw_content"] = content
            state["status"] = "writing_completed"
        except Exception as e:
            state["error"] = f"작성 오류: {str(e)}"
            state["status"] = "error"
        return state

    def edit_node(self, state: ReviewState) -> ReviewState:
        """리뷰 편집"""
        print(f"📝 리뷰 편집 중...")
        try:
            result = self.editor_agent.edit_content(state["raw_content"])
            state["edited_content"] = result["edited_content"]
            state["status"] = "editing_completed"
        except Exception as e:
            state["error"] = f"편집 오류: {str(e)}"
            state["status"] = "error"
        return state

    def seo_node(self, state: ReviewState) -> ReviewState:
        """SEO 최적화"""
        print(f"🎯 SEO 최적화 중...")
        try:
            seo_data = self.seo_agent.optimize_seo(
                state["edited_content"],
                state["product_name"]
            )
            state["seo_data"] = seo_data
            state["status"] = "seo_completed"
        except Exception as e:
            state["error"] = f"SEO 오류: {str(e)}"
            state["status"] = "error"
        return state

    def markdown_node(self, state: ReviewState) -> ReviewState:
        """마크다운 생성"""
        print(f"📄 마크다운 생성 중...")
        try:
            # SEO 데이터 파싱 (간단한 예제)
            metadata = {
                "title": f"{state['product_name']} 리뷰",
                "excerpt": f"{state['product_name']}에 대한 상세 리뷰",
                "tags": ["리뷰", state['product_name'].split()[0]],
                "rating": 4.0
            }

            markdown = self.markdown_agent.generate_markdown(
                state["edited_content"],
                metadata
            )
            state["markdown"] = markdown
            state["status"] = "completed"
        except Exception as e:
            state["error"] = f"마크다운 생성 오류: {str(e)}"
            state["status"] = "error"
        return state

    def create_graph(self):
        """워크플로우 그래프 생성"""
        workflow = StateGraph(ReviewState)

        # 노드 추가
        workflow.add_node("research", self.research_node)
        workflow.add_node("write", self.write_node)
        workflow.add_node("edit", self.edit_node)
        workflow.add_node("seo", self.seo_node)
        workflow.add_node("markdown", self.markdown_node)

        # 엣지 설정
        workflow.set_entry_point("research")
        workflow.add_edge("research", "write")
        workflow.add_edge("write", "edit")
        workflow.add_edge("edit", "seo")
        workflow.add_edge("seo", "markdown")
        workflow.add_edge("markdown", END)

        # 컴파일
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)


class QuickReviewWorkflow:
    """빠른 리뷰 워크플로우 (리서치 없이)"""

    def __init__(self):
        self.writer_agent = WriterAgent()
        self.markdown_agent = MarkdownAgent()

    def write_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 리뷰 작성"""
        print(f"✍️ 빠른 리뷰 작성 중...")
        prompt_data = {
            "product": state["product_name"],
            "key_points": state.get("key_points", [])
        }

        content = self.writer_agent.write_review(prompt_data)
        state["content"] = content
        return state

    def markdown_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """마크다운 생성"""
        print(f"📄 마크다운 생성 중...")
        metadata = {
            "title": f"{state['product_name']} 간단 리뷰",
            "excerpt": "빠르게 작성한 리뷰",
            "tags": ["간단리뷰"],
            "rating": 3.5
        }

        markdown = self.markdown_agent.generate_markdown(
            state["content"],
            metadata
        )
        state["markdown"] = markdown
        state["status"] = "completed"
        return state

    def create_graph(self):
        """워크플로우 그래프 생성"""
        workflow = StateGraph(dict)

        workflow.add_node("write", self.write_node)
        workflow.add_node("markdown", self.markdown_node)

        workflow.set_entry_point("write")
        workflow.add_edge("write", "markdown")
        workflow.add_edge("markdown", END)

        return workflow.compile()


# 워크플로우 실행 헬퍼 함수
def run_review_workflow(product_name: str):
    """리뷰 워크플로우 실행"""
    workflow = ReviewWorkflow()
    app = workflow.create_graph()

    initial_state = {
        "product_name": product_name,
        "research_data": {},
        "raw_content": "",
        "edited_content": "",
        "seo_data": {},
        "markdown": "",
        "status": "started",
        "error": ""
    }

    config = {"configurable": {"thread_id": f"review_{product_name}"}}

    print(f"\n🚀 '{product_name}' 리뷰 작성 시작\n")
    print("=" * 50)

    for output in app.stream(initial_state, config):
        for key, value in output.items():
            print(f"✅ {key} 완료")

    final_state = app.get_state(config)
    return final_state.values


def run_quick_review(product_name: str, key_points: List[str] = None):
    """빠른 리뷰 실행"""
    workflow = QuickReviewWorkflow()
    app = workflow.create_graph()

    initial_state = {
        "product_name": product_name,
        "key_points": key_points or [],
        "content": "",
        "markdown": "",
        "status": "started"
    }

    print(f"\n⚡ '{product_name}' 빠른 리뷰 작성\n")
    print("=" * 50)

    for output in app.stream(initial_state):
        for key, value in output.items():
            print(f"✅ {key} 완료")

    return initial_state