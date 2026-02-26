import { Link } from "react-router-dom";
import { formatDistanceToNow } from "date-fns";
import TagBadge from "./TagBadge.jsx";

const STATUS_COLORS = {
  OPEN: "bg-green-100 text-green-800",
  SOLVED: "bg-blue-100 text-blue-800",
  CLOSED: "bg-gray-100 text-gray-600",
};

export default function PostCard({ post }) {
  return (
    <div className={`card p-5 hover:shadow-md transition-shadow ${post.is_pinned ? "border-l-4 border-l-blue-500" : ""}`}>
      <div className="flex gap-4">
        {/* Stats */}
        <div className="hidden sm:flex flex-col items-center gap-3 min-w-[64px] text-center">
          <div className="text-sm">
            <div className="font-bold text-gray-800">{post.vote_count}</div>
            <div className="text-gray-500 text-xs">votes</div>
          </div>
          <div className={`text-sm rounded-md px-2 py-1 ${
            post.answer_count > 0 ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
          }`}>
            <div className="font-bold">{post.answer_count}</div>
            <div className="text-xs">answers</div>
          </div>
          <div className="text-xs text-gray-400">{post.view_count} views</div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2 mb-2">
            {post.is_pinned && (
              <span className="badge bg-blue-100 text-blue-700 shrink-0">📌 Pinned</span>
            )}
            <span className={`badge shrink-0 ${STATUS_COLORS[post.status] || STATUS_COLORS.OPEN}`}>
              {post.status}
            </span>
          </div>

          <Link
            to={`/posts/${post.post_id}`}
            className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors line-clamp-2"
          >
            {post.title}
          </Link>

          <div className="flex flex-wrap gap-1.5 mt-2 mb-3">
            {post.tags?.map((tag) => <TagBadge key={tag.tag_id} tag={tag} />)}
          </div>

          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
                {post.author?.display_name[0]?.toUpperCase()}
              </div>
              <span className="font-medium text-gray-700">{post.author?.display_name}</span>
            </div>
            <span>{formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
