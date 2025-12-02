import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Send } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useSocket } from '@/context/SocketContext';
import api from '@/services/api';
import { toast } from 'sonner';

const ChatRoom = () => {
  const { userId } = useParams();
  const { user } = useAuth();
  const { sendMessage, messages: socketMessages, connected } = useSocket();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchProfile();
    fetchMessageHistory();
  }, [userId]);

  useEffect(() => {
    // Add new messages from socket
    const newSocketMessages = socketMessages.filter(
      (msg) => msg.sender_id === userId || msg.recipient_id === userId
    );
    if (newSocketMessages.length > 0) {
      setMessages((prev) => [...prev, ...newSocketMessages]);
    }
  }, [socketMessages, userId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchProfile = async () => {
    try {
      const response = await api.get(`/profiles/${userId}`);
      setProfile(response.data);
    } catch (error) {
      toast.error('Failed to load profile');
    }
  };

  const fetchMessageHistory = async () => {
    try {
      const response = await api.get(`/messages/history/${userId}`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    if (!connected) {
      toast.error('Not connected to chat server');
      return;
    }

    try {
      sendMessage(userId, newMessage);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender_id: user.id,
          recipient_id: userId,
          content: newMessage,
          sent_at: new Date().toISOString(),
        },
      ]);
      setNewMessage('');
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <p>Loading chat...</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <Card className="h-[calc(100vh-12rem)]">
          {/* Chat Header */}
          <CardHeader className="border-b">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={() => navigate('/messages')}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <Avatar className="h-10 w-10">
                <AvatarImage src={profile?.profile_picture_url} />
                <AvatarFallback>
                  {profile?.display_name?.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <h2 className="font-semibold">{profile?.display_name}</h2>
                {profile?.is_online && (
                  <Badge variant="success" className="bg-green-500 text-xs">Online</Badge>
                )}
              </div>
              {profile?.price_per_message > 0 && (
                <Badge variant="secondary">{profile.price_per_message} credits/msg</Badge>
              )}
            </div>
          </CardHeader>

          <CardContent className="flex flex-col h-full p-0">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p>No messages yet</p>
                  <p className="text-sm">Start the conversation!</p>
                </div>
              ) : (
                messages.map((message) => {
                  const isOwn = message.sender_id === user.id;
                  return (
                    <div
                      key={message.id}
                      className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          isOwn
                            ? 'bg-pink-500 text-white'
                            : 'bg-gray-200 text-gray-900'
                        }`}
                      >
                        <p className="break-words">{message.content}</p>
                        <p className={`text-xs mt-1 ${
                          isOwn ? 'text-pink-100' : 'text-gray-500'
                        }`}>
                          {new Date(message.sent_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="border-t p-4">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <Input
                  placeholder="Type a message..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" disabled={!connected || !newMessage.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </form>
              {!connected && (
                <p className="text-xs text-red-500 mt-2">Disconnected from chat server</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default ChatRoom;