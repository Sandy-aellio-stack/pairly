import { useState } from 'react';
import { FileText, Calendar, User, Shield, Settings, Loader2 } from 'lucide-react';

// Sample log data - in production this would come from an API
const sampleLogs = [
  { id: 1, action: 'User Suspended', admin: 'admin@truebond.com', target: 'User123', timestamp: '2024-12-18 15:30:22', severity: 'warning' },
  { id: 2, action: 'Settings Updated', admin: 'admin@truebond.com', target: 'Message Cost: 1 → 2', timestamp: '2024-12-18 14:22:10', severity: 'info' },
  { id: 3, action: 'Content Removed', admin: 'moderator@truebond.com', target: 'Report #1234', timestamp: '2024-12-18 12:45:33', severity: 'warning' },
  { id: 4, action: 'User Reactivated', admin: 'admin@truebond.com', target: 'User456', timestamp: '2024-12-18 11:20:55', severity: 'info' },
  { id: 5, action: 'User Banned', admin: 'admin@truebond.com', target: 'User789', timestamp: '2024-12-18 10:15:42', severity: 'critical' },
  { id: 6, action: 'Admin Login', admin: 'admin@truebond.com', target: '-', timestamp: '2024-12-18 09:00:00', severity: 'info' },
  { id: 7, action: 'Credits Adjusted', admin: 'admin@truebond.com', target: 'User321: +100 coins', timestamp: '2024-12-17 16:30:15', severity: 'info' },
  { id: 8, action: 'Report Approved', admin: 'moderator@truebond.com', target: 'Report #1230', timestamp: '2024-12-17 14:45:22', severity: 'info' },
];

const AdminLogPage = () => {
  const [logs] = useState(sampleLogs);
  const [filter, setFilter] = useState('all');

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    return log.severity === filter;
  });

  const getSeverityBadge = (severity) => {
    const styles = {
      info: 'bg-blue-100 text-blue-700',
      warning: 'bg-yellow-100 text-yellow-700',
      critical: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[severity] || styles.info}`}>
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  const getActionIcon = (action) => {
    if (action.includes('Login')) return <User size={16} className="text-blue-500" />;
    if (action.includes('Settings')) return <Settings size={16} className="text-purple-500" />;
    if (action.includes('Suspended') || action.includes('Banned')) return <Shield size={16} className="text-red-500" />;
    return <FileText size={16} className="text-gray-500" />;
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">Admin Activity Log</h1>
        <p className="text-gray-600">Track all administrative actions and changes.</p>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {['all', 'info', 'warning', 'critical'].map((f) => (
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

      {/* Logs Table */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Action</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Admin</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Target</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Severity</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      {getActionIcon(log.action)}
                      <span className="font-medium text-[#0F172A]">{log.action}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-gray-600">{log.admin}</td>
                  <td className="py-4 px-6 text-gray-600">{log.target}</td>
                  <td className="py-4 px-6">{getSeverityBadge(log.severity)}</td>
                  <td className="py-4 px-6 text-gray-500 text-sm">
                    <div className="flex items-center gap-2">
                      <Calendar size={14} />
                      {log.timestamp}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Note about static data */}
        <div className="px-6 py-4 border-t border-gray-100 bg-gray-50">
          <p className="text-sm text-gray-500">
            ℹ️ Admin logs shown are sample data. Connect to a real logging system for production use.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminLogPage;
