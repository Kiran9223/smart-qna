import { useAuth } from "../hooks/useAuth.js";
import { useNavigate } from "react-router-dom";

export default function VoteButton({ count, userVote, onUpvote, onDownvote, disabled }) {
  const { user } = useAuth();
  const navigate = useNavigate();

  const requireAuth = (fn) => () => {
    if (!user) { navigate("/login"); return; }
    fn();
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={requireAuth(onUpvote)}
        disabled={disabled}
        className={`p-1.5 rounded-full transition-colors ${
          userVote === "UP"
            ? "text-blue-600 bg-blue-100"
            : "text-gray-400 hover:text-blue-600 hover:bg-blue-50"
        }`}
        aria-label="Upvote"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z" />
        </svg>
      </button>

      <span className={`text-sm font-bold ${
        count > 0 ? "text-blue-600" : count < 0 ? "text-red-600" : "text-gray-500"
      }`}>
        {count}
      </span>

      <button
        onClick={requireAuth(onDownvote)}
        disabled={disabled}
        className={`p-1.5 rounded-full transition-colors ${
          userVote === "DOWN"
            ? "text-red-600 bg-red-100"
            : "text-gray-400 hover:text-red-600 hover:bg-red-50"
        }`}
        aria-label="Downvote"
      >
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z" />
        </svg>
      </button>
    </div>
  );
}
