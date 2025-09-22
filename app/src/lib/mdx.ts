import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import remarkGfm from 'remark-gfm';
import remarkHtml from 'remark-html';
import { rehype } from 'rehype';
import rehypeSlug from 'rehype-slug';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypePrismPlus from 'rehype-prism-plus';
import rehypeStringify from 'rehype-stringify';
import readingTime from 'reading-time';

const postsDirectory = path.join(process.cwd(), 'posts');

export interface Post {
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

export function getAllPosts(): Post[] {
  const fileNames = fs.readdirSync(postsDirectory);
  const allPostsData = fileNames
    .filter((fileName) => fileName.endsWith('.md') || fileName.endsWith('.mdx'))
    .map((fileName) => {
      const slug = fileName.replace(/\.mdx?$/, '');
      const fullPath = path.join(postsDirectory, fileName);
      const fileContents = fs.readFileSync(fullPath, 'utf8');
      const { data, content } = matter(fileContents);
      const stats = readingTime(content);

      // front matter 호환: image -> coverImage 폴백
      const coverImage = (data.coverImage || data.image) as string | undefined;

      return {
        slug,
        content,
        title: data.title,
        date: data.date,
        excerpt: data.excerpt || content.slice(0, 160) + '...',
        readingTime: stats.text,
        tags: data.tags || [],
        coverImage,
        rating: data.rating,
      };
    });

  return allPostsData.sort((a, b) => (a.date < b.date ? 1 : -1));
}

export function getPostBySlug(slug: string): Post | undefined {
  const realSlug = slug.replace(/\.mdx?$/, '');
  const fullPath = path.join(postsDirectory, `${realSlug}.md`);
  const fullPathMdx = path.join(postsDirectory, `${realSlug}.mdx`);

  let fileContents: string;

  if (fs.existsSync(fullPath)) {
    fileContents = fs.readFileSync(fullPath, 'utf8');
  } else if (fs.existsSync(fullPathMdx)) {
    fileContents = fs.readFileSync(fullPathMdx, 'utf8');
  } else {
    return undefined;
  }

  const { data, content } = matter(fileContents);
  const stats = readingTime(content);

  // front matter 호환: image -> coverImage 폴백
  const coverImage = (data.coverImage || data.image) as string | undefined;

  return {
    slug: realSlug,
    content,
    title: data.title,
    date: data.date,
    excerpt: data.excerpt || content.slice(0, 160) + '...',
    readingTime: stats.text,
    tags: data.tags || [],
    coverImage,
    rating: data.rating,
  };
}

export async function markdownToHtml(markdown: string) {
  const processedContent = await remark()
    .use(remarkGfm)
    .use(remarkHtml)
    .process(markdown);

  const htmlContent = processedContent.toString();

  const rehypeResult = await rehype()
    .data('settings', { fragment: true })
    .use(rehypeSlug)
    .use(rehypeAutolinkHeadings, {
      behavior: 'wrap',
      properties: {
        className: ['anchor'],
      },
    })
    .use(rehypePrismPlus, {
      showLineNumbers: true,
      ignoreMissing: true,
    })
    .use(rehypeStringify)
    .process(htmlContent);

  return rehypeResult.toString();
}