export default function ReviewPolicyPage() {
  return (
    <main className="container mx-auto px-4 py-16 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">리뷰 정책</h1>
      <div className="text-slate-700 leading-7 space-y-4">
        <p>리뷰 활짝은 다음 기준에 따라 리뷰를 작성합니다.</p>
        <ul className="list-disc pl-6">
          <li>실사용 경험을 바탕으로 장점/단점을 구분합니다.</li>
          <li>수치·사양 등 객관 정보는 출처를 확인합니다.</li>
          <li>가격·대안·구매팁을 함께 제공합니다.</li>
          <li>협찬 시 명확히 표기하며, 편집권은 독립적으로 유지합니다.</li>
        </ul>
      </div>
    </main>
  );
}
