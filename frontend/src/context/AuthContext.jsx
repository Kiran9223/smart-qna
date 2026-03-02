import { createContext, useContext, useState, useEffect } from "react";
import { getCurrentSession, signOut, getRole, getUserInfo } from "../services/cognito.js";
import api from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCurrentSession().then(async (sess) => {
      if (sess) {
        setSession(sess);
        setRole(getRole(sess));
        try {
          const userInfo = getUserInfo(sess);
          if (userInfo?.email) {
            await api.patch("/auth/me", userInfo).catch(() => {});
          }
          const res = await api.get("/auth/me");
          setUser(res.data);
        } catch {
          setUser(null);
        }
      }
      setLoading(false);
    });
  }, []);

  const login = async (sess) => {
    setSession(sess);
    setRole(getRole(sess));
    // Sync real email/name from ID Token to backend DB
    const userInfo = getUserInfo(sess);
    if (userInfo?.email) {
      await api.patch("/auth/me", userInfo).catch(() => {});
    }
    const res = await api.get("/auth/me");
    setUser(res.data);
  };

  const logout = () => {
    signOut();
    setSession(null);
    setUser(null);
    setRole(null);
  };

  return (
    <AuthContext.Provider value={{ session, user, role, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
