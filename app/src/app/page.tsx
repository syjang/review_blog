import BlogList from '@/components/BlogList';
import { getAllPosts } from '@/lib/mdx';

export default function HomePage() {
  const posts = getAllPosts();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <main className="container mx-auto px-4 py-16 max-w-6xl">
        <header className="mb-16 text-center">
          <h1 className="text-5xl font-bold text-slate-900 mb-4">
            리뷰 활짝
          </h1>
          <p className="text-xl text-slate-600">
            진짜 사용해본 제품들의 솔직한 리뷰
          </p>
        </header>

        <BlogList posts={posts} />
      </main>
    </div>
  );
}