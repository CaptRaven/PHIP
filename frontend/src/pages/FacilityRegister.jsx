import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Building2, MapPin } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function FacilityRegister() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    facility_type: 'PHC',
    state: 'Kano',
    lga: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Map facility_type to type for backend
      const payload = {
        ...formData,
        type: formData.facility_type
      };
      await axios.post(`${API_BASE}/auth/register`, payload);
      navigate('/facility/login');
    } catch (err) {
      console.error(err);
      let errorMsg = 'Registration failed.';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          errorMsg = detail.map(e => e.msg).join(', ');
        } else {
          errorMsg = detail;
        }
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-lg border border-gray-100">
        <div className="flex flex-col items-center mb-6">
          <div className="p-3 bg-green-100 rounded-full mb-3">
            <Building2 className="text-green-600" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Register Facility</h1>
          <p className="text-gray-500 text-sm">Join the network to track outbreaks</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Facility Name</label>
              <input
                type="text"
                name="name"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
                value={formData.name}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                name="facility_type"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
                value={formData.facility_type}
                onChange={handleChange}
              >
                <option value="PHC">PHC</option>
                <option value="Hospital">Hospital</option>
                <option value="Clinic">Clinic</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input
                type="text"
                name="state"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
                value={formData.state}
                onChange={handleChange}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">LGA</label>
              <input
                type="text"
                name="lga"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
                value={formData.lga}
                onChange={handleChange}
              />
            </div>
          </div>

          <hr className="my-2 border-gray-100" />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text"
              name="username"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
              value={formData.username}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-green-500"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 rounded transition-colors disabled:opacity-70"
          >
            {loading ? 'Registering...' : 'Create Account'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          Already registered?{' '}
          <Link to="/facility/login" className="text-green-600 hover:underline font-medium">
            Login here
          </Link>
        </div>
      </div>
    </div>
  );
}
