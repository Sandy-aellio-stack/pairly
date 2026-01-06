import { useState, useEffect, useRef } from 'react';
import { Search, Send, MoreVertical, Phone, Video, ArrowLeft, Image, Smile, Coins, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { messagesAPI } from '@/services/api';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const ChatPage = () => {
  const navigate = useNavigate();
  const { user, refreshCredits } = useAuthStore();
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Fetch messages when a chat is selected
  useEffect(() => {
    if (selectedChat) {
      fetchMessages(selectedChat.id);
    }
  }, [selectedChat]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchConversations = async () => {
    setIsLoading(true);
    try {
      const response = await messagesAPI.getConversations();
      if (response.data.conversations && response.data.conversations.length > 0) {
        setConversations(response.data.conversations);
      } else {
        setConversations([]);
      }
    } catch (error) {
      setConversations([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMessages = async (userId) => {
    setLoadingMessages(true);
    try {
      const response = await messagesAPI.getMessages(userId);
      if (response.data.messages) {
        setMessages(response.data.messages);
        // Mark messages as read
        await messagesAPI.markRead(userId);
      }
    } catch (error) {
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const selectedConversation = conversations.find(c => c.id === selectedChat?.id) || selectedChat;

  const handleSend = async () => {
    if (!message.trim() || !selectedChat) return;

    // Check credits
    if ((user?.credits_balance || 0) < 1) {
      toast.error('You need coins to send messages! Buy more coins.');
      return;
    }

    setIsSending(true);
    const messageText = message;
    setMessage('');

    // Optimistically add message to UI
    const tempMessage = {
      id: Date.now(),
      sender: 'me',
      text: messageText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, tempMessage]);

    try {
      await messagesAPI.send(selectedChat.id, messageText);
      refreshCredits(); // Update credits balance
      toast.success('Message sent! (-1 coin)');
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error('Insufficient coins! Buy more to continue chatting.');
        // Remove optimistic message
        setMessages(prev => prev.filter(m => m.id !== tempMessage.id));
      } else {
        toast.error('Failed to send message');
      }
    } finally {
      setIsSending(false);
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4">
      <div className="bg-white rounded-3xl shadow-lg overflow-hidden h-[calc(100vh-180px)] flex">
        {/* Conversations List */}
        <div className={`w-full md:w-80 border-r border-gray-100 flex flex-col ${
          selectedChat ? 'hidden md:flex' : 'flex'
        }`}>
          {/* Search */}
          <div className="p-4 border-b border-gray-100">
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-full bg-[#F8FAFC] border border-gray-200 focus:border-[#0F172A] outline-none text-sm"
              />
            </div>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-[#0F172A]" />
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full p-4 text-center">
                <Send size={32} className="text-gray-300 mb-2" />
                <p className="text-gray-500 text-sm">No conversations yet</p>
                <p className="text-gray-400 text-xs">Start chatting with people nearby!</p>
              </div>
            ) : (
              filteredConversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedChat(conv)}
                  className={`w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors ${
                    selectedChat?.id === conv.id ? 'bg-[#E9D5FF]/20' : ''
                  }`}
                >
                  <div className="relative">
                    <img
                      src={conv.avatar || conv.profile_pictures?.[0] || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'}
                      alt={conv.name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                    {conv.online && (
                      <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                    )}
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-[#0F172A]">{conv.name}</h3>
                      <span className="text-xs text-gray-400">{conv.time || ''}</span>
                    </div>
                    <p className="text-sm text-gray-500 truncate">{conv.lastMessage || 'Start a conversation'}</p>
                  </div>
                  {conv.unread > 0 && (
                    <span className="w-5 h-5 bg-rose-500 text-white text-xs rounded-full flex items-center justify-center">
                      {conv.unread}
                    </span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className={`flex-1 flex flex-col ${
          selectedChat ? 'flex' : 'hidden md:flex'
        }`}>
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setSelectedChat(null)}
                    className="md:hidden p-2 hover:bg-gray-100 rounded-full"
                  >
                    <ArrowLeft size={20} />
                  </button>
                  <img
                    src={selectedConversation.avatar || selectedConversation.profile_pictures?.[0] || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'}
                    alt={selectedConversation.name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                  <div>
                    <h3 className="font-semibold text-[#0F172A]">{selectedConversation.name}</h3>
                    <p className="text-xs text-green-500">
                      {selectedConversation.online ? 'Online' : 'Offline'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => {
                      if ((user?.credits_balance || 0) < 5) {
                        toast.error('You need at least 5 coins for a voice call');
                        navigate('/dashboard/credits');
                      } else {
                        navigate(`/call/${selectedChat.id}?type=audio`);
                      }
                    }}
                    className="p-2 hover:bg-gray-100 rounded-full group relative"
                  >
                    <Phone size={20} className="text-gray-600" />
                    <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-[#0F172A] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap">5 coins/min</span>
                  </button>
                  <button 
                    onClick={() => {
                      if ((user?.credits_balance || 0) < 10) {
                        toast.error('You need at least 10 coins for a video call');
                        navigate('/dashboard/credits');
                      } else {
                        navigate(`/call/${selectedChat.id}?type=video`);
                      }
                    }}
                    className="p-2 hover:bg-gray-100 rounded-full group relative"
                  >
                    <Video size={20} className="text-gray-600" />
                    <span className="absolute -bottom-8 left-1/2 -translate-x-1/2 bg-[#0F172A] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap">10 coins/min</span>
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <MoreVertical size={20} className="text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#F8FAFC]">
                {loadingMessages ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 animate-spin text-[#0F172A]" />
                  </div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender === 'me' || msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                            msg.sender === 'me' || msg.sender_id === user?.id
                              ? 'bg-[#0F172A] text-white rounded-br-md'
                              : 'bg-white shadow-sm rounded-bl-md'
                          }`}
                        >
                          <p className="text-sm">{msg.text || msg.content}</p>
                          <p className={`text-xs mt-1 ${
                            msg.sender === 'me' || msg.sender_id === user?.id ? 'text-white/60' : 'text-gray-400'
                          }`}>
                            {msg.time || new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-gray-100 bg-white">
                <div className="flex items-center gap-3">
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <Image size={20} className="text-gray-500" />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <Smile size={20} className="text-gray-500" />
                  </button>
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-3 rounded-full bg-[#F8FAFC] border border-gray-200 focus:border-[#0F172A] outline-none text-sm"
                    onKeyPress={(e) => e.key === 'Enter' && !isSending && handleSend()}
                    disabled={isSending}
                  />
                  <button
                    onClick={handleSend}
                    disabled={isSending || !message.trim()}
                    className="p-3 bg-[#0F172A] text-white rounded-full hover:bg-gray-800 transition-colors disabled:opacity-50"
                  >
                    {isSending ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                  </button>
                </div>
                <p className="text-xs text-gray-400 text-center mt-2 flex items-center justify-center gap-1">
                  <Coins size={12} />
                  1 coin/msg • 5 coins/min audio • 10 coins/min video • You have {user?.credits_balance || 0} coins
                </p>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-[#F8FAFC]">
              <div className="text-center">
                <div className="w-20 h-20 bg-[#E9D5FF]/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Send size={32} className="text-[#0F172A]" />
                </div>
                <h3 className="text-xl font-semibold text-[#0F172A] mb-2">Your Messages</h3>
                <p className="text-gray-500">Select a conversation to start chatting</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
