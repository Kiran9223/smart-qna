import { useState } from "react";
import toast from "react-hot-toast";
import { useSubmitAnswer } from "../hooks/usePosts.js";

export default function AnswerForm({ postId }) {
  const [body, setBody] = useState("");
  const { mutate, isPending } = useSubmitAnswer();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!body.trim()) return;
    mutate(
      { postId, body: body.trim() },
      {
        onSuccess: () => {
          setBody("");
          toast.success("Answer posted!");
        },
        onError: (err) => toast.error(err.response?.data?.detail || "Failed to post answer"),
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="card p-5 mt-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Answer</h3>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={6}
        placeholder="Write a detailed answer..."
        className="input resize-none mb-3"
        required
      />
      <button type="submit" disabled={isPending || !body.trim()} className="btn-primary">
        {isPending ? "Posting..." : "Post Your Answer"}
      </button>
    </form>
  );
}
