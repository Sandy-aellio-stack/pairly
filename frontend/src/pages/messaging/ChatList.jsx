import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

const ChatList = () => {
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await api.get('/messages/conversations');
      setConversations(response.data);
    } catch (error) {
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const filteredConversations = conversations.filter((conv) =>
    conv.display_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Messages</h1>

        {/* Search Bar */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Conversations List */}
        {loading ? (
          <div className="text-center py-8 text-gray-600">Loading conversations...</div>
        ) : filteredConversations.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-600">No conversations yet</p>
              <p className="text-sm text-gray-500 mt-2">Start chatting with creators to see your messages here</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {filteredConversations.map((conversation) => (
              <Card
                key={conversation.user_id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => navigate(`/messages/${conversation.user_id}`)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center space-x-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={conversation.profile_picture_url} />
                      <AvatarFallback>
                        {conversation.display_name?.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold truncate">{conversation.display_name}</h3>
                        {conversation.is_online && (
                          <Badge variant="success" className="bg-green-500 ml-2">Online</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate">Click to start chatting</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default ChatList;