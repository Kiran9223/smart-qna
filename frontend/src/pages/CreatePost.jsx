import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useCreatePost } from "../hooks/usePosts.js";
import api from "../services/api.js";
import toast from "react-hot-toast";

export default function CreatePost() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", body: "", tag_ids: [] });
  const { mutate, isPending } = useCreatePost();

  const { data: tags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: () => api.get("/tags").then((r) => r.data),
  });

  const toggleTag = (tagId) => {
    setForm((f) => ({
      ...f,
      tag_ids: f.tag_ids.includes(tagId)
        ? f.tag_ids.filter((id) => id !== tagId)
        : [...f.tag_ids, tagId],
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim() || !form.body.trim()) return;
    mutate(form, {
      onSuccess: (post) => {
        toast.success("Question posted!");
        navigate(`/posts/${post.post_id}`);
      },
      onError: (err) => toast.error(err.response?.data?.detail || "Failed to post question"),
    });
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Ask a Question</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="card p-5">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Title
            <span className="font-normal text-gray-500 ml-1">— Be specific and clear</span>
          </label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="input"
            placeholder="e.g. How do I configure Docker networking for my FastAPI app?"
            maxLength={300}
            required
          />
          <p className="text-xs text-gray-400 mt-1">{form.title.length}/300</p>
        </div>

        <div className="card p-5">
          <label className="block text-sm font-semibold text-gray-700 mb-1">
            Body
            <span className="font-normal text-gray-500 ml-1">— Describe your problem in detail</span>
          </label>
          <textarea
            value={form.body}
            onChange={(e) => setForm({ ...form, body: e.target.value })}
            rows={10}
            className="input resize-none"
            placeholder="Include what you've tried, error messages, and relevant code..."
            required
          />
        </div>

        <div className="card p-5">
          <label className="block text-sm font-semibold text-gray-700 mb-3">Tags</label>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <button
                key={tag.tag_id}
                type="button"
                onClick={() => toggleTag(tag.tag_id)}
                className={`badge cursor-pointer transition-colors ${
                  form.tag_ids.includes(tag.tag_id)
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {tag.name}
              </button>
            ))}
          </div>
          {form.tag_ids.length > 0 && (
            <p className="text-xs text-gray-500 mt-2">{form.tag_ids.length} tag(s) selected</p>
          )}
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={isPending} className="btn-primary">
            {isPending ? "Posting..." : "Post Your Question"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
