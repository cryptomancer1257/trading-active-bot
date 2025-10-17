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

    // Debug logging
    console.log('useAuth debug:', {
      storedToken: storedToken ? `${storedToken.substring(0, 20)}...` : null,
      storedUser: storedUser ? 'exists' : null,
      localStorageKeys: Object.keys(localStorage)
    });

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

  // Debug logging
  console.log('useAuth return:', {
    user: user ? { id: user.id, email: user.email, role: user.role } : null,
    token: token ? `${token.substring(0, 20)}...` : null,
    loading,
    isAuthenticated: !!user && !!token,
  });

  return {
    user,
    token,
    loading,
    isAuthenticated: !!user && !!token,
  };
};

