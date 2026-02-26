import { Link } from "react-router-dom";

export default function TagBadge({ tag }) {
  return (
    <Link
      to={`/tags/${tag.name}`}
      className="badge bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
    >
      {tag.name}
    </Link>
  );
}
