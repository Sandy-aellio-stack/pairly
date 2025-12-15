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
      <section className="relative min-h-[90vh] flex items-center px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Background atmosphere */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-300/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-fuchsia-300/20 rounded-full blur-3xl"></div>
        </div>

        <div className="max-w-[1400px] mx-auto w-full">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Content */}
            <div className="text-center lg:text-left">
              <Badge className="mb-6 bg-violet-100 text-violet-700 hover:bg-violet-100 px-4 py-2 text-sm inline-flex items-center">
                <Sparkles className="h-4 w-4 mr-2" />
                <span>Making meaningful <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent font-semibold">connections</span> since 2024</span>
              </Badge>
              
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.1] mb-6">
                We exist to bring people
                <span className="block mt-2 bg-gradient-to-r from-violet-600 via-fuchsia-500 to-pink-500 bg-clip-text text-transparent">
                  closer to love.
                </span>
              </h1>
              
              <p className="text-xl text-slate-600 leading-relaxed mb-8 max-w-xl lg:mx-0 mx-auto">
                We want our members to find meaningful and authentic relationships 
                that ignite confidence and joy.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 lg:justify-start justify-center mb-4">
                <Button
                  size="lg"
                  onClick={() => navigate('/signup')}
                  className="relative bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 text-lg px-10 py-7 rounded-full shadow-xl shadow-violet-500/30 hover:shadow-2xl hover:shadow-violet-500/40 transition-all duration-300"
                >
                  Get Started Free
                  <ArrowRight className="ml-2 h-5 w-5" />
                  <div className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-400 to-fuchsia-400 blur-xl opacity-40 group-hover:opacity-60 transition-opacity -z-10"></div>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg px-10 py-7 rounded-full border border-slate-200 hover:border-violet-300 hover:bg-violet-50 text-slate-700 transition-all"
                >
                  <Play className="mr-2 h-5 w-5" />
                  Watch Demo
                </Button>
              </div>
              
              <p className="text-sm text-slate-500">
                No credit card required · 10 free coins
              </p>
            </div>

            {/* Right Column - Phone Mockup with Floating Cards */}
            <div className="relative lg:block hidden">
              {/* Radial glow behind phone */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-80 h-80 bg-gradient-to-br from-violet-400/30 to-fuchsia-400/30 rounded-full blur-3xl"></div>
              </div>

              {/* Phone mockup */}
              <div className="relative z-10 flex justify-center">
                <div className="w-72 h-[580px] bg-slate-900 rounded-[3rem] shadow-2xl overflow-hidden border-8 border-slate-800 transform scale-105">
                  <div className="w-full h-full bg-gradient-to-b from-violet-500 to-fuchsia-500 p-6">
                    <div className="w-full h-full bg-white/10 rounded-3xl backdrop-blur-sm flex flex-col items-center justify-center gap-4 p-6">
                      <div className="w-20 h-20 rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
                        <Heart className="h-10 w-10 text-white" />
                      </div>
                      <div className="text-center text-white space-y-2">
                        <h3 className="font-bold text-lg">Find Your Match</h3>
                        <p className="text-sm opacity-90">Start meaningful connections today</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating cards */}
              <style dangerouslySetInnerHTML={{__html: `
                @keyframes float-slow {
                  0%, 100% { transform: translateY(0px); }
                  50% { transform: translateY(-20px); }
                }
                @keyframes float-medium {
                  0%, 100% { transform: translateY(0px); }
                  50% { transform: translateY(-15px); }
                }
                @keyframes float-fast {
                  0%, 100% { transform: translateY(0px); }
                  50% { transform: translateY(-10px); }
                }
                .float-slow { animation: float-slow 6s ease-in-out infinite; }
                .float-medium { animation: float-medium 5s ease-in-out infinite; }
                .float-fast { animation: float-fast 4s ease-in-out infinite; }
              `}} />

              {/* Top left card */}
              <div className="absolute top-12 -left-8 float-slow z-20">
                <div className="bg-white rounded-2xl shadow-xl p-4 w-48 border border-slate-100">
                  <div className="flex items-center gap-3 mb-2">
                    <img 
                      src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop" 
                      alt="User"
                      className="w-12 h-12 rounded-full"
                    />
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-slate-900">Emma</p>
                      <p className="text-xs text-slate-500">0.3 mi away</p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {[1,2,3,4,5].map((i) => (
                      <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                </div>
              </div>

              {/* Top right card */}
              <div className="absolute top-32 -right-12 float-medium z-20">
                <div className="bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-2xl shadow-xl p-4 w-44">
                  <div className="flex items-center gap-2 text-white mb-2">
                    <CheckCircle className="h-5 w-5" />
                    <p className="font-semibold text-sm">Verified</p>
                  </div>
                  <p className="text-xs text-white/90">ID verified profiles for safer dating</p>
                </div>
              </div>

              {/* Bottom left card */}
              <div className="absolute bottom-24 -left-12 float-fast z-20">
                <div className="bg-white rounded-2xl shadow-xl p-4 w-44 border border-slate-100">
                  <MessageSquare className="h-6 w-6 text-fuchsia-500 mb-2" />
                  <p className="font-semibold text-sm text-slate-900 mb-1">2.5M+</p>
                  <p className="text-xs text-slate-500">Conversations started</p>
                </div>
              </div>

              {/* Bottom right card */}
              <div className="absolute bottom-12 -right-8 float-medium z-20" style={{animationDelay: '1s'}}>
                <div className="bg-white rounded-2xl shadow-xl p-3 w-40 border border-slate-100">
                  <div className="flex items-center gap-2">
                    <div className="flex -space-x-2">
                      <img src="https://i.pravatar.cc/40?img=1" className="w-8 h-8 rounded-full border-2 border-white" alt="" />
                      <img src="https://i.pravatar.cc/40?img=2" className="w-8 h-8 rounded-full border-2 border-white" alt="" />
                      <img src="https://i.pravatar.cc/40?img=3" className="w-8 h-8 rounded-full border-2 border-white" alt="" />
                    </div>
                    <p className="text-xs text-slate-600 font-medium">+50K online</p>
                  </div>
                </div>
              </div>
            </div>
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
