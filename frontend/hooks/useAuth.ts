import { useState, useEffect } from 'react';

interface User {
  id: number;
  email: string;
  username: string;
  role: 'USER' | 'DEVELOPER' | 'ADMIN';
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get token from localStorage
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse user data:', e);
      }
    }
    setLoading(false);
  }, []);

  return {
    user,
    token,
    loading,
    isAuthenticated: !!user && !!token,
  };
};

