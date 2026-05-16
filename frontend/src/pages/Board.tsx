import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchPosts, fetchPost, createPost } from '../api/stockApi'
import { Post, PostCategory } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'

const CATEGORY_COLORS: Record<PostCategory, string> = {
  '버그제보': 'bg-red-500/20 text-red-400 border-red-500/30',
  '기능제안': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  '기타': 'bg-gray-700 text-gray-400 border-gray-600',
}

function CategoryBadge({ category }: { category: PostCategory }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${CATEGORY_COLORS[category]}`}>
      {category}
    </span>
  )
}

function PostDetail({ postId, onBack }: { postId: number; onBack: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ['post', postId],
    queryFn: () => fetchPost(postId),
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <LoadingSpinner size="md" />
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="flex flex-col gap-4">
      <button
        className="self-start text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
        onClick={onBack}
      >
        ← 목록으로
      </button>
      <div className="bg-gray-900 rounded-xl p-6 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <CategoryBadge category={data.category} />
          <span className="text-xs text-gray-500">{data.created_at}</span>
        </div>
        <h2 className="text-xl font-bold text-white">{data.title}</h2>
        <hr className="border-gray-800" />
        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{data.content}</p>
      </div>
    </div>
  )
}

function WriteForm({ onCancel, onSuccess }: { onCancel: () => void; onSuccess: () => void }) {
  const queryClient = useQueryClient()
  const [category, setCategory] = useState<PostCategory>('버그제보')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: createPost,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      onSuccess()
    },
    onError: (err: unknown) => {
      const msg = (err as { message?: string })?.message
      setError(msg || '작성 중 오류가 발생했습니다.')
    },
  })

  const handleSubmit = () => {
    setError('')
    if (!title.trim()) { setError('제목을 입력해주세요.'); return }
    if (!content.trim()) { setError('내용을 입력해주세요.'); return }
    mutation.mutate({ category, title: title.trim(), content: content.trim() })
  }

  return (
    <div className="flex flex-col gap-4">
      <button
        className="self-start text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
        onClick={onCancel}
      >
        ← 취소
      </button>
      <div className="bg-gray-900 rounded-xl p-6 flex flex-col gap-4">
        <h2 className="text-lg font-bold text-white">글 작성</h2>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">카테고리</label>
          <div className="flex gap-2">
            {(['버그제보', '기능제안', '기타'] as PostCategory[]).map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                  category === cat
                    ? CATEGORY_COLORS[cat]
                    : 'bg-gray-800 text-gray-500 border-gray-700 hover:border-gray-500'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">제목 <span className="text-gray-600">({title.length}/100)</span></label>
          <input
            type="text"
            maxLength={100}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="제목을 입력하세요"
            className="bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-400">내용 <span className="text-gray-600">({content.length}/2000)</span></label>
          <textarea
            maxLength={2000}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="내용을 입력하세요"
            rows={8}
            className="bg-gray-800 text-white text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={mutation.isPending}
          className="self-end px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {mutation.isPending ? '등록 중...' : '등록'}
        </button>
      </div>
    </div>
  )
}

type View = { type: 'list' } | { type: 'detail'; id: number } | { type: 'write' }

export default function Board() {
  const navigate = useNavigate()
  const [view, setView] = useState<View>({ type: 'list' })
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['posts', page],
    queryFn: () => fetchPosts(page),
    enabled: view.type === 'list',
  })

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">
      <button
        className="self-start text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
        onClick={() => navigate('/')}
      >
        ← 홈으로
      </button>

      {view.type !== 'list' ? null : (
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">버그제보 / 기능제안</h1>
          <button
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
            onClick={() => setView({ type: 'write' })}
          >
            글 작성
          </button>
        </div>
      )}

      {view.type === 'list' && (
        <>
          {isLoading && (
            <div className="flex justify-center py-16">
              <LoadingSpinner size="md" />
            </div>
          )}

          {data && (
            <>
              {data.posts.length === 0 && (
                <p className="text-center text-gray-500 text-sm py-16">아직 게시글이 없습니다. 첫 번째 글을 작성해보세요!</p>
              )}

              {data.posts.length > 0 && (
                <div className="rounded-xl border border-gray-800 overflow-hidden">
                  {data.posts.map((post: Post) => (
                    <button
                      key={post.id}
                      onClick={() => setView({ type: 'detail', id: post.id })}
                      className="w-full flex items-center gap-4 px-5 py-4 bg-gray-900 hover:bg-gray-800 border-b border-gray-800 last:border-0 text-left transition-colors"
                    >
                      <CategoryBadge category={post.category} />
                      <span className="flex-1 text-white text-sm font-medium truncate">{post.title}</span>
                      <span className="text-xs text-gray-500 shrink-0">{post.created_at}</span>
                    </button>
                  ))}
                </div>
              )}

              {totalPages > 1 && (
                <div className="flex justify-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 text-gray-300 text-sm rounded-lg transition-colors"
                  >
                    이전
                  </button>
                  <span className="px-3 py-1.5 text-gray-400 text-sm">{page} / {totalPages}</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 text-gray-300 text-sm rounded-lg transition-colors"
                  >
                    다음
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}

      {view.type === 'detail' && (
        <PostDetail postId={view.id} onBack={() => setView({ type: 'list' })} />
      )}

      {view.type === 'write' && (
        <WriteForm
          onCancel={() => setView({ type: 'list' })}
          onSuccess={() => { setPage(1); setView({ type: 'list' }) }}
        />
      )}
    </div>
  )
}
