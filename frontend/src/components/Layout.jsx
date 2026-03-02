import { Outlet, Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";
import NotificationBell from "./NotificationBell.jsx";
import SearchBar from "./SearchBar.jsx";

export default function Layout() {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            <Link to="/" className="flex items-center gap-2 shrink-0">
              <span className="text-2xl">💡</span>
              <span className="font-bold text-xl text-blue-600 hidden sm:block">Smart Q&amp;A</span>
            </Link>

            <div className="flex-1 max-w-xl">
              <SearchBar />
            </div>

            <nav className="flex items-center gap-2 shrink-0">
              {user ? (
                <>
                  <Link to="/posts/new" className="btn-primary hidden sm:inline-flex">
                    Ask Question
                  </Link>
                  <NotificationBell />
                  <div className="relative group">
                    <button className="flex items-center gap-2 rounded-full p-1 hover:bg-gray-100 transition-colors">
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                        {(user.display_name || user.email || "U")[0].toUpperCase()}
                      </div>
                    </button>
                    <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                      <div className="px-4 py-2 text-sm text-gray-500 border-b border-gray-100">
                        <p className="font-medium text-gray-900 truncate">{user.display_name || user.email}</p>
                        <p className="truncate">{user.email}</p>
                      </div>
                      <Link to="/profile" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                        Profile
                      </Link>
                      {role === "ADMIN" && (
                        <Link to="/admin/users" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          Admin Panel
                        </Link>
                      )}
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50"
                      >
                        Sign out
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn-secondary">Sign in</Link>
                  <Link to="/register" className="btn-primary">Sign up</Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-gray-200 py-4 text-center text-sm text-gray-500">
        Smart Q&amp;A — Course Discussion Platform
      </footer>
    </div>
  );
}
