import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api.js";

export default function TagDirectory() {
  const { data: tags = [], isLoading } = useQuery({
    queryKey: ["tags"],
    queryFn: () => api.get("/tags").then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 animate-pulse">
        {[...Array(12)].map((_, i) => (
          <div key={i} className="card p-4 h-20 bg-gray-200 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">All Tags</h1>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {tags.map((tag) => (
          <Link
            key={tag.tag_id}
            to={`/tags/${tag.name}`}
            className="card p-4 hover:shadow-md transition-shadow"
          >
            <div className="badge bg-blue-100 text-blue-800 mb-2">{tag.name}</div>
            <p className="text-xs text-gray-500">{tag.post_count} questions</p>
            {tag.description && (
              <p className="text-xs text-gray-600 mt-1 line-clamp-2">{tag.description}</p>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
