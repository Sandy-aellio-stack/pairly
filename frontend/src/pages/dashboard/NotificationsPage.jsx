import { useState, useEffect } from 'react';
import { Heart, MapPin, MessageCircle, UserPlus, Eye, Clock, Bell, Sparkles, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { notificationsAPI } from '@/services/api';
import { toast } from 'sonner';

const NotificationsPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('all');
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    setIsLoading(true);
    try {
      const response = await notificationsAPI.getAll(false, 50);
      if (response.data.notifications && response.data.notifications.length > 0) {
        const mappedNotifications = response.data.notifications.map(n => ({
          id: n.id,
          type: mapNotificationType(n.type),
          user: {
            name: n.title || 'Someone',
            age: n.user_age || null,
            photo: n.user_photo || null,
            distance: n.user_distance || null
          },
          message: n.body,
          time: formatTime(n.createdAt),
          isNew: !n.isRead
        }));
        setNotifications(mappedNotifications);
      } else {
        setNotifications([]);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setNotifications([]);
    } finally {
      setIsLoading(false);
    }
  };

  const mapNotificationType = (type) => {
    const typeMap = { match: 'match', message: 'message', credit: 'credit', system: 'system' };
    return typeMap[type] || 'like';
  };


  const formatTime = (isoString) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 60) return `${diffMins} minutes ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    return `${Math.floor(diffHours / 24)} days ago`;
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllAsRead();
      setNotifications(notifications.map(n => ({ ...n, isNew: false })));
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark notifications as read');
    }
  };

  const tabs = [
    { id: 'all', label: 'All', icon: Bell },
    { id: 'likes', label: 'Likes', icon: Heart },
    { id: 'nearby', label: 'Nearby', icon: MapPin },
    { id: 'matches', label: 'Matches', icon: Sparkles },
  ];

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'like':
        return <Heart size={16} className="text-rose-500" fill="currentColor" />;
      case 'superlike':
        return <Sparkles size={16} className="text-blue-500" />;
      case 'nearby':
        return <MapPin size={16} className="text-green-500" />;
      case 'match':
        return <Users size={16} className="text-purple-500" />;
      case 'view':
        return <Eye size={16} className="text-gray-500" />;
      case 'message':
        return <MessageCircle size={16} className="text-blue-500" />;
      default:
        return <Bell size={16} className="text-gray-500" />;
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (activeTab === 'all') return true;
    if (activeTab === 'likes') return n.type === 'like' || n.type === 'superlike';
    if (activeTab === 'nearby') return n.type === 'nearby';
    if (activeTab === 'matches') return n.type === 'match';
    return true;
  });

  const newCount = notifications.filter(n => n.isNew).length;

  const handleNotificationClick = (notification) => {
    if (notification.type === 'match' || notification.type === 'message') {
      navigate('/dashboard/chat');
    } else if (notification.type === 'nearby') {
      navigate('/dashboard/nearby');
    } else {
      navigate('/dashboard/nearby');
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-[#0F172A]">Notifications</h1>
              <p className="text-sm text-gray-500 mt-1">
                {newCount > 0 ? `${newCount} new notifications` : 'No new notifications'}
              </p>
            </div>
            {newCount > 0 && (
              <button 
                onClick={handleMarkAllRead}
                className="text-sm text-[#0F172A] font-medium hover:underline"
              >
                Mark all as read
              </button>
            )}
          </div>

          <div className="flex gap-2 overflow-x-auto pb-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  activeTab === tab.id
                    ? 'bg-[#0F172A] text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="divide-y divide-gray-100">
          {isLoading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-[#0F172A] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Loading notifications...</p>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="p-8 text-center">
              <Bell size={40} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No notifications yet</p>
              <p className="text-gray-400 text-sm mt-1">When someone likes you or is nearby, you'll see it here</p>
            </div>
          ) : (
            filteredNotifications.map(notification => (
              <div
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                className={`flex items-center gap-4 p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                  notification.isNew ? 'bg-[#E9D5FF]/10' : ''
                }`}
              >
                <div className="relative">
                  {notification.user.photo ? (
                    <img
                      src={notification.user.photo}
                      alt={notification.user.name}
                      className="w-14 h-14 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-14 h-14 rounded-full bg-[#E9D5FF] flex items-center justify-center">
                      <Users size={24} className="text-[#0F172A]" />
                    </div>
                  )}
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-white shadow flex items-center justify-center">
                    {getNotificationIcon(notification.type)}
                  </div>
                  {notification.isNew && (
                    <div className="absolute -top-1 -left-1 w-3 h-3 bg-rose-500 rounded-full border-2 border-white" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#0F172A]">
                    <span className="font-semibold">
                      {notification.user.name}{notification.user.age ? `, ${notification.user.age}` : ''}
                    </span>
                    {' '}{notification.message}
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    {notification.user.distance && (
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <MapPin size={12} />
                        {notification.user.distance}
                      </span>
                    )}
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock size={12} />
                      {notification.time}
                    </span>
                  </div>
                </div>

                {(notification.type === 'like' || notification.type === 'superlike') && (
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate('/dashboard/chat');
                    }}
                    className="px-4 py-2 bg-[#0F172A] text-white text-sm font-medium rounded-full hover:bg-gray-800 transition-colors"
                  >
                    Like Back
                  </button>
                )}

                {notification.type === 'match' && (
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate('/dashboard/chat');
                    }}
                    className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium rounded-full hover:opacity-90 transition-colors"
                  >
                    Message
                  </button>
                )}

                {notification.type === 'nearby' && (
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate('/dashboard/nearby');
                    }}
                    className="px-4 py-2 border border-gray-200 text-[#0F172A] text-sm font-medium rounded-full hover:bg-gray-50 transition-colors"
                  >
                    View
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        {filteredNotifications.length > 0 && (
          <div className="p-4 border-t border-gray-100 text-center">
            <p className="text-xs text-gray-400">
              Showing {filteredNotifications.length} notifications
            </p>
          </div>
        )}
      </div>

      <div className="mt-6 bg-gradient-to-r from-[#E9D5FF] to-[#FCE7F3] rounded-2xl p-6 text-center">
        <Sparkles className="w-8 h-8 text-[#0F172A] mx-auto mb-3" />
        <h3 className="font-bold text-[#0F172A] mb-2">Get More Matches</h3>
        <p className="text-sm text-gray-600 mb-4">
          Upgrade to see who liked you first and get priority in nearby searches
        </p>
        <button 
          onClick={() => navigate('/dashboard/credits')}
          className="px-6 py-2 bg-[#0F172A] text-white font-medium rounded-full hover:bg-gray-800 transition-colors"
        >
          Get Premium
        </button>
      </div>
    </div>
  );
};

export default NotificationsPage;
