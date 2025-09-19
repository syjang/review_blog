"""
간단한 LangGraph 예제 - Function calling 없이!
이 예제는 가장 기본적인 LangGraph 사용법을 보여줍니다.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from config import get_llm
import os
from dotenv import load_dotenv

load_dotenv()


class BlogState(TypedDict):
    """블로그 리뷰 상태"""
    product: str
    intro: str
    pros: str
    cons: str
    conclusion: str
    final_review: str


def create_simple_workflow():
    """
    Function calling 없이 작동하는 간단한 워크플로우
    각 노드는 단순히 텍스트를 생성합니다.
    """

    # 저렴한 모델 사용 (gpt-3.5-turbo 또는 무료 모델)
    llm = get_llm("gpt-3.5-turbo", temperature=0.7)

    def write_intro(state: BlogState) -> BlogState:
        """서론 작성"""
        print("📝 서론 작성 중...")

        messages = [
            SystemMessage(content="당신은 리뷰 작성자입니다."),
            HumanMessage(content=f"{state['product']}에 대한 리뷰 서론을 2줄로 작성하세요.")
        ]

        response = llm.invoke(messages)
        state['intro'] = response.content if hasattr(response, 'content') else str(response)
        return state

    def write_pros(state: BlogState) -> BlogState:
        """장점 작성"""
        print("✅ 장점 작성 중...")

        messages = [
            SystemMessage(content="당신은 리뷰 작성자입니다."),
            HumanMessage(content=f"{state['product']}의 장점 3가지를 작성하세요.")
        ]

        response = llm.invoke(messages)
        state['pros'] = response.content if hasattr(response, 'content') else str(response)
        return state

    def write_cons(state: BlogState) -> BlogState:
        """단점 작성"""
        print("❌ 단점 작성 중...")

        messages = [
            SystemMessage(content="당신은 리뷰 작성자입니다."),
            HumanMessage(content=f"{state['product']}의 단점 2가지를 작성하세요.")
        ]

        response = llm.invoke(messages)
        state['cons'] = response.content if hasattr(response, 'content') else str(response)
        return state

    def write_conclusion(state: BlogState) -> BlogState:
        """결론 작성"""
        print("🎯 결론 작성 중...")

        messages = [
            SystemMessage(content="당신은 리뷰 작성자입니다."),
            HumanMessage(content=f"{state['product']}에 대한 최종 평가를 2줄로 작성하세요.")
        ]

        response = llm.invoke(messages)
        state['conclusion'] = response.content if hasattr(response, 'content') else str(response)
        return state

    def combine_review(state: BlogState) -> BlogState:
        """전체 리뷰 조합"""
        print("📄 최종 리뷰 생성 중...")

        final_review = f"""
# {state['product']} 리뷰

## 서론
{state['intro']}

## 장점
{state['pros']}

## 단점
{state['cons']}

## 결론
{state['conclusion']}
"""
        state['final_review'] = final_review
        return state

    # 워크플로우 생성
    workflow = StateGraph(BlogState)

    # 노드 추가 (각 노드는 독립적인 작업)
    workflow.add_node("intro", write_intro)
    workflow.add_node("pros", write_pros)
    workflow.add_node("cons", write_cons)
    workflow.add_node("conclusion", write_conclusion)
    workflow.add_node("combine", combine_review)

    # 순차적 실행 설정
    workflow.set_entry_point("intro")
    workflow.add_edge("intro", "pros")
    workflow.add_edge("pros", "cons")
    workflow.add_edge("cons", "conclusion")
    workflow.add_edge("conclusion", "combine")
    workflow.add_edge("combine", END)

    return workflow.compile()


def run_simple_review(product_name: str):
    """간단한 리뷰 실행"""
    print(f"\n{'='*60}")
    print(f"🚀 간단한 리뷰 생성: {product_name}")
    print(f"{'='*60}\n")

    # 워크플로우 생성
    app = create_simple_workflow()

    # 초기 상태
    initial_state = {
        "product": product_name,
        "intro": "",
        "pros": "",
        "cons": "",
        "conclusion": "",
        "final_review": ""
    }

    # 실행
    try:
        result = app.invoke(initial_state)
        print("\n" + "="*60)
        print("✨ 리뷰 생성 완료!")
        print("="*60)
        print(result['final_review'])
        return result['final_review']
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. .env 파일에 OPENAI_API_KEY 설정")
        print("2. 또는 Ollama 로컬 모델 사용")
        return None


def main():
    """메인 함수"""
    print("""
    🌟 간단한 LangGraph 워크플로우 예제
    =====================================

    Function calling 없이 작동하는 예제입니다.
    각 노드는 단순히 LLM을 호출하여 텍스트를 생성합니다.
    """)

    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("\n대안:")
        print("1. .env 파일에 OPENAI_API_KEY 설정")
        print("2. config.py에서 Ollama 모델로 변경")
        return

    # 테스트 실행
    products = [
        "샤오미 로봇청소기",
        "에어팟 프로 2",
        "스타벅스 텀블러"
    ]

    print("테스트할 제품을 선택하세요:")
    for i, product in enumerate(products, 1):
        print(f"{i}. {product}")

    choice = input("\n선택 (1-3, 또는 직접 입력): ").strip()

    if choice in ["1", "2", "3"]:
        product = products[int(choice) - 1]
    else:
        product = choice if choice else products[0]

    # 리뷰 생성
    run_simple_review(product)


if __name__ == "__main__":
    main()