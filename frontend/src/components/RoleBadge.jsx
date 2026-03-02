const STYLES = {
  ADMIN: "bg-red-100 text-red-700 border-red-200",
  TA: "bg-blue-100 text-blue-700 border-blue-200",
  STUDENT: "bg-gray-100 text-gray-600 border-gray-200",
};

export default function RoleBadge({ role }) {
  if (!role) return null;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${STYLES[role] ?? STYLES.STUDENT}`}>
      {role}
    </span>
  );
}
