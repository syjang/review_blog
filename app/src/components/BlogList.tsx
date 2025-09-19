'use client';

import Link from 'next/link';
import { useState, useMemo } from 'react';

interface Post {
  slug: string;
  title: string;
  date: string;
  excerpt: string;
  content: string;
  readingTime: string;
  tags?: string[];
  coverImage?: string;
  rating?: number;
}

interface BlogListProps {
  posts: Post[];
}

const categories = ['전체', '전자기기', '생활용품', '뷰티', '패션'];

export default function BlogList({ posts }: BlogListProps) {
  const [selectedCategory, setSelectedCategory] = useState('전체');

  const filteredPosts = useMemo(() => {
    if (selectedCategory === '전체') {
      return posts;
    }
    return posts.filter(post =>
      post.tags?.some(tag => tag === selectedCategory)
    );
  }, [selectedCategory, posts]);

  return (
    <>
      <div className="flex flex-wrap gap-4 justify-center mb-12">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-5 py-2.5 rounded-full font-medium transition-all transform hover:scale-105 ${
              selectedCategory === category
                ? 'bg-slate-900 text-white shadow-lg'
                : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {filteredPosts.length > 0 ? (
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPosts.map((post) => (
            <article
              key={post.slug}
              className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group"
            >
              <Link href={`/blog/${post.slug}`}>
                <div className="aspect-[16/10] bg-gradient-to-br from-blue-100 to-purple-100 relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center text-6xl">
                    {post.tags?.includes('전자기기') && '💻'}
                    {post.tags?.includes('생활용품') && '🏠'}
                    {post.tags?.includes('뷰티') && '💄'}
                    {post.tags?.includes('패션') && '👕'}
                    {!post.tags?.some(tag => ['전자기기', '생활용품', '뷰티', '패션'].includes(tag)) && '📦'}
                  </div>
                </div>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-slate-900 mb-2 group-hover:text-blue-600 transition-colors line-clamp-2">
                    {post.title}
                  </h2>

                  <div className="flex items-center gap-3 text-sm text-slate-500 mb-3">
                    <time dateTime={post.date}>
                      {new Date(post.date).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'numeric',
                        day: 'numeric',
                      })}
                    </time>
                    <span>·</span>
                    <span>{post.readingTime}</span>
                    {post.rating && (
                      <>
                        <span>·</span>
                        <span className="flex items-center gap-1">
                          <span className="text-yellow-500">★</span>
                          <span>{post.rating}/5</span>
                        </span>
                      </>
                    )}
                  </div>

                  <p className="text-slate-600 mb-4 line-clamp-3 text-sm">
                    {post.excerpt}
                  </p>

                  {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {post.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2.5 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded-md"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </Link>
            </article>
          ))}
        </section>
      ) : (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-slate-500 text-lg">
            {selectedCategory === '전체'
              ? '아직 작성된 리뷰가 없습니다.'
              : `${selectedCategory} 카테고리에 리뷰가 없습니다.`}
          </p>
        </div>
      )}
    </>
  );
}