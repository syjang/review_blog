'use client';

import Link from 'next/link';
import Image from 'next/image';
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

const POSTS_PER_PAGE = 12;

export default function BlogList({ posts }: BlogListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredPosts = useMemo(() => {
    if (!searchQuery.trim()) {
      return posts;
    }

    const query = searchQuery.toLowerCase();
    return posts.filter(post =>
      post.title.toLowerCase().includes(query) ||
      post.excerpt.toLowerCase().includes(query) ||
      post.content.toLowerCase().includes(query) ||
      post.tags?.some(tag => tag.toLowerCase().includes(query))
    );
  }, [searchQuery, posts]);

  const totalPages = Math.ceil(filteredPosts.length / POSTS_PER_PAGE);

  const paginatedPosts = useMemo(() => {
    const startIndex = (currentPage - 1) * POSTS_PER_PAGE;
    const endIndex = startIndex + POSTS_PER_PAGE;
    return filteredPosts.slice(startIndex, endIndex);
  }, [filteredPosts, currentPage]);

  // Reset to first page when search changes
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  return (
    <>
      <div className="flex justify-center mb-12">
        <div className="relative w-full max-w-md">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            placeholder="리뷰 검색... (제목, 내용, 태그)"
            value={searchQuery}
            onChange={handleSearchChange}
            className="block w-full pl-10 pr-3 py-3 border border-slate-300 rounded-lg leading-5 bg-white text-slate-900 placeholder-slate-500 focus:outline-none focus:placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {paginatedPosts.length > 0 ? (
        <>
          <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedPosts.map((post) => (
            <article
              key={post.slug}
              className="bg-white rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden group"
            >
              <Link href={`/blog/${post.slug}`}>
                <div className="aspect-[16/10] bg-gradient-to-br from-blue-100 to-purple-100 relative overflow-hidden">
                  {post.coverImage ? (
                    <Image
                      src={post.coverImage}
                      alt={post.title}
                      fill
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                      className="object-cover transition-transform duration-500 group-hover:scale-105"
                      priority={false}
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-6xl">
                      {post.tags?.includes('전자기기') && '💻'}
                      {post.tags?.includes('생활용품') && '🏠'}
                      {post.tags?.includes('뷰티') && '💄'}
                      {post.tags?.includes('패션') && '👕'}
                      {!post.tags?.some(tag => ['전자기기', '생활용품', '뷰티', '패션'].includes(tag)) && '📦'}
                    </div>
                  )}
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

          {totalPages > 1 && (
            <div className="flex justify-center mt-12">
              <nav className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-2 rounded-md text-sm font-medium text-slate-500 hover:text-slate-700 disabled:text-slate-300 disabled:cursor-not-allowed"
                >
                  이전
                </button>

                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50'
                    }`}
                  >
                    {page}
                  </button>
                ))}

                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 rounded-md text-sm font-medium text-slate-500 hover:text-slate-700 disabled:text-slate-300 disabled:cursor-not-allowed"
                >
                  다음
                </button>
              </nav>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-slate-500 text-lg">
            {searchQuery.trim()
              ? `"${searchQuery}" 검색 결과가 없습니다.`
              : '아직 작성된 리뷰가 없습니다.'}
          </p>
        </div>
      )}
    </>
  );
}