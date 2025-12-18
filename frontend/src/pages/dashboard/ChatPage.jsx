import { useState } from 'react';
import { Search, Send, MoreVertical, Phone, Video, ArrowLeft, Image, Smile, Coins } from 'lucide-react';

const mockConversations = [
  {
    id: '1',
    name: 'Priya',
    lastMessage: 'That sounds great! Would love to meet for coffee ☕',
    time: '2 min ago',
    unread: 2,
    online: true,
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100'
  },
  {
    id: '2',
    name: 'Arjun',
    lastMessage: 'Haha, you have great taste in music!',
    time: '1 hour ago',
    unread: 0,
    online: false,
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100'
  },
  {
    id: '3',
    name: 'Ananya',
    lastMessage: 'Thanks for the book recommendation 📚',
    time: 'Yesterday',
    unread: 0,
    online: true,
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100'
  },
];

const mockMessages = [
  { id: 1, sender: 'them', text: 'Hey! I saw we have similar interests 😊', time: '10:30 AM' },
  { id: 2, sender: 'me', text: 'Hi! Yes, I noticed you love traveling too!', time: '10:32 AM' },
  { id: 3, sender: 'them', text: 'Absolutely! What\'s your favorite destination so far?', time: '10:33 AM' },
  { id: 4, sender: 'me', text: 'I\'d say Ladakh. The mountains are breathtaking! How about you?', time: '10:35 AM' },
  { id: 5, sender: 'them', text: 'That sounds amazing! I\'ve been wanting to go there. I loved my trip to Kerala - the backwaters were so peaceful 🌴', time: '10:38 AM' },
  { id: 6, sender: 'me', text: 'Kerala is on my list! Would love to hear more about it sometime', time: '10:40 AM' },
  { id: 7, sender: 'them', text: 'That sounds great! Would love to meet for coffee ☕', time: '10:42 AM' },
];

const ChatPage = () => {
  const [selectedChat, setSelectedChat] = useState(null);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const selectedConversation = mockConversations.find(c => c.id === selectedChat);

  const handleSend = () => {
    if (!message.trim()) return;
    // TODO: Send message API
    setMessage('');
  };

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
            {mockConversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setSelectedChat(conv.id)}
                className={`w-full flex items-center gap-3 p-4 hover:bg-gray-50 transition-colors ${
                  selectedChat === conv.id ? 'bg-[#E9D5FF]/20' : ''
                }`}
              >
                <div className="relative">
                  <img
                    src={conv.avatar}
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
                    <span className="text-xs text-gray-400">{conv.time}</span>
                  </div>
                  <p className="text-sm text-gray-500 truncate">{conv.lastMessage}</p>
                </div>
                {conv.unread > 0 && (
                  <span className="w-5 h-5 bg-rose-500 text-white text-xs rounded-full flex items-center justify-center">
                    {conv.unread}
                  </span>
                )}
              </button>
            ))}
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
                    src={selectedConversation.avatar}
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
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <Phone size={20} className="text-gray-600" />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <Video size={20} className="text-gray-600" />
                  </button>
                  <button className="p-2 hover:bg-gray-100 rounded-full">
                    <MoreVertical size={20} className="text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#F8FAFC]">
                {mockMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.sender === 'me' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] px-4 py-3 rounded-2xl ${
                        msg.sender === 'me'
                          ? 'bg-[#0F172A] text-white rounded-br-md'
                          : 'bg-white shadow-sm rounded-bl-md'
                      }`}
                    >
                      <p className="text-sm">{msg.text}</p>
                      <p className={`text-xs mt-1 ${
                        msg.sender === 'me' ? 'text-white/60' : 'text-gray-400'
                      }`}>
                        {msg.time}
                      </p>
                    </div>
                  </div>
                ))}
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
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  />
                  <button
                    onClick={handleSend}
                    className="p-3 bg-[#0F172A] text-white rounded-full hover:bg-gray-800 transition-colors"
                  >
                    <Send size={18} />
                  </button>
                </div>
                <p className="text-xs text-gray-400 text-center mt-2 flex items-center justify-center gap-1">
                  <Coins size={12} />
                  1 coin per message
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
