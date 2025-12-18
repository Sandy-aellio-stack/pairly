import { useState } from 'react';
import { Search, Filter, User, Settings, Shield, Ban, CheckCircle, Eye, Download } from 'lucide-react';

const mockLogs = [
  { id: 1, admin: 'Admin1', action: 'User Banned', target: 'user_123', details: 'Reason: Harassment', timestamp: '2024-01-15 14:30:22', type: 'ban' },
  { id: 2, admin: 'Admin2', action: 'Content Removed', target: 'photo_456', details: 'Inappropriate image', timestamp: '2024-01-15 14:25:10', type: 'moderation' },
  { id: 3, admin: 'Admin1', action: 'Settings Changed', target: 'search_radius', details: 'Changed from 50km to 100km', timestamp: '2024-01-15 13:45:00', type: 'settings' },
  { id: 4, admin: 'Admin3', action: 'User Verified', target: 'user_789', details: 'Manual verification completed', timestamp: '2024-01-15 12:30:15', type: 'verification' },
  { id: 5, admin: 'Admin2', action: 'User Suspended', target: 'user_012', details: 'Reason: Fake profile', timestamp: '2024-01-15 11:20:45', type: 'suspension' },
  { id: 6, admin: 'Admin1', action: 'Report Reviewed', target: 'report_345', details: 'Content approved - no action', timestamp: '2024-01-15 10:15:30', type: 'moderation' },
  { id: 7, admin: 'Admin3', action: 'User Reactivated', target: 'user_678', details: 'Appeal approved', timestamp: '2024-01-15 09:45:00', type: 'reactivation' },
  { id: 8, admin: 'Admin2', action: 'Credits Adjusted', target: 'user_901', details: 'Added 50 bonus credits', timestamp: '2024-01-14 16:30:00', type: 'credits' },
  { id: 9, admin: 'Admin1', action: 'Settings Changed', target: 'signup_bonus', details: 'Changed from 5 to 10 coins', timestamp: '2024-01-14 15:20:00', type: 'settings' },
  { id: 10, admin: 'Admin3', action: 'Content Removed', target: 'message_234', details: 'Spam content', timestamp: '2024-01-14 14:10:00', type: 'moderation' },
];

const AdminLogPage = () => {
  const [logs, setLogs] = useState(mockLogs);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.admin.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.target.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'all' || log.type === typeFilter;
    return matchesSearch && matchesType;
  });

  const getActionIcon = (type) => {
    switch (type) {
      case 'ban': return <Ban size={16} className="text-red-500" />;
      case 'suspension': return <Ban size={16} className="text-yellow-500" />;
      case 'moderation': return <Shield size={16} className="text-blue-500" />;
      case 'settings': return <Settings size={16} className="text-purple-500" />;
      case 'verification': return <CheckCircle size={16} className="text-green-500" />;
      case 'reactivation': return <CheckCircle size={16} className="text-green-500" />;
      default: return <Eye size={16} className="text-gray-500" />;
    }
  };

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'Admin', 'Action', 'Target', 'Details'].join(','),
      ...filteredLogs.map(log => 
        [log.timestamp, log.admin, log.action, log.target, log.details].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'admin_logs.csv';
    a.click();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Admin Activity Log</h1>
          <p className="text-gray-600">Track all administrative actions for auditing.</p>
        </div>
        <button
          onClick={exportLogs}
          className="px-4 py-2 bg-white border border-gray-200 rounded-xl font-medium text-[#0F172A] hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <Download size={18} />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {['all', 'ban', 'suspension', 'moderation', 'settings', 'verification'].map((type) => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                  typeFilter === type
                    ? 'bg-[#0F172A] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Logs List */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="divide-y divide-gray-100">
          {filteredLogs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500">No logs found matching your criteria.</p>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div key={log.id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    {getActionIcon(log.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium text-[#0F172A]">{log.action}</p>
                        <p className="text-sm text-gray-500">
                          Target: <span className="font-mono text-xs bg-gray-100 px-1 rounded">{log.target}</span>
                        </p>
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{log.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{log.details}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="w-5 h-5 bg-[#E9D5FF] rounded-full flex items-center justify-center">
                        <User size={12} className="text-[#0F172A]" />
                      </div>
                      <span className="text-xs text-gray-500">by {log.admin}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminLogPage;
