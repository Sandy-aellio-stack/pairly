import { useState, useEffect } from 'react';
import { Search, Eye, UserX, Ban, CheckCircle, XCircle, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { adminUsersAPI } from '@/services/adminApi';

const UserManagementPage = () => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchUsers();
  }, [currentPage, statusFilter]);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const params = { page: currentPage, limit: 20 };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;
      
      const response = await adminUsersAPI.list(params);
      setUsers(response.data.users);
      setTotalPages(response.data.pages);
      setTotal(response.data.total);
    } catch (error) {
      toast.error('Failed to fetch users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchUsers();
  };

  const handleSuspend = async (userId) => {
    try {
      await adminUsersAPI.suspend(userId);
      toast.success('User suspended');
      fetchUsers();
    } catch (error) {
      toast.error('Failed to suspend user');
    }
  };

  const handleReactivate = async (userId) => {
    try {
      await adminUsersAPI.reactivate(userId);
      toast.success('User reactivated');
      fetchUsers();
    } catch (error) {
      toast.error('Failed to reactivate user');
    }
  };

  const handleBan = async (userId) => {
    if (window.confirm('Are you sure you want to ban this user? This action is severe.')) {
      handleSuspend(userId); // Use suspend for now
    }
  };

  const viewUser = async (user) => {
    try {
      const response = await adminUsersAPI.get(user.id);
      setSelectedUser(response.data);
      setShowUserModal(true);
    } catch (error) {
      toast.error('Failed to fetch user details');
    }
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
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
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
            {['all', 'active', 'suspended'].map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => { setStatusFilter(status); setCurrentPage(1); }}
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
        </form>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-md overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-gray-400" />
          </div>
        ) : (
          <>
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
                  {users.map((user) => (
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
                          {user.status !== 'banned' && user.status === 'active' && (
                            <button
                              onClick={() => handleBan(user.id)}
                              className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                              title="Ban"
                            >
                              <Ban size={18} className="text-red-600" />
                            </button>
                          )}
                          {user.status === 'suspended' && (
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
              <p className="text-sm text-gray-500">Showing {users.length} of {total} users</p>
              <div className="flex gap-2">
                <button 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                >
                  <ChevronLeft size={18} />
                </button>
                <span className="px-3 py-2 text-sm">Page {currentPage} of {totalPages}</span>
                <button 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* User Detail Modal */}
      {showUserModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-[#E9D5FF] flex items-center justify-center font-bold text-2xl text-[#0F172A]">
                {selectedUser.user.name[0]}
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#0F172A]">{selectedUser.user.name}</h3>
                <p className="text-gray-500">{selectedUser.user.email}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Age</p>
                <p className="font-semibold text-[#0F172A]">{selectedUser.user.age}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Gender</p>
                <p className="font-semibold text-[#0F172A] capitalize">{selectedUser.user.gender}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Credits</p>
                <p className="font-semibold text-[#0F172A]">{selectedUser.user.credits}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500">Status</p>
                {getStatusBadge(selectedUser.user.status)}
              </div>
            </div>

            {/* Recent Transactions */}
            {selectedUser.transactions?.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-[#0F172A] mb-3">Recent Transactions</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {selectedUser.transactions.map((t, i) => (
                    <div key={i} className="flex justify-between text-sm p-2 bg-gray-50 rounded-lg">
                      <span className="text-gray-600">{t.description}</span>
                      <span className={t.amount > 0 ? 'text-green-600' : 'text-red-600'}>
                        {t.amount > 0 ? '+' : ''}{t.amount}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setShowUserModal(false)}
                className="flex-1 py-3 bg-gray-100 text-[#0F172A] rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;
