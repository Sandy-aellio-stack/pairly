import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { 
  Heart, Camera, DollarSign, Users, TrendingUp, Star,
  CheckCircle, ArrowRight, Sparkles, BarChart3, Zap
} from 'lucide-react';

const Creators = () => {
  const navigate = useNavigate();

  const benefits = [
    {
      icon: DollarSign,
      title: 'Earn From Your Content',
      description: 'Get paid for posts, messages, and tips from your fans. Keep up to 85% of your earnings.',
    },
    {
      icon: Users,
      title: 'Build Your Audience',
      description: 'Grow your fanbase with our discovery features and recommendation algorithm.',
    },
    {
      icon: BarChart3,
      title: 'Track Your Growth',
      description: 'Detailed analytics on views, engagement, earnings, and audience demographics.',
    },
    {
      icon: Zap,
      title: 'Instant Payouts',
      description: 'Get paid weekly or request instant payouts anytime. No minimum threshold.',
    },
  ];

  const stats = [
    { value: '$10M+', label: 'Paid to Creators' },
    { value: '50K+', label: 'Active Creators' },
    { value: '$2,500', label: 'Avg Monthly Earnings' },
  ];

  const testimonials = [
    {
      name: 'Alex Rivera',
      handle: '@alexcreates',
      image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      quote: 'I went from 0 to $5,000/month in just 3 months. The platform makes it so easy to connect with fans.',
      earnings: '$8,500/mo',
    },
    {
      name: 'Mia Chen',
      handle: '@mialifestyle',
      image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      quote: 'The analytics help me understand exactly what my audience wants. My engagement has tripled!',
      earnings: '$12,000/mo',
    },
    {
      name: 'Jordan Taylor',
      handle: '@jordanfit',
      image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop',
      quote: 'Best decision I made was joining Pairly. The community here is genuine and supportive.',
      earnings: '$6,200/mo',
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-fuchsia-600 via-violet-600 to-indigo-600">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="text-white">
              <Badge className="mb-6 bg-white/20 text-white hover:bg-white/20 border-white/30">
                <Sparkles className="h-4 w-4 mr-2 inline" />
                Creator Program
              </Badge>
              <h1 className="text-5xl sm:text-6xl font-bold mb-6">
                Turn your passion into
                <span className="block">a paycheck</span>
              </h1>
              <p className="text-xl opacity-90 mb-8">
                Join thousands of creators earning on Pairly. Share content, connect with fans, 
                and build a sustainable income doing what you love.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  onClick={() => navigate('/signup')}
                  className="bg-white text-violet-600 hover:bg-slate-100 rounded-full px-8 font-semibold"
                >
                  Start Creating
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white text-white hover:bg-white/10 rounded-full px-8"
                >
                  Learn More
                </Button>
              </div>
            </div>
            <div className="hidden lg:block">
              <div className="relative">
                <img 
                  src="https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=600&h=600&fit=crop"
                  alt="Creator"
                  className="rounded-3xl shadow-2xl"
                />
                <div className="absolute -bottom-6 -left-6 bg-white p-4 rounded-2xl shadow-xl">
                  <p className="text-sm text-slate-600">Monthly Earnings</p>
                  <p className="text-2xl font-bold text-emerald-600">$12,450</p>
                </div>
                <div className="absolute -top-6 -right-6 bg-white p-4 rounded-2xl shadow-xl">
                  <p className="text-sm text-slate-600">Total Fans</p>
                  <p className="text-2xl font-bold text-violet-600">24.5K</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <p className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-slate-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 text-slate-900">Why creators love Pairly</h2>
            <p className="text-xl text-slate-600">Everything you need to succeed</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit, index) => {
              const Icon = benefit.icon;
              return (
                <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow text-center">
                  <CardContent className="p-8">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-6">
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-slate-900">{benefit.title}</h3>
                    <p className="text-slate-600">{benefit.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 text-slate-900">Start earning in 3 steps</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Create Account', desc: 'Sign up as a Creator and set up your profile' },
              { step: '2', title: 'Post Content', desc: 'Share photos, videos, and stories with your fans' },
              { step: '3', title: 'Get Paid', desc: 'Earn from subscriptions, tips, and messages' },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center mx-auto mb-6 text-white text-2xl font-bold">
                  {item.step}
                </div>
                <h3 className="text-xl font-bold mb-2 text-slate-900">{item.title}</h3>
                <p className="text-slate-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4 text-slate-900">Creator success stories</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="border-0 shadow-lg">
                <CardContent className="p-8">
                  <div className="flex items-center gap-4 mb-6">
                    <img 
                      src={testimonial.image}
                      alt={testimonial.name}
                      className="w-14 h-14 rounded-full"
                    />
                    <div>
                      <p className="font-bold text-slate-900">{testimonial.name}</p>
                      <p className="text-slate-500 text-sm">{testimonial.handle}</p>
                    </div>
                  </div>
                  <p className="text-slate-700 mb-6 italic">"{testimonial.quote}"</p>
                  <Badge className="bg-emerald-100 text-emerald-700">
                    <TrendingUp className="h-4 w-4 mr-1 inline" />
                    {testimonial.earnings}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-r from-fuchsia-600 via-violet-600 to-indigo-600 rounded-3xl p-12 text-white text-center shadow-2xl">
            <Camera className="h-16 w-16 mx-auto mb-6 opacity-90" />
            <h2 className="text-4xl font-bold mb-4">Ready to start your creator journey?</h2>
            <p className="text-xl mb-8 opacity-90">
              Join today and start earning from day one. No fees to get started.
            </p>
            <Button
              size="lg"
              onClick={() => navigate('/signup')}
              className="bg-white text-violet-600 hover:bg-slate-100 rounded-full px-12 font-semibold"
            >
              Become a Creator
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Creators;
