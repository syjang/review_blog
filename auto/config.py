"""
모델 설정 파일
다양한 LLM 제공자와 모델을 사용할 수 있습니다
"""

import os
from dotenv import load_dotenv

load_dotenv()

# 사용 가능한 모델들
MODELS = {
    # OpenAI 모델들
    "gpt-4o": {
        "provider": "openai",
        "model": "gpt-4o",
        "supports_functions": True,
        "cost": "high"
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "supports_functions": True,
        "cost": "medium"
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "supports_functions": True,
        "cost": "low"
    },

    # Anthropic Claude (langchain-anthropic 설치 필요)
    "claude-3-opus": {
        "provider": "anthropic",
        "model": "claude-3-opus-20240229",
        "supports_functions": True,
        "cost": "high"
    },
    "claude-3-sonnet": {
        "provider": "anthropic",
        "model": "claude-3-sonnet-20240229",
        "supports_functions": True,
        "cost": "medium"
    },

    # Google Gemini (langchain-google-genai 설치 필요)
    "gemini-pro": {
        "provider": "google",
        "model": "gemini-pro",
        "supports_functions": False,
        "cost": "low"
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "model": "gemini-2.5-flash",
        "supports_functions": False,
        "cost": "low"
    },


    # Ollama 로컬 모델 (langchain-community 설치 필요)
    "gpt-oss": {
        "provider": "ollama",
        "model": "gpt-oss:20b",
        "supports_functions": False,
        "cost": "free"
    },
    "llama2": {
        "provider": "ollama",
        "model": "llama2",
        "supports_functions": False,
        "cost": "free"
    },
    "mistral": {
        "provider": "ollama",
        "model": "mistral",
        "supports_functions": False,
        "cost": "free"
    },
    "gemma": {
        "provider": "ollama",
        "model": "gemma",
        "supports_functions": False,
        "cost": "free"
    }
}

def get_llm(model_name="gpt-3.5-turbo", temperature=0.7):
    """
    선택한 모델의 LLM 인스턴스 반환

    Args:
        model_name: 사용할 모델 이름
        temperature: 생성 온도 (0~1)

    Returns:
        LLM 인스턴스
    """

    if model_name not in MODELS:
        print(f"⚠️ {model_name}은 지원하지 않는 모델입니다. gpt-3.5-turbo를 사용합니다.")
        model_name = "gpt-3.5-turbo"

    model_info = MODELS[model_name]
    provider = model_info["provider"]

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_info["model"],
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    elif provider == "anthropic":
        # pip install langchain-anthropic 필요
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=model_info["model"],
                temperature=temperature,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        except ImportError:
            print("⚠️ langchain-anthropic이 설치되지 않았습니다.")
            print("설치: pip install langchain-anthropic")
            return get_llm("gpt-3.5-turbo", temperature)

    elif provider == "google":
        # pip install langchain-google-genai 필요
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model_info["model"],
                temperature=temperature,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        except ImportError:
            print("⚠️ langchain-google-genai가 설치되지 않았습니다.")
            print("설치: pip install langchain-google-genai")
            return get_llm("gpt-3.5-turbo", temperature)

    elif provider == "ollama":
        # pip install langchain-community 필요
        # Ollama 로컬 서버가 실행 중이어야 함
        try:
            from langchain_community.llms import Ollama
            return Ollama(
                model=model_info["model"],
                temperature=temperature
            )
        except ImportError:
            print("⚠️ langchain-community가 설치되지 않았습니다.")
            print("설치: pip install langchain-community")
            return get_llm("gpt-3.5-turbo", temperature)
        except Exception as e:
            print(f"⚠️ Ollama 연결 실패: {e}")
            print("Ollama가 실행 중인지 확인하세요: ollama serve")
            return get_llm("gpt-3.5-turbo", temperature)

    else:
        print(f"⚠️ {provider}는 지원하지 않는 제공자입니다.")
        return get_llm("gpt-3.5-turbo", temperature)


# 비용 최적화를 위한 모델 선택 헬퍼
def get_model_for_task(task_type="general"):
    """
    작업 유형에 따라 적절한 모델 선택

    Args:
        task_type: 작업 유형 (research, writing, editing, seo, general)

    Returns:
        모델 이름
    """

    # 작업별 권장 모델
    task_models = {
        "research": "gpt-oss",  # 리서치는 로컬 모델로 무료!
        "writing": "gpt-oss",   # 작성도 로컬 모델
        "editing": "gpt-oss",   # 편집도 로컬 모델
        "seo": "gpt-oss",       # SEO도 로컬 모델
        "general": "gpt-oss"    # 일반 작업도 로컬
    }

    # 환경변수로 오버라이드 가능
    override = os.getenv(f"MODEL_{task_type.upper()}")
    if override:
        return override

    return task_models.get(task_type, "gpt-3.5-turbo")


# 로컬 모델 사용 예제
def use_local_model():
    """
    무료 로컬 모델 사용 예제
    Ollama 설치 필요: https://ollama.ai
    """

    print("🏠 로컬 모델 사용 예제")
    print("-" * 50)
    print("1. Ollama 설치: curl -fsSL https://ollama.ai/install.sh | sh")
    print("2. 모델 다운로드: ollama pull llama2")
    print("3. 서버 시작: ollama serve")
    print("4. 이 스크립트 실행")
    print("-" * 50)

    # 로컬 모델 사용
    llm = get_llm("llama2", temperature=0.7)

    # 테스트
    from langchain_core.messages import HumanMessage
    response = llm.invoke([
        HumanMessage(content="안녕하세요! 간단히 자기소개해주세요.")
    ])

    print(f"응답: {response.content}")
    return llm


if __name__ == "__main__":
    # 사용 가능한 모델 출력
    print("📋 사용 가능한 모델들:")
    print("-" * 50)
    for name, info in MODELS.items():
        print(f"• {name:15} | 제공자: {info['provider']:10} | 비용: {info['cost']:6} | Function: {info['supports_functions']}")

    print("\n💡 모델 사용 예제:")
    print("-" * 50)

    # 다양한 모델 테스트
    models_to_test = ["gpt-3.5-turbo", "gpt-4o-mini"]

    for model_name in models_to_test:
        print(f"\n테스트: {model_name}")
        llm = get_llm(model_name, temperature=0.5)
        print(f"✅ {model_name} 로드 성공")