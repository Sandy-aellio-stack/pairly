import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Send, MoreVertical, Phone, Video, ArrowLeft, Image, Smile, Coins, Loader2, X } from 'lucide-react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import { messagesAPI, userAPI } from '@/services/api';
import { connectSocket, getSocket, joinChat, onNewMessage, offNewMessage, onIncomingCall, offIncomingCall, sendTyping, sendStopTyping } from '@/services/socket';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { userId: urlUserId } = useParams();
  const { user, refreshCredits } = useAuthStore();
  const [conversations, setConversations] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [incomingCall, setIncomingCall] = useState(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  const selectedChatRef = useRef(null);

  selectedChatRef.current = selectedChat;

  // Connect socket and set up listeners
  useEffect(() => {
    const token = localStorage.getItem('tb_access_token');
    if (token) {
      connectSocket(token);
    }

    const handleNewMessage = (data) => {
      const current = selectedChatRef.current;
      if (
        current &&
        (data.sender_id === current.id || data.receiver_id === current.id)
      ) {
        setMessages((prev) => {
          const exists = prev.some((m) => m.id === data.id);
          if (exists) return prev;
          return [
            ...prev,
            {
              id: data.id,
              sender_id: data.sender_id,
              content: data.content,
              created_at: data.created_at,
            },
          ];
        });
      }

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === data.sender_id) {
            return { ...c, lastMessage: data.content, unread: (c.unread || 0) + 1 };
          }
          return c;
        })
      );
    };

    const handleIncomingCall = (data) => {
      setIncomingCall(data);
    };

    onNewMessage(handleNewMessage);
    onIncomingCall(handleIncomingCall);

    return () => {
      offNewMessage(handleNewMessage);
      offIncomingCall(handleIncomingCall);
    };
  }, []);

  // Handle ?user=userId or /chat/:userId to start new conversation
  useEffect(() => {
    const targetUserId = urlUserId || searchParams.get('user');
    if (targetUserId) {
      if (selectedChat?.id === targetUserId) return;

      const existingConv = conversations.find(c => (c.id || c.user_id) === targetUserId);
      if (existingConv) {
        setSelectedChat(existingConv);
        return;
      }

      const startNewChat = async () => {
        try {
          const response = await messagesAPI.startConversation(targetUserId);
          const targetUser = response.data.user;
          const newChat = {
            id: targetUserId,
            name: targetUser.name,
            avatar: targetUser.profile_picture,
            online: targetUser.is_online,
          };
          setSelectedChat(newChat);
        } catch (error) {
          console.error('Failed to load user for chat:', error);
          toast.error('Could not start conversation with this user');
        }
      };
      startNewChat();
    }
  }, [urlUserId, searchParams, conversations, selectedChat]);

  // Join socket chat room when a chat is selected
  useEffect(() => {
    if (selectedChat?.id) {
      const socket = getSocket();
      if (socket?.connected) {
        joinChat(selectedChat.id).catch(() => {});
      }
    }
  }, [selectedChat?.id]);

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
        const formattedConvs = response.data.conversations.map(conv => ({
          ...conv,
          id: conv.user?.id || conv.user_id,
          name: conv.user?.name || conv.name,
          avatar: conv.user?.profile_picture || conv.avatar,
          online: conv.user?.is_online || conv.online,
        }));
        setConversations(formattedConvs);
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
    if (!userId) return;
    setLoadingMessages(true);
    try {
      const response = await messagesAPI.getMessages(userId);
      if (response.data.messages) {
        setMessages(response.data.messages);
        await messagesAPI.markRead(userId);
      }
    } catch (error) {
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const selectedConversation = conversations.find(c => (c.id || c.user?.id) === selectedChat?.id) || selectedChat;

  const handleTyping = useCallback(() => {
    if (selectedChat?.id) {
      sendTyping(selectedChat.id);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        sendStopTyping(selectedChat.id);
      }, 2000);
    }
  }, [selectedChat?.id]);

  const handleSend = async () => {
    if (!message.trim() || !selectedChat) return;

    if ((user?.credits_balance || 0) < 1) {
      toast.error('You need coins to send messages! Buy more coins.');
      navigate('/dashboard/credits');
      return;
    }

    setIsSending(true);
    const messageText = message;
    setMessage('');

    const tempId = `temp_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    const tempMessage = {
      id: tempId,
      sender_id: user?.id,
      content: messageText,
      created_at: new Date().toISOString(),
      _temp: true,
    };
    setMessages(prev => [...prev, tempMessage]);

    try {
      const result = await messagesAPI.send(selectedChat.id, messageText);
      setMessages(prev =>
        prev.map(m => m.id === tempId ? { ...m, id: result.data?.message_id || tempId, _temp: false } : m)
      );
      refreshCredits();
    } catch (error) {
      if (error.response?.status === 402) {
        toast.error('Insufficient coins! Buy more to continue chatting.');
        navigate('/dashboard/credits');
        setMessages(prev => prev.filter(m => m.id !== tempId));
      } else {
        toast.error('Failed to send message');
        setMessages(prev => prev.filter(m => m.id !== tempId));
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleAcceptCall = () => {
    if (incomingCall) {
      navigate(`/call/${incomingCall.caller_id}?type=${incomingCall.call_type || 'audio'}&call_id=${incomingCall.call_id}&incoming=true`);
      setIncomingCall(null);
    }
  };

  const handleRejectCall = () => {
    if (incomingCall) {
      const socket = getSocket();
      if (socket?.connected) {
        socket.emit('reject_call', { call_id: incomingCall.call_id, reason: 'rejected' });
      }
      setIncomingCall(null);
    }
  };

  const filteredConversations = conversations.filter(conv =>
    conv.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4">
      {/* Incoming Call Modal */}
      {incomingCall && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-80 text-center shadow-2xl">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Phone size={28} className="text-green-600 animate-pulse" />
            </div>
            <h3 className="text-lg font-bold text-[#0F172A] mb-1">Incoming Call</h3>
            <p className="text-gray-500 text-sm mb-6">
              {incomingCall.call_type === 'video' ? 'Video' : 'Voice'} call from user
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleRejectCall}
                className="flex-1 py-3 bg-red-100 text-red-600 rounded-xl font-semibold hover:bg-red-200 transition-colors flex items-center justify-center gap-2"
              >
                <X size={18} />
                Decline
              </button>
              <button
                onClick={handleAcceptCall}
                className="flex-1 py-3 bg-green-500 text-white rounded-xl font-semibold hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
              >
                <Phone size={18} />
                Accept
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow-lg overflow-hidden h-[calc(100vh-180px)] flex">
        {/* Conversations List */}
        <div className={`w-full md:w-80 border-r border-gray-100 flex flex-col ${
          selectedChat ? 'hidden md:flex' : 'flex'
        }`}>
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
                  key={conv.id || conv.user_id}
                  onClick={() => {
                    setSelectedChat(conv);
                    navigate(`/dashboard/chat/${conv.id || conv.user_id}`, { replace: true });
                  }}
                  className={`w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors ${
                    selectedChat?.id === (conv.id || conv.user_id) ? 'bg-[#E9D5FF]/20' : ''
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
        <div className={`flex-1 flex flex-col ${selectedChat ? 'flex' : 'hidden md:flex'}`}>
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
                  <div
                    className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
                    onClick={() => navigate(`/dashboard/profile/${selectedChat.id}`)}
                  >
                    <img
                      src={selectedConversation.avatar || selectedConversation.profile_pictures?.[0] || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'}
                      alt={selectedConversation.name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                    <div>
                      <h3 className="font-semibold text-[#0F172A]">{selectedConversation.name}</h3>
                      <p className="text-xs text-green-500">
                        {isTyping ? 'Typing...' : selectedConversation.online ? 'Online' : 'Tap to view profile'}
                      </p>
                    </div>
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
                    {messages.map((msg) => {
                      const isMine = msg.sender === 'me' || msg.sender_id === user?.id;
                      return (
                        <div key={msg.id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                          <div
                            className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                              isMine
                                ? `bg-[#0F172A] text-white rounded-br-md ${msg._temp ? 'opacity-70' : ''}`
                                : 'bg-white shadow-sm rounded-bl-md'
                            }`}
                          >
                            <p className="text-sm">{msg.text || msg.content}</p>
                            <p className={`text-xs mt-1 ${isMine ? 'text-white/60' : 'text-gray-400'}`}>
                              {msg.time || (msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '')}
                            </p>
                          </div>
                        </div>
                      );
                    })}
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
                    onChange={(e) => {
                      setMessage(e.target.value);
                      handleTyping();
                    }}
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
