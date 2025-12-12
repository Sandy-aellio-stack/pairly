import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
              <Link to="/features" className="text-gray-700 hover:text-amber-600 transition font-medium">Features</Link>
              <Link to="/safety" className="text-gray-700 hover:text-amber-600 transition font-medium">Safety</Link>
              <Link to="/support" className="text-gray-700 hover:text-amber-600 transition font-medium">Support</Link>
              <Link to="/pricing" className="text-gray-700 hover:text-amber-600 transition font-medium">Pricing</Link>
              <Link to="/creators" className="text-amber-600 font-medium">Creators</Link>
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
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-pink-500 via-rose-500 to-orange-400">
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
                  className="bg-white text-pink-600 hover:bg-gray-100 rounded-full px-8"
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
                  <p className="text-sm text-gray-600">Monthly Earnings</p>
                  <p className="text-2xl font-bold text-green-600">$12,450</p>
                </div>
                <div className="absolute -top-6 -right-6 bg-white p-4 rounded-2xl shadow-xl">
                  <p className="text-sm text-gray-600">Total Fans</p>
                  <p className="text-2xl font-bold text-pink-600">24.5K</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <p className="text-4xl font-bold bg-gradient-to-r from-pink-500 to-orange-500 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-gray-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Why creators love Pairly</h2>
            <p className="text-xl text-gray-600">Everything you need to succeed</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit, index) => {
              const Icon = benefit.icon;
              return (
                <Card key={index} className="border-0 shadow-lg hover:shadow-xl transition-shadow text-center">
                  <CardContent className="p-8">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-pink-500 to-orange-500 flex items-center justify-center mx-auto mb-6">
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    <h3 className="text-xl font-bold mb-3">{benefit.title}</h3>
                    <p className="text-gray-600">{benefit.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Start earning in 3 steps</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: '1', title: 'Create Account', desc: 'Sign up as a Creator and set up your profile' },
              { step: '2', title: 'Post Content', desc: 'Share photos, videos, and stories with your fans' },
              { step: '3', title: 'Get Paid', desc: 'Earn from subscriptions, tips, and messages' },
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-500 to-orange-500 flex items-center justify-center mx-auto mb-6 text-white text-2xl font-bold">
                  {item.step}
                </div>
                <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Creator success stories</h2>
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
                      <p className="font-bold">{testimonial.name}</p>
                      <p className="text-gray-500 text-sm">{testimonial.handle}</p>
                    </div>
                  </div>
                  <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
                  <Badge className="bg-green-100 text-green-700">
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
          <div className="bg-gradient-to-r from-pink-500 via-rose-500 to-orange-400 rounded-3xl p-12 text-white text-center">
            <Camera className="h-16 w-16 mx-auto mb-6 opacity-90" />
            <h2 className="text-4xl font-bold mb-4">Ready to start your creator journey?</h2>
            <p className="text-xl mb-8 opacity-90">
              Join today and start earning from day one. No fees to get started.
            </p>
            <Button
              size="lg"
              onClick={() => navigate('/signup')}
              className="bg-white text-pink-600 hover:bg-gray-100 rounded-full px-12"
            >
              Become a Creator
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Creators;
