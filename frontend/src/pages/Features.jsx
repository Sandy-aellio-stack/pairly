import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Heart, MessageSquare, Shield, Users, Sparkles, Globe, 
  MapPin, Camera, Video, Zap, Lock, Bell, Search, Star,
  ArrowRight, CheckCircle
} from 'lucide-react';

const Features = () => {
  const navigate = useNavigate();

  const mainFeatures = [
    {
      icon: Globe,
      title: 'Snap Map Style Discovery',
      description: 'See nearby users on an interactive map. Discover people around you in real-time with our location-based matching.',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Sparkles,
      title: 'AI-Powered Matching',
      description: 'Our intelligent algorithm learns your preferences and suggests compatible matches based on interests, values, and behavior.',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Video,
      title: 'Video & Voice Calls',
      description: 'Connect face-to-face with video calls or have voice conversations before meeting in person.',
      color: 'from-amber-500 to-orange-500',
    },
    {
      icon: Shield,
      title: 'Verified Profiles',
      description: 'Photo verification and ID checks ensure you\'re talking to real people. Safety is our top priority.',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: Camera,
      title: 'Creator Content',
      description: 'Creators can share exclusive content, stories, and updates with their followers.',
      color: 'from-pink-500 to-rose-500',
    },
    {
      icon: MessageSquare,
      title: 'Real-Time Messaging',
      description: 'Instant messaging with read receipts, typing indicators, and rich media sharing.',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  const additionalFeatures = [
    { icon: Bell, text: 'Smart Notifications' },
    { icon: Lock, text: 'End-to-End Encryption' },
    { icon: Search, text: 'Advanced Filters' },
    { icon: Star, text: 'Super Likes' },
    { icon: Users, text: 'Group Chats' },
    { icon: Zap, text: 'Boost Profile' },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-md border-b z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-400 to-pink-500 flex items-center justify-center">
                <Heart className="h-5 w-5 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-amber-600 to-pink-600 bg-clip-text text-transparent">
                Pairly
              </span>
            </Link>
            <div className="hidden md:flex items-center space-x-6">
              <Link to="/features" className="text-amber-600 font-medium">Features</Link>
              <Link to="/safety" className="text-gray-700 hover:text-amber-600 transition font-medium">Safety</Link>
              <Link to="/support" className="text-gray-700 hover:text-amber-600 transition font-medium">Support</Link>
              <Link to="/pricing" className="text-gray-700 hover:text-amber-600 transition font-medium">Pricing</Link>
              <Link to="/creators" className="text-gray-700 hover:text-amber-600 transition font-medium">Creators</Link>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="ghost" onClick={() => navigate('/login')}>Log In</Button>
              <Button onClick={() => navigate('/signup')} className="bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600 rounded-full px-6">
                Join Now
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-amber-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-amber-100 text-amber-700">
            <Sparkles className="h-4 w-4 mr-2 inline" />
            Powerful Features
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6">
            Everything you need to
            <span className="block bg-gradient-to-r from-amber-500 to-pink-500 bg-clip-text text-transparent">
              find your match
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Discover the features that make Pairly the most innovative dating platform.
          </p>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {mainFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow overflow-hidden group">
                  <CardContent className="p-8">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                      <Icon className="h-7 w-7 text-white" />
                    </div>
                    <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Additional Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-12">And so much more...</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {additionalFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm">
                  <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-amber-600" />
                  </div>
                  <span className="font-medium">{feature.text}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-amber-500 to-pink-500 rounded-3xl p-12 text-white">
            <h2 className="text-3xl font-bold mb-4">Ready to experience these features?</h2>
            <p className="text-lg mb-8 opacity-90">Join millions of users finding meaningful connections.</p>
            <Button size="lg" onClick={() => navigate('/signup')} className="bg-white text-pink-600 hover:bg-gray-100 rounded-full px-8">
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Features;
