import { useState, useEffect } from 'react';
import { Phone, Video, Clock, Calendar, Coins, User, Loader2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const CallHistoryPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [calls, setCalls] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, audio, video, missed

  useEffect(() => {
    fetchCallHistory();
  }, [filter]);

  const fetchCallHistory = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/calls/history', {
        params: { limit: 50, filter }
      });
      
      if (response.data.calls) {
        setCalls(response.data.calls);
      }
    } catch (error) {
      toast.error('Failed to load call history');
      setCalls([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ', ' + 
             date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50';
      case 'missed': return 'text-red-600 bg-red-50';
      case 'rejected': return 'text-orange-600 bg-orange-50';
      case 'failed': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status, type, initiatedBy) => {
    if (status === 'missed' && initiatedBy !== user?.id) {
      return <Phone size={16} className="text-red-500" />;
    }
    return type === 'video' ? <Video size={16} /> : <Phone size={16} />;
  };

  const filteredCalls = calls.filter(call => {
    if (filter === 'all') return true;
    if (filter === 'missed') return call.status === 'missed';
    return call.call_type === filter;
  });

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/dashboard/chat')}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-600" />
              </button>
              <h1 className="text-xl font-semibold text-[#0F172A]">Call History</h1>
            </div>
            
            {/* Filter Tabs */}
            <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
              {['all', 'audio', 'video', 'missed'].map((filterType) => (
                <button
                  key={filterType}
                  onClick={() => setFilter(filterType)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    filter === filterType
                      ? 'bg-white text-[#0F172A] shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {filterType.charAt(0).toUpperCase() + filterType.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-[#0F172A]" />
          </div>
        ) : filteredCalls.length === 0 ? (
          <div className="text-center py-12">
            <Phone size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No calls found</h3>
            <p className="text-gray-500">
              {filter === 'all' 
                ? "You haven't made any calls yet" 
                : `No ${filter} calls found`}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredCalls.map((call) => {
              const isOutgoing = call.caller_id === user?.id;
              const otherUser = isOutgoing ? call.receiver : call.caller;
              
              return (
                <div
                  key={call.id}
                  className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* User Avatar */}
                      <div className="relative">
                        <img
                          src={otherUser?.profile_picture || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'}
                          alt={otherUser?.name || 'User'}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                        <div className={`absolute -bottom-1 -right-1 p-1 rounded-full bg-white border-2 border-white ${getStatusColor(call.status)}`}>
                          {getStatusIcon(call.status, call.call_type, call.caller_id)}
                        </div>
                      </div>

                      {/* Call Info */}
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-[#0F172A]">
                            {otherUser?.name || 'Unknown User'}
                          </h3>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(call.status)}`}>
                            {call.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                          <span className="flex items-center gap-1">
                            {isOutgoing ? (
                              <>
                                <Phone size={14} className="text-green-500" />
                                Outgoing
                              </>
                            ) : (
                              <>
                                <Phone size={14} className="text-blue-500" />
                                Incoming
                              </>
                            )}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {call.duration_seconds > 0 ? formatDuration(call.duration_seconds) : 'No duration'}
                          </span>
                          {call.credits_spent > 0 && (
                            <span className="flex items-center gap-1">
                              <Coins size={14} className="text-yellow-500" />
                              {call.credits_spent} coins
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Time and Actions */}
                    <div className="text-right">
                      <div className="text-sm text-gray-500">
                        {formatDate(call.created_at)}
                      </div>
                      {otherUser?.id && (
                        <button
                          onClick={() => navigate(`/call/${otherUser.id}?type=${call.call_type || 'audio'}`)}
                          className="mt-2 px-3 py-1 bg-[#0F172A] text-white text-sm rounded-full hover:bg-gray-800 transition-colors"
                        >
                          Call Again
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default CallHistoryPage;
