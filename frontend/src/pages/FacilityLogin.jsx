import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Building2, Lock, User } from 'lucide-react';
import { API_BASE } from '../config';

export default function FacilityLogin() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const data = new FormData();
    data.append('username', formData.username);
    data.append('password', formData.password);

    try {
      const res = await axios.post(`${API_BASE}/auth/login`, data);
      const { access_token, facility } = res.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('facility', JSON.stringify(facility));
      
      navigate('/facility/dashboard');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md border border-gray-100">
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-blue-100 rounded-full mb-3">
            <Building2 className="text-blue-600" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Facility Portal</h1>
          <p className="text-gray-500 text-sm">Sign in to submit daily reports</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 text-gray-400" size={18} />
              <input
                type="text"
                required
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter facility username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 text-gray-400" size={18} />
              <input
                type="password"
                required
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded transition-colors disabled:opacity-70"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/facility/register" className="text-blue-600 hover:underline font-medium">
            Register Facility
          </Link>
        </div>
      </div>
    </div>
  );
}
