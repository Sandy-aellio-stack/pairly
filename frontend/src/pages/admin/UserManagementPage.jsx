import { useState } from 'react';
import { Search, Filter, MoreVertical, Edit, Ban, Eye, UserX, CheckCircle, XCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const mockUsers = [
  { id: '1', name: 'Priya Sharma', email: 'priya@example.com', age: 26, gender: 'female', status: 'active', verified: true, joinedDate: '2024-01-15', credits: 150 },
  { id: '2', name: 'Rahul Kumar', email: 'rahul@example.com', age: 28, gender: 'male', status: 'active', verified: true, joinedDate: '2024-01-14', credits: 75 },
  { id: '3', name: 'Ananya Mehta', email: 'ananya@example.com', age: 24, gender: 'female', status: 'suspended', verified: false, joinedDate: '2024-01-13', credits: 0 },
  { id: '4', name: 'Arjun Patel', email: 'arjun@example.com', age: 30, gender: 'male', status: 'active', verified: true, joinedDate: '2024-01-12', credits: 200 },
  { id: '5', name: 'Sneha Das', email: 'sneha@example.com', age: 27, gender: 'female', status: 'banned', verified: false, joinedDate: '2024-01-11', credits: 10 },
  { id: '6', name: 'Vikram Singh', email: 'vikram@example.com', age: 29, gender: 'male', status: 'active', verified: true, joinedDate: '2024-01-10', credits: 500 },
  { id: '7', name: 'Kavita Reddy', email: 'kavita@example.com', age: 25, gender: 'female', status: 'active', verified: false, joinedDate: '2024-01-09', credits: 25 },
  { id: '8', name: 'Amit Shah', email: 'amit@example.com', age: 31, gender: 'male', status: 'active', verified: true, joinedDate: '2024-01-08', credits: 350 },
];

const UserManagementPage = () => {
  const [users, setUsers] = useState(mockUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleSuspend = (userId) => {
    setUsers(users.map(u => u.id === userId ? { ...u, status: 'suspended' } : u));
    toast.success('User suspended');
  };

  const handleBan = (userId) => {
    if (window.confirm('Are you sure you want to ban this user? This action is severe.')) {
      setUsers(users.map(u => u.id === userId ? { ...u, status: 'banned' } : u));
      toast.success('User banned');
    }
  };

  const handleReactivate = (userId) => {
    setUsers(users.map(u => u.id === userId ? { ...u, status: 'active' } : u));
    toast.success('User reactivated');
  };

  const viewUser = (user) => {
    setSelectedUser(user);
    setShowUserModal(true);
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-green-100 text-green-700',
      suspended: 'bg-yellow-100 text-yellow-700',
      banned: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.active}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#0F172A] mb-2">User Management</h1>
        <p className="text-gray-600">Search, view, and manage all TrueBond users.</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 focus:border-[#0F172A] outline-none"
            />
          </div>
          <div className="flex gap-2">
            {['all', 'active', 'suspended', 'banned'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  statusFilter === status
                    ? 'bg-[#0F172A] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">User</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Status</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Verified</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Credits</th>
                <th className="text-left py-4 px-6 text-sm font-semibold text-[#0F172A]">Joined</th>
                <th className="text-right py-4 px-6 text-sm font-semibold text-[#0F172A]">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#E9D5FF] flex items-center justify-center font-bold text-[#0F172A]">
                        {user.name[0]}
                      </div>
                      <div>
                        <p className="font-medium text-[#0F172A]">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">{getStatusBadge(user.status)}</td>
                  <td className="py-4 px-6">
                    {user.verified ? (
                      <CheckCircle size={20} className="text-green-500" />
                    ) : (
                      <XCircle size={20} className="text-gray-300" />
                    )}
                  </td>
                  <td className="py-4 px-6">
                    <span className="font-medium text-[#0F172A]">{user.credits}</span>
                  </td>
                  <td className="py-4 px-6 text-gray-500 text-sm">{user.joinedDate}</td>
                  <td className="py-4 px-6">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => viewUser(user)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <Eye size={18} className="text-gray-600" />
                      </button>
                      {user.status === 'active' && (
                        <button
                          onClick={() => handleSuspend(user.id)}
                          className="p-2 hover:bg-yellow-100 rounded-lg transition-colors"
                          title="Suspend"
                        >
                          <UserX size={18} className="text-yellow-600" />
                        </button>
                      )}
                      {user.status !== 'banned' && (
                        <button
                          onClick={() => handleBan(user.id)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                          title="Ban"
                        >
                          <Ban size={18} className="text-red-600" />
                        </button>
                      )}
                      {(user.status === 'suspended' || user.status === 'banned') && (
                        <button
                          onClick={() => handleReactivate(user.id)}
                          className="p-2 hover:bg-green-100 rounded-lg transition-colors"
                          title="Reactivate"
                        >
                          <CheckCircle size={18} className="text-green-600" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
          <p className="text-sm text-gray-500">Showing {filteredUsers.length} of {users.length} users</p>
          <div className="flex gap-2">
            <button className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50" disabled>
              <ChevronLeft size={18} />
            </button>
            <button className="px-3 py-1 bg-[#0F172A] text-white rounded-lg text-sm">1</button>
            <button className="px-3 py-1 hover:bg-gray-100 rounded-lg text-sm">2</button>
            <button className="px-3 py-1 hover:bg-gray-100 rounded-lg text-sm">3</button>
            <button className="p-2 hover:bg-gray-100 rounded-lg">
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* User Detail Modal */}
      {showUserModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-[#E9D5FF] flex items-center justify-center font-bold text-2xl text-[#0F172A]">
                {selectedUser.name[0]}
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#0F172A]">{selectedUser.name}</h3>
                <p className="text-gray-500">{selectedUser.email}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Age</p>
                <p className="font-semibold text-[#0F172A]">{selectedUser.age}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Gender</p>
                <p className="font-semibold text-[#0F172A] capitalize">{selectedUser.gender}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Credits</p>
                <p className="font-semibold text-[#0F172A]">{selectedUser.credits}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Status</p>
                {getStatusBadge(selectedUser.status)}
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowUserModal(false)}
                className="flex-1 py-3 bg-gray-100 text-[#0F172A] rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
              <button className="flex-1 py-3 bg-[#0F172A] text-white rounded-xl font-medium hover:bg-gray-800 transition-colors">
                Edit User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;
