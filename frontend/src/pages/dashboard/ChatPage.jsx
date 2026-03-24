import { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Send, MoreVertical, Phone, Video, ArrowLeft, Image, Smile, Coins, Loader2, X, CheckCircle } from 'lucide-react';
import { useNavigate, useSearchParams, useParams } from 'react-router-dom';
import api from '../../services/api';
import { messagesAPI, userAPI } from '../../services/api';
import { connectSocket, getSocket, joinChat, onNewMessage, offNewMessage, onIncomingCall, offIncomingCall, sendTyping, sendStopTyping } from '../../services/socket';
import useAuthStore from '../../store/authStore';
import { toast } from 'sonner';

const ChatPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { conversationId } = useParams();
  const { user, refreshUser } = useAuthStore();

  const currentUserId = user?._id || user?.id || user?.user_id;

  console.log("[CHAT INIT] component mounted");
  console.log("[CHAT INIT] currentUserId:", currentUserId);
  
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
      const currentUser = useAuthStore.getState().user;
      const current = selectedChatRef.current;

      if (
        current &&
        (data.sender_id === current.id || data.receiver_id === current.id)
      ) {
        if (data.sender_id === currentUser?.id) {
          // Own message: resolve any matching temp message to the real ID
          setMessages((prev) => {
            const alreadyReal = prev.some((m) => m.id === data.id && !m._temp);
            if (alreadyReal) return prev;
            const hasTemp = prev.some((m) => m._temp);
            if (hasTemp) {
              return prev.map((m) =>
                m._temp && m.content === data.content
                  ? { ...m, id: data.id, _temp: false }
                  : m
              );
            }
            return prev;
          });
        } else {
          // Incoming message from the other person
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
      }

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === data.sender_id && data.sender_id !== currentUser?.id) {
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

  // Handle route hydration and direct chat startup
  useEffect(() => {
    const queryUserId = searchParams.get('userId');
    const queryUserName = searchParams.get('user');
    
    console.log('[INIT DEBUG] Hydration effect triggered:', { 
      conversationId, 
      queryUserId, 
      queryUserName, 
      conversationsCount: conversations.length,
      isLoading 
    });

    // If skip logic if still loading initial conversations
    if (isLoading) return;

    // 1. Try to find existing conversation in the sidebar list
    let existingConv = null;
    
    if (conversationId) {
      existingConv = conversations.find(c => 
        c.id === conversationId || 
        c.user_id === conversationId ||
        c._id === conversationId ||
        c.conversation_id === conversationId
      );
      if (existingConv) console.log('[INIT DEBUG] Found conversation by route conversationId:', conversationId);
    }
    
    if (!existingConv && queryUserId) {
      existingConv = conversations.find(c => 
        c.id === queryUserId || 
        c.user_id === queryUserId
      );
      if (existingConv) console.log('[INIT DEBUG] Found conversation by query userId:', queryUserId);
    }

    if (existingConv) {
      if (selectedChat?.id !== (existingConv.id || existingConv.user_id)) {
        console.log('[INIT DEBUG] Selecting existing conversation:', existingConv.id);
        setSelectedChat(existingConv);
      }
      return;
    }

    // 2. If no existing conversation found but we have a target userId, start/placeholder it
    if (queryUserId) {
      if (selectedChat?.id === queryUserId) return;
      
      console.log('[INIT DEBUG] Creating placeholder chat for userId:', queryUserId);

      const startNewChat = async () => {
        try {
          // Attempt to get real metadata from server
          console.log('[INIT DEBUG] Calling startConversation for:', queryUserId);
          const response = await messagesAPI.startConversation(queryUserId);
          const targetUser = response.data.user;
          const newChat = {
            id: queryUserId,
            name: targetUser.name || queryUserName || 'User',
            avatar: targetUser.profile_picture,
            online: targetUser.is_online,
            conversation_id: response.data.conversation_id
          };
          console.log('[INIT DEBUG] startConversation success:', newChat);
          setSelectedChat(newChat);
        } catch (error) {
          console.error('[INIT DEBUG] Failed to load user for chat:', error);
          
          // If we have a name from query, show a lightweight UI instead of failing
          if (queryUserName) {
            console.log('[INIT DEBUG] Using fallback lightweight chat state');
            setSelectedChat({
              id: queryUserId,
              name: queryUserName,
              avatar: null,
              online: false,
            });
          } else {
            // Only toast if we literally have no way to show who we're talking to
            toast.error('Could not start conversation with this user');
          }
        }
      };
      startNewChat();
    }
  }, [conversationId, searchParams, conversations, isLoading, selectedChat?.id]);

  // Join socket chat room when a chat is selected
  useEffect(() => {
    if (selectedChat?.id) {
      const socket = getSocket();
      if (socket?.connected) {
        joinChat(selectedChat.id).catch(() => {});
      }
    }
  }, [selectedChat?.id]);

  // Step 1: Exact normalization helper per 1121
  const normalizeConversations = (res) => {
    const payload = res?.data ?? res;
    if (Array.isArray(payload)) return payload;
    if (Array.isArray(payload?.conversations)) return payload.conversations;
    if (Array.isArray(payload?.data?.conversations)) return payload.data.conversations;
    return [];
  };

  const fetchConversations = useCallback(async () => {
    if (!currentUserId) {
      console.log("[CHAT INIT] no currentUserId, skip fetch");
      return;
    }

    try {
      console.log("[CHAT INIT] fetching conversations for:", currentUserId);
      const res = await messagesAPI.getConversations();
      const list =
        res?.data?.conversations ||
        res?.data?.data ||
        res?.data ||
        [];

      console.log("[CHAT INIT] raw response:", res?.data);
      console.log("[CHAT INIT] parsed list:", list);
      console.log("[CHAT INIT] before setConversations count:", list?.length || 0);

      setConversations(Array.isArray(list) ? list : []);
      setIsLoading(false);
    } catch (error) {
      console.error("[CHAT INIT] failed to fetch conversations:", error);
      setConversations([]);
      setIsLoading(false);
    }
  }, [currentUserId]);

  useEffect(() => {
    if (!currentUserId) return;
    console.log("[CHAT INIT] starting fetchConversations");
    fetchConversations();
  }, [currentUserId, fetchConversations]);

  useEffect(() => {
    refreshUser?.();
  }, []);



  // Fetch messages when a chat is selected
  // Step 3 & 5: fetchMessages only when chat is selected
  useEffect(() => {
    if (selectedChat) {
      console.log('[MSG PAGE DEBUG] Fetching messages for:', selectedChat.id);
      fetchMessages(selectedChat.id);
    }
  }, [selectedChat]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);


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

    if ((user?.coins || 0) < 1) {
      toast.error('You need coins to send messages! Buy more coins.');
      navigate('/dashboard/credits');
      return;
    }

    setIsSending(true);
    const messageText = message;
    setMessage('');

    console.log('[SEND DEBUG] Preparing to send message:', {
      recipientId: selectedChat.id,
      conversationId: selectedChat.conversation_id || selectedChat._id || selectedChat.id,
      textLength: messageText.length
    });

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
      const payload = { 
        receiver_id: selectedChat.id, 
        content: messageText 
      };
      
      // If we have a conversation_id, include it to help the backend
      if (selectedChat.conversation_id || selectedChat._id) {
        payload.conversation_id = selectedChat.conversation_id || selectedChat._id;
      }
      
      console.log('[SEND DEBUG] Calling messagesAPI.send with payload:', payload);
      const result = await messagesAPI.send(payload);
      
      const ack = result.data;
      
      // Step 6: Robust success check to avoid false error toast
      const isSuccess = ack.success === true || !!ack.message_id || !!ack.id;
      
      if (!isSuccess) {
        throw new Error(ack.error || 'Backend reported failure');
      }

      // Step 6: Success path
      setMessages(prev =>
        prev.map(m => m.id === tempId ? { ...m, id: ack.message_id || ack.id || tempId, _temp: false } : m)
      );
      
      // If messages still appear missing in sidebar, refresh list
      fetchConversations();
      
      if (refreshUser) {
        refreshUser();
      }
    } catch (error) {
      console.error('[SEND DEBUG] Send failed:', error.response?.data || error.message);
      if (error.response?.status === 402) {
        toast.error('Insufficient coins! Buy more to continue chatting.');
        navigate('/dashboard/credits');
      } else {
        toast.error('Failed to send message');
      }
      setMessages(prev => prev.filter(m => m.id !== tempId));
    } finally {
      setIsSending(false);
    }
  };

  const handleImageSend = async (file) => {
    if (!selectedChat || (user?.coins || 0) < 1) {
      toast.error('You need coins to send images!');
      navigate('/dashboard/credits');
      return;
    }

    setIsSending(true);
    const formData = new FormData();
    formData.append('image', file);
    formData.append('receiver_id', selectedChat.id);

    try {
      const response = await messagesAPI.uploadImage(formData);
      
      const tempId = `temp_image_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      const tempMessage = {
        id: tempId,
        sender_id: user?.id,
        image_url: URL.createObjectURL(file),
        created_at: new Date().toISOString(),
        _temp: true,
      };
      setMessages(prev => [...prev, tempMessage]);
      
      if (refreshUser) {
        refreshUser();
      }
    } catch (error) {
      toast.error('Failed to send image');
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

  // Step 2 & 7: Derived state and deduplication
  const safeConversations = Array.isArray(conversations) ? conversations : [];
  
  // Step 7: Robust dedupe by conversation_id or user id
  const dedupedConversations = Object.values(
    safeConversations.reduce((acc, conv) => {
      const key = conv?.id || conv?.user_id || conv?.conversation_id || conv?._id || Math.random().toString();
      const prev = acc[key];
      if (!prev) acc[key] = conv;
      else {
        // Keep latest
        const prevTime = new Date(prev?.last_message_at || prev?.updated_at || 0).getTime();
        const nextTime = new Date(conv?.last_message_at || conv?.updated_at || 0).getTime();
        acc[key] = nextTime >= prevTime ? conv : prev;
      }
      return acc;
    }, {})
  ).sort((a, b) => {
    const timeA = new Date(a.last_message_at || a.updated_at || 0).getTime();
    const timeB = new Date(b.last_message_at || b.updated_at || 0).getTime();
    return timeB - timeA;
  });

  const filteredConversations = dedupedConversations.filter((conv) => {
    const q = (searchQuery || "").toLowerCase();
    const name =
      conv?.user?.name?.toLowerCase?.() ||
      conv?.name?.toLowerCase?.() ||
      "";
    return !q || name.includes(q);
  });

  const selectedConversation = safeConversations.find(c => (c.id || c.user?.id) === selectedChat?.id) || selectedChat;

  // Step 3: Handler aliases
  const sendMessage = handleSend;
  const toggleEmoji = () => {
    toast.info('Emoji picker coming soon!');
  }; 
  const openImageUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) handleImageSend(file);
    };
    input.click();
  };

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
                      if ((user?.coins || 0) < 5) {
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
                      if ((user?.coins || 0) < 10) {
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
                      const isSeen = msg.status === 'seen';
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
                            <div className="flex items-center gap-1 mt-1">
                              <p className={`text-xs ${isMine ? 'text-white/60' : 'text-gray-400'}`}>
                                {msg.time || (msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '')}
                              </p>
                              {isMine && (
                                <CheckCircle 
                                  size={12}
                                  className={`ml-1 ${isSeen ? 'text-pink-400' : 'text-white/60'}`}
                                />
                              )}
                            </div>
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
                  <button 
                    onClick={openImageUpload}
                    className="p-2 hover:bg-gray-100 rounded-full"
                  >
                    <Image size={20} className="text-gray-500" />
                  </button>
                  <button 
                    onClick={toggleEmoji}
                    className="p-2 hover:bg-gray-100 rounded-full"
                  >
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
