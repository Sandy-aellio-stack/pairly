import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Flag, Image, MessageSquare, User, Clock, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { adminModerationAPI } from '@/services/adminApi';

const ModerationPage = () => {
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState({ pending: 0, photoReports: 0, profileReports: 0, messageReports: 0 });
  const [filter, setFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [filter]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [reportsRes, statsRes] = await Promise.all([
        adminModerationAPI.listReports({ status: filter === 'all' ? 'pending' : 'pending', report_type: filter !== 'all' ? filter : undefined }),
        adminModerationAPI.getStats()
      ]);
      setReports(reportsRes.data.reports);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch moderation data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (reportId) => {
    try {
      await adminModerationAPI.approveReport(reportId);
      toast.success('Content approved - no action taken');
      fetchData();
    } catch (error) {
      toast.error('Failed to approve');
    }
  };

  const handleRemove = async (reportId) => {
    try {
      await adminModerationAPI.removeContent(reportId);
      toast.success('Content removed and user warned');
      fetchData();
    } catch (error) {
      toast.error('Failed to remove');
    }
  };

  const handleBan = async (reportId) => {
    if (window.confirm('Ban this user? This is a severe action.')) {
      try {
        await adminModerationAPI.banUser(reportId);
        toast.success('User has been banned');
        fetchData();
      } catch (error) {
        toast.error('Failed to ban user');
      }
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'photo': return <Image size={18} className="text-blue-500" />;
      case 'profile': return <User size={18} className="text-purple-500" />;
      case 'message': return <MessageSquare size={18} className="text-green-500" />;
      default: return <Flag size={18} className="text-gray-500" />;
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Content Moderation</h1>
        <p className="text-gray-600">Review and manage reported content.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Clock size={20} className="text-yellow-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{stats.pending}</span>
          </div>
          <p className="text-sm text-gray-500">Pending Review</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Image size={20} className="text-blue-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{stats.photoReports}</span>
          </div>
          <p className="text-sm text-gray-500">Photo Reports</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <User size={20} className="text-purple-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{stats.profileReports}</span>
          </div>
          <p className="text-sm text-gray-500">Profile Reports</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <MessageSquare size={20} className="text-green-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{stats.messageReports}</span>
          </div>
          <p className="text-sm text-gray-500">Message Reports</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {['all', 'photo', 'profile', 'message'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-[#0F172A] text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100 shadow-sm'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Review Queue */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-gray-400" />
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {reports.length === 0 ? (
            <div className="col-span-2 bg-white rounded-2xl p-12 shadow-md text-center">
              <CheckCircle size={48} className="text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-[#0F172A] mb-2">All caught up!</h3>
              <p className="text-gray-500">No pending reports to review.</p>
            </div>
          ) : (
            reports.map((report) => (
              <div key={report.id} className="bg-white rounded-2xl shadow-md overflow-hidden">
                <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getTypeIcon(report.type)}
                    <div>
                      <p className="font-medium text-[#0F172A]">{report.reason}</p>
                      <p className="text-xs text-gray-500">Reported by {report.reportedBy}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">{report.timestamp}</span>
                </div>

                {/* Content Preview */}
                <div className="p-4">
                  {report.type === 'photo' && report.content ? (
                    <img
                      src={report.content}
                      alt="Reported content"
                      className="w-full h-48 object-cover rounded-xl mb-4"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="bg-gray-50 rounded-xl p-4 mb-4">
                      <p className="text-gray-700 text-sm">{report.content || 'No content available'}</p>
                    </div>
                  )}

                  <p className="text-sm text-gray-500 mb-4">
                    <strong>User:</strong> {report.reportedUser}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(report.id)}
                      className="flex-1 py-2 bg-green-100 text-green-700 rounded-xl font-medium hover:bg-green-200 transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckCircle size={18} /> Approve
                    </button>
                    <button
                      onClick={() => handleRemove(report.id)}
                      className="flex-1 py-2 bg-yellow-100 text-yellow-700 rounded-xl font-medium hover:bg-yellow-200 transition-colors flex items-center justify-center gap-2"
                    >
                      <XCircle size={18} /> Remove
                    </button>
                    <button
                      onClick={() => handleBan(report.id)}
                      className="py-2 px-4 bg-red-100 text-red-700 rounded-xl font-medium hover:bg-red-200 transition-colors"
                      title="Ban User"
                    >
                      Ban
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ModerationPage;
