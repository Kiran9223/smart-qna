import { useAuth } from "../hooks/useAuth.js";
import { usePosts } from "../hooks/usePosts.js";
import RoleBadge from "../components/RoleBadge.jsx";

export default function Profile() {
  const { user, role } = useAuth();
  const { data } = usePosts({ author_id: user?.user_id, size: 10 });

  if (!user) return null;

  const displayName = user.display_name || user.email || "User";
  const initial = displayName[0].toUpperCase();

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card p-8 mb-6">
        <div className="flex items-center gap-6">
          <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-white text-3xl font-bold shadow-md">
            {initial}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{displayName}</h1>
            <p className="text-gray-500 mt-0.5">{user.email}</p>
            <div className="mt-2">
              <RoleBadge role={role} />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-8 pt-6 border-t border-gray-100">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{data?.total ?? "–"}</div>
            <div className="text-sm text-gray-500 mt-0.5">Questions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">–</div>
            <div className="text-sm text-gray-500 mt-0.5">Answers</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">–</div>
            <div className="text-sm text-gray-500 mt-0.5">Votes received</div>
          </div>
        </div>
      </div>

      <h2 className="text-lg font-bold text-gray-900 mb-3">Recent Questions</h2>
      {data?.items?.length === 0 ? (
        <div className="card p-6 text-center text-gray-500">
          You haven't asked any questions yet.
        </div>
      ) : (
        <div className="space-y-2">
          {data?.items?.map((post) => (
            <div key={post.post_id} className="card p-4">
              <a
                href={`/posts/${post.post_id}`}
                className="font-medium text-gray-900 hover:text-blue-600 transition-colors"
              >
                {post.title}
              </a>
              <div className="text-xs text-gray-500 mt-1">
                {post.answer_count} answers · {post.vote_count} votes
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
