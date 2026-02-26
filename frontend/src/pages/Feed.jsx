import { useState } from "react";
import { Link, useSearchParams, useParams } from "react-router-dom";
import { usePosts } from "../hooks/usePosts.js";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api.js";
import PostCard from "../components/PostCard.jsx";
import Pagination from "../components/Pagination.jsx";
import { useAuth } from "../hooks/useAuth.js";

const SORT_TABS = [
  { key: "latest", label: "Latest" },
  { key: "unanswered", label: "Unanswered" },
  { key: "popular", label: "Popular" },
];

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="card p-5 animate-pulse">
          <div className="flex gap-4">
            <div className="hidden sm:flex flex-col gap-2 w-16">
              <div className="h-4 bg-gray-200 rounded" />
              <div className="h-8 bg-gray-200 rounded" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="h-5 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="flex gap-2">
                <div className="h-5 w-16 bg-gray-200 rounded-full" />
                <div className="h-5 w-16 bg-gray-200 rounded-full" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Feed() {
  const { tagName } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  const sort = searchParams.get("sort") || "latest";
  const search = searchParams.get("search") || undefined;
  const page = parseInt(searchParams.get("page") || "1");

  const { data, isLoading, isError } = usePosts({
    sort,
    tag: tagName,
    search,
    page,
    size: 20,
  });

  const { data: tags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: () => api.get("/tags").then((r) => r.data),
  });

  const setSort = (s) => {
    const params = new URLSearchParams(searchParams);
    params.set("sort", s);
    params.delete("page");
    setSearchParams(params);
  };

  const setPage = (p) => {
    const params = new URLSearchParams(searchParams);
    params.set("page", String(p));
    setSearchParams(params);
    window.scrollTo(0, 0);
  };

  return (
    <div className="flex gap-6">
      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-gray-900">
            {tagName ? `Questions tagged: ${tagName}` : search ? `Results for "${search}"` : "All Questions"}
          </h1>
          {user && (
            <Link to="/posts/new" className="btn-primary">
              Ask Question
            </Link>
          )}
        </div>

        {/* Sort tabs */}
        {!tagName && !search && (
          <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit">
            {SORT_TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setSort(tab.key)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  sort === tab.key
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {isLoading ? (
          <LoadingSkeleton />
        ) : isError ? (
          <div className="card p-8 text-center text-gray-500">
            <p className="text-lg">Failed to load questions.</p>
            <p className="text-sm mt-1">Please try refreshing the page.</p>
          </div>
        ) : data?.items?.length === 0 ? (
          <div className="card p-12 text-center">
            <p className="text-4xl mb-3">🤔</p>
            <p className="text-lg font-medium text-gray-700">No questions found</p>
            <p className="text-sm text-gray-500 mt-1">
              {user ? "Be the first to ask one!" : "Sign in to ask the first question."}
            </p>
            {user && <Link to="/posts/new" className="btn-primary mt-4 inline-flex">Ask a Question</Link>}
          </div>
        ) : (
          <>
            <div className="text-sm text-gray-500 mb-3">{data?.total} questions</div>
            <div className="space-y-3">
              {data?.items?.map((post) => <PostCard key={post.post_id} post={post} />)}
            </div>
            <Pagination page={data?.page} pages={data?.pages} onPageChange={setPage} />
          </>
        )}
      </div>

      {/* Sidebar */}
      <aside className="hidden lg:block w-56 shrink-0">
        <div className="card p-4 sticky top-20">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Popular Tags</h2>
          <div className="flex flex-wrap gap-1.5">
            {tags.slice(0, 15).map((tag) => (
              <Link
                key={tag.tag_id}
                to={`/tags/${tag.name}`}
                className="badge bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
              >
                {tag.name}
                <span className="ml-1 text-blue-600">×{tag.post_count}</span>
              </Link>
            ))}
          </div>
          <Link to="/tags" className="block mt-3 text-xs text-blue-600 hover:underline">
            View all tags →
          </Link>
        </div>
      </aside>
    </div>
  );
}
