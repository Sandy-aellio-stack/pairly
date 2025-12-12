import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
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
      color: 'from-violet-500 to-fuchsia-500',
    },
    {
      icon: Video,
      title: 'Video & Voice Calls',
      description: 'Connect face-to-face with video calls or have voice conversations before meeting in person.',
      color: 'from-orange-500 to-rose-500',
    },
    {
      icon: Shield,
      title: 'Verified Profiles',
      description: 'Photo verification and ID checks ensure you\'re talking to real people. Safety is our top priority.',
      color: 'from-emerald-500 to-teal-500',
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
      color: 'from-indigo-500 to-violet-500',
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
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-violet-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-violet-100 text-violet-700">
            <Sparkles className="h-4 w-4 mr-2 inline" />
            Powerful Features
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6 text-slate-900">
            Everything you need to
            <span className="block bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              find your match
            </span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
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
                    <h3 className="text-xl font-bold mb-3 text-slate-900">{feature.title}</h3>
                    <p className="text-slate-600">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Additional Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-12 text-slate-900">And so much more...</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {additionalFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm">
                  <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                    <Icon className="h-5 w-5 text-violet-600" />
                  </div>
                  <span className="font-medium text-slate-700">{feature.text}</span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-3xl p-12 text-white shadow-2xl">
            <h2 className="text-3xl font-bold mb-4">Ready to experience these features?</h2>
            <p className="text-lg mb-8 opacity-90">Join millions of users finding meaningful connections.</p>
            <Button size="lg" onClick={() => navigate('/signup')} className="bg-white text-violet-600 hover:bg-slate-100 rounded-full px-8 font-semibold">
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Features;
