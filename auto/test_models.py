"""
다양한 모델로 LangGraph 테스트
LangGraph는 Function calling이 없어도 작동합니다!
"""

from config import get_llm, get_model_for_task, MODELS
from langgraph.graph import StateGraph, END
from typing import TypedDict
import os
from dotenv import load_dotenv

load_dotenv()


class SimpleState(TypedDict):
    """간단한 상태 정의"""
    input: str
    output: str


def simple_workflow_test(model_name="gpt-3.5-turbo"):
    """
    간단한 워크플로우로 모델 테스트
    Function calling 없이도 작동합니다!
    """

    print(f"\n{'='*60}")
    print(f"🧪 테스트 모델: {model_name}")
    print(f"{'='*60}")

    # 모델 정보
    model_info = MODELS.get(model_name, {})
    print(f"제공자: {model_info.get('provider', 'unknown')}")
    print(f"Function 지원: {model_info.get('supports_functions', False)}")
    print(f"비용: {model_info.get('cost', 'unknown')}")
    print("-" * 60)

    # LLM 가져오기
    try:
        llm = get_llm(model_name, temperature=0.5)
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return False

    # 간단한 노드 함수
    def process_node(state: SimpleState) -> SimpleState:
        """입력을 처리하는 노드"""
        from langchain_core.messages import HumanMessage, SystemMessage

        try:
            response = llm.invoke([
                SystemMessage(content="당신은 도움이 되는 어시스턴트입니다."),
                HumanMessage(content=f"다음 제품의 간단한 특징을 2줄로 설명해주세요: {state['input']}")
            ])

            # response가 문자열이면 그대로, 아니면 content 추출
            if hasattr(response, 'content'):
                state['output'] = response.content
            else:
                state['output'] = str(response)

            return state
        except Exception as e:
            print(f"⚠️ 처리 중 오류: {e}")
            state['output'] = f"오류 발생: {str(e)}"
            return state

    # LangGraph 워크플로우 생성
    workflow = StateGraph(SimpleState)
    workflow.add_node("process", process_node)
    workflow.set_entry_point("process")
    workflow.add_edge("process", END)

    # 컴파일
    app = workflow.compile()

    # 실행
    test_input = "애플워치"
    initial_state = {
        "input": test_input,
        "output": ""
    }

    print(f"입력: {test_input}")
    print("-" * 40)

    try:
        result = app.invoke(initial_state)
        print(f"출력: {result['output']}")
        print(f"✅ {model_name} 테스트 성공!")
        return True
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        return False


def test_cost_optimization():
    """
    비용 최적화된 모델 선택 테스트
    """
    print(f"\n{'='*60}")
    print("💰 작업별 최적 모델 선택")
    print(f"{'='*60}")

    tasks = ["research", "writing", "editing", "seo", "general"]

    for task in tasks:
        model = get_model_for_task(task)
        model_info = MODELS.get(model, {})
        print(f"• {task:10} → {model:15} (비용: {model_info.get('cost', 'unknown')})")


def test_free_models():
    """
    무료 모델 사용 예제
    """
    print(f"\n{'='*60}")
    print("🆓 무료/저렴한 모델 옵션")
    print(f"{'='*60}")

    free_models = [
        ("gpt-3.5-turbo", "저렴한 OpenAI 모델"),
        ("llama2", "무료 로컬 모델 (Ollama)"),
        ("mistral", "무료 로컬 모델 (Ollama)"),
        ("gemma", "무료 로컬 모델 (Ollama)")
    ]

    for model, desc in free_models:
        model_info = MODELS.get(model, {})
        print(f"\n📌 {model}")
        print(f"   설명: {desc}")
        print(f"   제공자: {model_info.get('provider', 'unknown')}")
        print(f"   비용: {model_info.get('cost', 'unknown')}")

        if model_info.get('provider') == 'ollama':
            print(f"   💡 팁: Ollama 설치 후 'ollama pull {model_info.get('model')}' 실행")


def main():
    """메인 실행 함수"""
    print("""
    🤖 LangGraph 모델 유연성 테스트
    ================================

    LangGraph는 다양한 모델과 함께 사용할 수 있습니다!
    Function calling이 반드시 필요한 것은 아닙니다.
    """)

    # 1. 비용 최적화 테스트
    test_cost_optimization()

    # 2. 무료 모델 옵션 표시
    test_free_models()

    # 3. 실제 모델 테스트
    print(f"\n{'='*60}")
    print("🚀 실제 모델 테스트")
    print(f"{'='*60}")

    # API 키가 있는 경우 테스트
    if os.getenv("OPENAI_API_KEY"):
        # 저렴한 모델로 테스트
        simple_workflow_test("gpt-3.5-turbo")
    else:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("💡 대안: Ollama 로컬 모델을 사용해보세요!")
        print("\n설치 방법:")
        print("1. Ollama 설치: curl -fsSL https://ollama.ai/install.sh | sh")
        print("2. 모델 다운로드: ollama pull llama2")
        print("3. 서버 시작: ollama serve")
        print("4. 이 스크립트 재실행")

    print(f"\n{'='*60}")
    print("📝 결론:")
    print("• LangGraph는 Function calling 없이도 작동합니다")
    print("• GPT-3.5-turbo 같은 저렴한 모델 사용 가능")
    print("• Ollama로 완전 무료 로컬 실행 가능")
    print("• 작업별로 다른 모델을 선택해 비용 최적화 가능")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()