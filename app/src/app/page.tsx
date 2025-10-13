import BlogList from '@/components/BlogList';
import { getAllPosts } from '@/lib/mdx';
import type { Metadata } from 'next';
import { getSiteUrl } from '@/lib/site';

export const metadata: Metadata = {
  alternates: {
    canonical: getSiteUrl(),
  },
};

export default function HomePage() {
  const posts = getAllPosts();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <main className="container mx-auto px-4 py-16 max-w-6xl">
        <header className="mb-16 text-center">
          <h1 className="text-5xl font-bold text-slate-900 mb-4">
            All Review 블로그 - 리뷰활짝
          </h1>
          <p className="text-xl text-slate-600">
            세상의 모든 제품 리뷰
          </p>
        </header>

        <BlogList posts={posts} />
      </main>
    </div>
  );
}