"""
웹 검색 도구 모음
제품 리뷰를 위한 최신 정보 검색
"""

from duckduckgo_search import DDGS
from typing import List, Dict
import time
from random import uniform
import httpx


class WebSearcher:
    """웹 검색 도구"""

    def __init__(self):
        # User-Agent 헤더와 타임아웃 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.delay_range = (2.0, 4.0)  # 요청 간 지연 시간 범위 (증가)
        self.max_retries = 3  # 최대 재시도 횟수

    def _search_with_retry(self, search_func, *args, **kwargs):
        """
        재시도 로직이 포함된 검색 실행
        """
        for attempt in range(self.max_retries):
            try:
                # 첫 번째 시도가 아니면 지연 시간 추가
                if attempt > 0:
                    delay = uniform(*self.delay_range) * (attempt + 1)  # 재시도마다 지연 증가
                    print(f"⏳ {delay:.1f}초 대기 중... (재시도 {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    # 첫 시도에도 약간의 지연 추가
                    time.sleep(uniform(0.5, 1.0))

                # 매번 새로운 DDGS 인스턴스 생성 (세션 초기화)
                with DDGS(headers=self.headers, timeout=30) as ddgs:
                    results = search_func(ddgs, *args, **kwargs)

                # 성공하면 다음 요청을 위해 지연
                time.sleep(uniform(1.0, 2.0))

                return results

            except Exception as e:
                error_msg = str(e)
                # Rate limit 관련 에러 체크
                if any(x in error_msg.lower() for x in ['ratelimit', 'rate limit', '429', '202']):
                    if attempt < self.max_retries - 1:
                        print(f"⚠️ Rate limit 감지. 재시도 준비중...")
                        continue
                    else:
                        print(f"❌ 최대 재시도 횟수 초과: {e}")
                        return []  # raise 대신 빈 리스트 반환
                # "Exception occurred in previous call" 처리
                elif 'exception occurred in previous call' in error_msg.lower():
                    print(f"⚠️ 이전 호출 오류로 인한 건너뛰기")
                    return []
                else:
                    print(f"❌ 검색 오류: {e}")
                    return []  # raise 대신 빈 리스트 반환

        return []

    def search_product_info(self, product_name: str, max_results: int = 5) -> List[Dict]:
        """
        제품 정보 검색

        Args:
            product_name: 검색할 제품명
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        print(f"🔍 '{product_name}' 검색 중...")

        try:
            # 제품 리뷰 및 사양 검색
            search_query = f"{product_name} 리뷰 사양 특징"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=max_results,
                    region='kr-kr',  # 한국 지역 검색
                    safesearch='moderate'
                ))
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return formatted_results

        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            return []

    def search_product_price(self, product_name: str) -> List[Dict]:
        """
        제품 가격 정보 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            가격 정보 리스트
        """
        print(f"💰 '{product_name}' 가격 검색 중...")

        try:
            # 가격 정보 검색
            search_query = f"{product_name} 가격 최저가"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=3,
                    region='kr-kr'
                ))
            )

            price_info = []
            for result in results:
                price_info.append({
                    "source": result.get("title", ""),
                    "description": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return price_info

        except Exception as e:
            print(f"❌ 가격 검색 오류: {e}")
            return []

    def search_recent_news(self, product_name: str) -> List[Dict]:
        """
        제품 관련 최신 뉴스 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            뉴스 리스트
        """
        print(f"📰 '{product_name}' 뉴스 검색 중...")

        try:
            # 재시도 로직이 포함된 뉴스 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.news(
                    f"{product_name}",
                    max_results=3,
                    region='kr-kr'
                ))
            )

            news = []
            for result in results:
                news.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", ""),
                    "url": result.get("url", "")
                })

            return news

        except Exception as e:
            print(f"❌ 뉴스 검색 오류: {e}")
            return []

    def search_user_reviews(self, product_name: str) -> List[Dict]:
        """
        사용자 리뷰 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            리뷰 정보 리스트
        """
        print(f"⭐ '{product_name}' 사용자 리뷰 검색 중...")

        try:
            # 사용자 리뷰 검색
            search_query = f"{product_name} 사용후기 장단점 실사용"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=5,
                    region='kr-kr'
                ))
            )

            reviews = []
            for result in results:
                reviews.append({
                    "title": result.get("title", ""),
                    "summary": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return reviews

        except Exception as e:
            print(f"❌ 리뷰 검색 오류: {e}")
            return []

    def get_comprehensive_info(self, product_name: str) -> Dict:
        """
        제품에 대한 종합 정보 수집

        Args:
            product_name: 검색할 제품명

        Returns:
            종합 정보 딕셔너리
        """
        print(f"🎯 '{product_name}' 종합 정보 수집 시작...")
        print("="*60)
        print("⚠️ Rate limit 방지를 위해 검색 간 지연 시간이 적용됩니다...")

        comprehensive_info = {
            "product": product_name,
            "basic_info": self.search_product_info(product_name),
            "price_info": self.search_product_price(product_name),
            "recent_news": self.search_recent_news(product_name),
            "user_reviews": self.search_user_reviews(product_name)
        }

        print("="*60)
        print(f"✅ 종합 정보 수집 완료!")

        return comprehensive_info


def format_search_results(search_data: Dict) -> str:
    """
    검색 결과를 마크다운 형식으로 포맷팅

    Args:
        search_data: 검색 결과 데이터

    Returns:
        포맷팅된 마크다운 문자열
    """
    markdown = f"# {search_data['product']} 검색 결과\n\n"

    # 기본 정보
    if search_data.get("basic_info"):
        markdown += "## 📋 제품 정보\n\n"
        for info in search_data["basic_info"][:3]:
            markdown += f"### {info['title']}\n"
            markdown += f"{info['body']}\n"
            markdown += f"[자세히 보기]({info['url']})\n\n"

    # 가격 정보
    if search_data.get("price_info"):
        markdown += "## 💰 가격 정보\n\n"
        for price in search_data["price_info"]:
            markdown += f"- **{price['source']}**: {price['description']}\n"

    # 최신 뉴스
    if search_data.get("recent_news"):
        markdown += "\n## 📰 최신 뉴스\n\n"
        for news in search_data["recent_news"]:
            markdown += f"- **{news['title']}** ({news.get('date', 'N/A')})\n"
            markdown += f"  {news['body'][:100]}...\n"

    # 사용자 리뷰
    if search_data.get("user_reviews"):
        markdown += "\n## ⭐ 사용자 리뷰\n\n"
        for review in search_data["user_reviews"][:3]:
            markdown += f"- {review['title']}\n"
            markdown += f"  {review['summary'][:100]}...\n"

    return markdown


# 테스트 코드
if __name__ == "__main__":
    searcher = WebSearcher()

    # 테스트할 제품
    test_product = "갤럭시 S24 울트라"

    print(f"🔍 테스트 제품: {test_product}")
    print("-"*60)

    # 종합 정보 수집
    info = searcher.get_comprehensive_info(test_product)

    # 결과 출력
    print("\n📊 수집된 정보:")
    print(f"- 기본 정보: {len(info['basic_info'])}개")
    print(f"- 가격 정보: {len(info['price_info'])}개")
    print(f"- 최신 뉴스: {len(info['recent_news'])}개")
    print(f"- 사용자 리뷰: {len(info['user_reviews'])}개")

    # 마크다운 포맷팅
    markdown_result = format_search_results(info)

    print("\n📝 마크다운 결과 (첫 500자):")
    print(markdown_result[:500])