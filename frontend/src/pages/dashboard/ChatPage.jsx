import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send, Coins, AlertCircle, Instagram, MessageSquare, Phone, MoreVertical } from 'lucide-react';
import { messagesAPI, userAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import gsap from 'gsap';

const ChatPage = () => {
  const { userId } = useParams();
  const { user: currentUser, credits, updateCredits, refreshCredits } = useAuthStore();
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [otherUser, setOtherUser] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (userId) {
      loadChat();
    } else {
      loadConversations();
    }
  }, [userId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const response = await messagesAPI.getConversations();
      setConversations(response.data.conversations || []);
    } catch (e) {
      // Mock data
      setConversations([
        { conversation_id: '1', user: { id: '1', name: 'Sarah', is_online: true }, last_message: 'Hey! How are you?', unread_count: 2 },
        { conversation_id: '2', user: { id: '2', name: 'Emma', is_online: false }, last_message: 'That sounds great!', unread_count: 0 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadChat = async () => {
    try {
      const [messagesRes, userRes] = await Promise.all([
        messagesAPI.getMessages(userId),
        userAPI.getProfile(userId),
      ]);
      setMessages(messagesRes.data.messages || []);
      setOtherUser(userRes.data);
      await messagesAPI.markRead(userId);
    } catch (e) {
      // Mock data
      setOtherUser({ id: userId, name: 'Sarah', age: 24, is_online: true, instagram: '@sarah_', snapchat: 'sarah.s' });
      setMessages([
        { id: '1', content: 'Hey there! 👋', is_mine: false, created_at: new Date().toISOString() },
        { id: '2', content: 'Hi! How are you?', is_mine: true, created_at: new Date().toISOString() },
        { id: '3', content: "I'm doing great! Love your profile", is_mine: false, created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending || credits < 1) return;

    setSending(true);
    try {
      await messagesAPI.send(userId, newMessage.trim());
      setNewMessage('');
      updateCredits(-1);
      await loadChat();
    } catch (e) {
      // Mock send
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: newMessage.trim(),
        is_mine: true,
        created_at: new Date().toISOString()
      }]);
      setNewMessage('');
      updateCredits(-1);
    } finally {
      setSending(false);
    }
  };

  // Conversations list view
  if (!userId) {
    return (
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Messages</h1>

        {loading ? (
          <div className="text-center py-10 text-gray-500">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-20 card">
            <MessageSquare size={48} className="text-purple-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No conversations yet</p>
            <Link to="/dashboard/nearby" className="text-purple-600 hover:underline font-medium">
              Find people nearby to start chatting
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {conversations.map((conv) => (
              <Link
                key={conv.conversation_id}
                to={`/dashboard/chat/${conv.user.id}`}
                className="card flex items-center gap-4 py-4 hover:shadow-lg transition-all"
              >
                <div className="relative">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
                    <span className="text-xl font-bold text-white">{conv.user.name?.[0]}</span>
                  </div>
                  {conv.user.is_online && (
                    <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-gray-900">{conv.user.name}</h3>
                    {conv.unread_count > 0 && (
                      <span className="bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-500 text-sm truncate">{conv.last_message}</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Chat view
  return (
    <div className="h-[calc(100vh-200px)] lg:h-[calc(100vh-100px)] flex flex-col max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 pb-4 border-b border-gray-100">
        <Link to="/dashboard/chat" className="text-gray-500 hover:text-gray-700">
          <ArrowLeft size={24} />
        </Link>
        {otherUser && (
          <>
            <div className="relative">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
                <span className="text-lg font-bold text-white">{otherUser.name?.[0]}</span>
              </div>
              {otherUser.is_online && (
                <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
              )}
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-gray-900">{otherUser.name}</h2>
              <p className="text-gray-500 text-sm">{otherUser.is_online ? 'Online' : 'Offline'}</p>
            </div>
            {/* Social Links */}
            <div className="flex items-center gap-2">
              {otherUser.instagram && (
                <a href={`https://instagram.com/${otherUser.instagram.replace('@', '')}`} target="_blank" rel="noopener noreferrer" className="social-icon">
                  <Instagram size={18} />
                </a>
              )}
              {otherUser.snapchat && (
                <div className="social-icon" title={otherUser.snapchat}>
                  <MessageSquare size={18} />
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {loading ? (
          <div className="text-center py-10 text-gray-500">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-gray-500">No messages yet</p>
            <p className="text-sm text-gray-400">Send the first message! (1 coin)</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.is_mine ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] px-4 py-3 ${
                  msg.is_mine
                    ? 'message-mine'
                    : 'message-other'
                }`}
              >
                <p>{msg.content}</p>
                <p className={`text-xs mt-1 ${msg.is_mine ? 'text-white/60' : 'text-gray-400'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="pt-4 border-t border-gray-100">
        {credits < 1 ? (
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
            <AlertCircle size={20} className="text-red-500" />
            <p className="text-red-600 text-sm flex-1">You need coins to send messages</p>
            <Link to="/dashboard/credits" className="btn-primary text-sm py-2 px-4">
              Buy Coins
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSend} className="flex gap-3">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type a message..."
              className="input flex-1"
              disabled={sending}
            />
            <button
              type="submit"
              disabled={!newMessage.trim() || sending}
              className="btn-primary px-6 flex items-center gap-2 disabled:opacity-50"
            >
              <Send size={18} />
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
