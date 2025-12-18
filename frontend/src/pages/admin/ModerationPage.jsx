import { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Flag, Image, MessageSquare, User, Clock } from 'lucide-react';
import { toast } from 'sonner';

const mockReports = [
  {
    id: '1',
    type: 'photo',
    reportedUser: 'User123',
    reportedBy: 'User456',
    reason: 'Inappropriate content',
    timestamp: '2024-01-15 10:30',
    content: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200',
    status: 'pending'
  },
  {
    id: '2',
    type: 'profile',
    reportedUser: 'User789',
    reportedBy: 'User012',
    reason: 'Fake profile suspected',
    timestamp: '2024-01-15 09:45',
    content: 'Profile bio contains suspicious links',
    status: 'pending'
  },
  {
    id: '3',
    type: 'message',
    reportedUser: 'User345',
    reportedBy: 'User678',
    reason: 'Harassment',
    timestamp: '2024-01-15 08:20',
    content: 'Reported message content...',
    status: 'pending'
  },
  {
    id: '4',
    type: 'photo',
    reportedUser: 'User901',
    reportedBy: 'User234',
    reason: 'Not a real photo',
    timestamp: '2024-01-14 22:15',
    content: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200',
    status: 'pending'
  },
];

const ModerationPage = () => {
  const [reports, setReports] = useState(mockReports);
  const [filter, setFilter] = useState('all');

  const filteredReports = reports.filter(r => {
    if (filter === 'all') return r.status === 'pending';
    return r.type === filter && r.status === 'pending';
  });

  const handleApprove = (reportId) => {
    setReports(reports.map(r => r.id === reportId ? { ...r, status: 'approved' } : r));
    toast.success('Content approved - no action taken');
  };

  const handleRemove = (reportId) => {
    setReports(reports.map(r => r.id === reportId ? { ...r, status: 'removed' } : r));
    toast.success('Content removed and user warned');
  };

  const handleBanUser = (reportId) => {
    if (window.confirm('Ban this user? This is a severe action.')) {
      setReports(reports.map(r => r.id === reportId ? { ...r, status: 'banned' } : r));
      toast.success('User has been banned');
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
            <span className="text-2xl font-bold text-[#0F172A]">{reports.filter(r => r.status === 'pending').length}</span>
          </div>
          <p className="text-sm text-gray-500">Pending Review</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
              <Image size={20} className="text-blue-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{reports.filter(r => r.type === 'photo' && r.status === 'pending').length}</span>
          </div>
          <p className="text-sm text-gray-500">Photo Reports</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <User size={20} className="text-purple-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{reports.filter(r => r.type === 'profile' && r.status === 'pending').length}</span>
          </div>
          <p className="text-sm text-gray-500">Profile Reports</p>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
              <MessageSquare size={20} className="text-green-600" />
            </div>
            <span className="text-2xl font-bold text-[#0F172A]">{reports.filter(r => r.type === 'message' && r.status === 'pending').length}</span>
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
      <div className="grid md:grid-cols-2 gap-6">
        {filteredReports.length === 0 ? (
          <div className="col-span-2 bg-white rounded-2xl p-12 shadow-md text-center">
            <CheckCircle size={48} className="text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-[#0F172A] mb-2">All caught up!</h3>
            <p className="text-gray-500">No pending reports to review.</p>
          </div>
        ) : (
          filteredReports.map((report) => (
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
                {report.type === 'photo' ? (
                  <img
                    src={report.content}
                    alt="Reported content"
                    className="w-full h-48 object-cover rounded-xl mb-4"
                  />
                ) : (
                  <div className="bg-gray-50 rounded-xl p-4 mb-4">
                    <p className="text-gray-700 text-sm">{report.content}</p>
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
                    onClick={() => handleBanUser(report.id)}
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
    </div>
  );
};

export default ModerationPage;
