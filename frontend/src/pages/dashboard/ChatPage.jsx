import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send, Coins, AlertCircle } from 'lucide-react';
import { messagesAPI, userAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';

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
      console.log('Failed to load conversations');
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
      
      // Mark as read
      await messagesAPI.markRead(userId);
    } catch (e) {
      console.log('Failed to load chat');
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
      console.log('Failed to send message:', e.response?.data?.detail);
    } finally {
      setSending(false);
    }
  };

  // Conversations list view
  if (!userId) {
    return (
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Messages</h1>

        {loading ? (
          <div className="text-center py-10 text-white/60">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-20 card-dark">
            <p className="text-white/60 mb-4">No conversations yet</p>
            <Link to="/dashboard/nearby" className="text-purple-400 hover:underline">
              Find people nearby to start chatting
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {conversations.map((conv) => (
              <Link
                key={conv.conversation_id}
                to={`/dashboard/chat/${conv.user.id}`}
                className="card-dark flex items-center gap-4 py-4 hover:border-purple-500/30 transition-colors"
              >
                <div className="relative">
                  <div className="w-14 h-14 rounded-full bg-purple-500/20 flex items-center justify-center overflow-hidden">
                    {conv.user.profile_picture ? (
                      <img src={conv.user.profile_picture} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-xl font-bold text-purple-400">{conv.user.name?.[0]}</span>
                    )}
                  </div>
                  {conv.user.is_online && (
                    <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 rounded-full border-2 border-[#0B0B0F]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold">{conv.user.name}</h3>
                    {conv.unread_count > 0 && (
                      <span className="bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-white/40 text-sm truncate">{conv.last_message}</p>
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
    <div className="h-[calc(100vh-200px)] lg:h-[calc(100vh-100px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-4 pb-4 border-b border-white/10">
        <Link to="/dashboard/chat" className="text-white/60 hover:text-white">
          <ArrowLeft size={24} />
        </Link>
        {otherUser && (
          <>
            <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center overflow-hidden">
              {otherUser.profile_pictures?.[0] ? (
                <img src={otherUser.profile_pictures[0]} alt="" className="w-full h-full object-cover" />
              ) : (
                <span className="text-lg font-bold text-purple-400">{otherUser.name?.[0]}</span>
              )}
            </div>
            <div>
              <h2 className="font-semibold">{otherUser.name}</h2>
              <p className="text-white/40 text-sm">{otherUser.is_online ? 'Online' : 'Offline'}</p>
            </div>
          </>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {loading ? (
          <div className="text-center py-10 text-white/60">Loading messages...</div>
        ) : messages.length === 0 ? (
          <div className="text-center py-10 text-white/60">
            <p>No messages yet</p>
            <p className="text-sm">Send the first message! (1 coin)</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.is_mine ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                  msg.is_mine
                    ? 'bg-purple-500 text-white rounded-br-sm'
                    : 'bg-white/10 text-white rounded-bl-sm'
                }`}
              >
                <p>{msg.content}</p>
                <p className={`text-xs mt-1 ${msg.is_mine ? 'text-white/60' : 'text-white/40'}`}>
                  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="pt-4 border-t border-white/10">
        {credits < 1 ? (
          <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
            <AlertCircle size={20} className="text-red-400" />
            <p className="text-red-400 text-sm flex-1">You need coins to send messages</p>
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
              className="input-dark flex-1"
              disabled={sending}
            />
            <button
              type="submit"
              disabled={!newMessage.trim() || sending}
              className="btn-primary px-6 flex items-center gap-2 disabled:opacity-50"
            >
              <Send size={18} />
              <span className="hidden sm:inline">Send</span>
              <span className="text-xs opacity-60">(1🪙)</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
