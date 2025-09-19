"""
Ollama 로컬 모델 테스트
완전 무료로 LangGraph 사용하기!
"""

from config import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

def test_ollama():
    """Ollama 모델 테스트"""
    print("🚀 Ollama gpt-oss:20b 모델 테스트")
    print("="*60)

    # gpt-oss 모델 사용
    llm = get_llm("gpt-oss", temperature=0.7)

    # 간단한 테스트
    messages = [
        SystemMessage(content="당신은 친절한 리뷰 작성자입니다."),
        HumanMessage(content="애플워치의 장점을 3가지 알려주세요.")
    ]

    print("📝 요청: 애플워치의 장점 3가지")
    print("-"*40)

    try:
        response = llm.invoke(messages)
        print("✅ 응답:")
        print(response.content if hasattr(response, 'content') else response)
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_ollama()