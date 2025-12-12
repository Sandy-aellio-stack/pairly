import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { 
  Heart, MessageSquare, Shield, Users, Star, CheckCircle, 
  Sparkles, Globe, MapPin, Camera, Play, ArrowRight,
  Smartphone, QrCode, Calendar, Video
} from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();

  const lifestyles = [
    { label: 'Outdoors', image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=400&fit=crop' },
    { label: 'Running', image: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop' },
    { label: 'Dog Parent', image: 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=400&fit=crop' },
  ];

  const stats = [
    { value: '50K+', label: 'Active Users' },
    { value: '2.5M+', label: 'Connections Made' },
    { value: '4.8★', label: 'User Rating' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-violet-50">
      <Navbar />

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto mb-16">
            <Badge className="mb-6 bg-violet-100 text-violet-700 hover:bg-violet-100 px-4 py-2 text-sm">
              <Sparkles className="h-4 w-4 mr-2 inline" />
              Making meaningful connections since 2024
            </Badge>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight mb-6">
              We exist to bring people
              <span className="block bg-gradient-to-r from-violet-600 via-fuchsia-500 to-pink-500 bg-clip-text text-transparent">
                closer to love.
              </span>
            </h1>
            <p className="text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto mb-8">
              We want our members to find meaningful and authentic relationships 
              that ignite confidence and joy.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/signup')}
                className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 text-lg px-8 py-6 rounded-full shadow-lg shadow-violet-500/25"
              >
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8 py-6 rounded-full border-2 border-slate-300 hover:border-violet-400"
              >
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </div>
          </div>

          {/* Lifestyle Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {lifestyles.map((item, index) => (
              <div key={index} className="relative group cursor-pointer">
                <div className="aspect-square rounded-3xl overflow-hidden shadow-xl">
                  <img 
                    src={item.image} 
                    alt={item.label}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent" />
                  <Badge className="absolute bottom-4 left-4 bg-white/90 text-slate-800 backdrop-blur-sm">
                    {item.label}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600">
        <div className="max-w-4xl mx-auto text-center text-white">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Be the first to know</h2>
          <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto">
            Pairly has led to millions of relationships, marriages, and friendships around the world. 
            Want to see what we're building next? Sign up to get our latest updates.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <Input 
              type="email" 
              placeholder="Enter your email" 
              className="bg-white/20 border-white/30 text-white placeholder:text-white/70 rounded-full"
            />
            <Button className="bg-white text-violet-600 hover:bg-slate-100 rounded-full px-8 font-semibold">
              Subscribe
            </Button>
          </div>
        </div>
      </section>

      {/* AI Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 bg-fuchsia-100 text-fuchsia-700 hover:bg-fuchsia-100">
                <Sparkles className="h-4 w-4 mr-2 inline" />
                AI-Powered Matching
              </Badge>
              <h2 className="text-4xl sm:text-5xl font-bold mb-6 text-slate-900">
                Smart connections,
                <span className="block text-fuchsia-600">meaningful matches</span>
              </h2>
              <p className="text-lg text-slate-600 mb-8">
                Whether it's tips from our dating experts, how we're using AI to power better 
                matchmaking, or feature updates like ID Verification that improve members' safety, 
                you'll be the first to discover how we're putting love at the heart of dating.
              </p>
              <div className="space-y-4">
                {[
                  { icon: Shield, text: 'ID Verification for safer dating' },
                  { icon: Sparkles, text: 'AI-powered compatibility matching' },
                  { icon: MessageSquare, text: 'Expert dating advice & tips' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center">
                      <item.icon className="h-5 w-5 text-violet-600" />
                    </div>
                    <span className="text-slate-700 font-medium">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="grid grid-cols-2 gap-4">
                <img 
                  src="https://images.unsplash.com/photo-1516914943479-89db7d9ae7f2?w=400&h=500&fit=crop" 
                  alt="Connection"
                  className="rounded-3xl shadow-xl"
                />
                <img 
                  src="https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400&h=500&fit=crop" 
                  alt="Friends"
                  className="rounded-3xl shadow-xl mt-8"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Date & BFF Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Date Card */}
            <Card className="overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-shadow">
              <div className="h-64 bg-gradient-to-br from-violet-500 to-fuchsia-500 relative">
                <img 
                  src="https://images.unsplash.com/photo-1523908511403-7fc7b25592f4?w=600&h=400&fit=crop"
                  alt="Date"
                  className="w-full h-full object-cover mix-blend-overlay opacity-60"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Heart className="h-16 w-16 text-white" />
                </div>
              </div>
              <CardContent className="p-8">
                <Badge className="mb-4 bg-violet-100 text-violet-700">Pairly Date</Badge>
                <h3 className="text-2xl font-bold mb-3 text-slate-900">Find Your Person</h3>
                <p className="text-slate-600 mb-6">
                  Whether you're new to dating or ready to try again, Pairly Date is built 
                  to bring you closer to love safely and meaningfully.
                </p>
                <Button className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 rounded-full">
                  Find your person
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            {/* BFF Card */}
            <Card className="overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-shadow">
              <div className="h-64 bg-gradient-to-br from-cyan-500 to-blue-500 relative">
                <img 
                  src="https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600&h=400&fit=crop"
                  alt="BFF"
                  className="w-full h-full object-cover mix-blend-overlay opacity-60"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Users className="h-16 w-16 text-white" />
                </div>
              </div>
              <CardContent className="p-8">
                <Badge className="mb-4 bg-cyan-100 text-cyan-700">Pairly BFF</Badge>
                <h3 className="text-2xl font-bold mb-3 text-slate-900">Find Your People</h3>
                <p className="text-slate-600 mb-6">
                  Whether you've moved to a new city or just want to expand your circle, 
                  BFF makes it easy to meet like-minded people who match your vibe.
                </p>
                <Button className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 rounded-full">
                  Find your people
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Testimonial */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex justify-center mb-8">
            <div className="flex -space-x-4">
              <img 
                src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop" 
                alt="Leslie"
                className="w-20 h-20 rounded-full border-4 border-white shadow-lg"
              />
              <img 
                src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop" 
                alt="Thomas"
                className="w-20 h-20 rounded-full border-4 border-white shadow-lg"
              />
            </div>
          </div>
          <blockquote className="text-2xl sm:text-3xl font-medium text-slate-800 mb-6 italic">
            "We are both naturally positive, happy-go-getters, but when you put us together, 
            it feels like there is nothing we can't accomplish."
          </blockquote>
          <p className="text-slate-600">
            <span className="font-semibold">Leslie & Thomas</span>, married in 2025
          </p>
        </div>
      </section>

      {/* IRL Events */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-indigo-100 to-violet-100">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 bg-indigo-200 text-indigo-700">
                <Calendar className="h-4 w-4 mr-2 inline" />
                Pairly IRL
              </Badge>
              <h2 className="text-4xl sm:text-5xl font-bold mb-6 text-slate-900">
                Start the chat
                <span className="block text-indigo-600">in person</span>
              </h2>
              <p className="text-lg text-slate-600 mb-8">
                Pairly IRL events mean you can stop typing and start talking. 
                Come solo or bring a friend—and leave with a new connection.
              </p>
              <Button className="bg-indigo-600 hover:bg-indigo-700 rounded-full px-8">
                Find events near you
                <MapPin className="ml-2 h-4 w-4" />
              </Button>
            </div>
            <div className="relative">
              <img 
                src="https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?w=600&h=500&fit=crop"
                alt="IRL Event"
                className="rounded-3xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* App Download Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="flex justify-center gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="w-48 h-96 bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border-4 border-slate-800">
                    <div className="w-full h-full bg-gradient-to-b from-violet-500 to-fuchsia-500 p-4">
                      <div className="w-full h-full bg-white/10 rounded-2xl backdrop-blur" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <Badge className="mb-4 bg-slate-100 text-slate-700">
                <Smartphone className="h-4 w-4 mr-2 inline" />
                Mobile App
              </Badge>
              <h2 className="text-4xl sm:text-5xl font-bold mb-6 text-slate-900">
                Get the app
              </h2>
              <p className="text-lg text-slate-600 mb-8">
                Just scan the QR code to get started. Available on iOS and Android.
              </p>
              <div className="flex items-center gap-6">
                <div className="w-32 h-32 bg-white rounded-2xl shadow-lg p-4 flex items-center justify-center border">
                  <QrCode className="w-full h-full text-slate-800" />
                </div>
                <div className="space-y-3">
                  <Button variant="outline" className="w-full justify-start gap-2 rounded-xl">
                    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                    </svg>
                    App Store
                  </Button>
                  <Button variant="outline" className="w-full justify-start gap-2 rounded-xl">
                    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3.609 1.814L13.792 12 3.61 22.186a.996.996 0 01-.61-.92V2.734a1 1 0 01.609-.92zm10.89 10.893l2.302 2.302-10.937 6.333 8.635-8.635zm3.199-3.198l2.807 1.626a1 1 0 010 1.73l-2.808 1.626L15.206 12l2.492-2.491zM5.864 2.658L16.8 8.99l-2.302 2.302-8.634-8.634z"/>
                    </svg>
                    Google Play
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 rounded-3xl p-12 text-white text-center shadow-2xl">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Connect with Purpose, Not Just Profiles
            </h2>
            <p className="text-xl mb-8 opacity-90">
              Join thousands of people who found their perfect match through meaningful 
              conversations and high-quality connections.
            </p>
            <div className="grid grid-cols-3 gap-8 mb-8">
              {stats.map((stat, index) => (
                <div key={index}>
                  <p className="text-4xl font-bold">{stat.value}</p>
                  <p className="text-sm opacity-80">{stat.label}</p>
                </div>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/signup')}
                className="bg-white text-violet-600 hover:bg-slate-100 rounded-full px-8 font-semibold"
              >
                Get Started Free
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-white text-white hover:bg-white/10 rounded-full px-8"
              >
                Watch Demo
              </Button>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
