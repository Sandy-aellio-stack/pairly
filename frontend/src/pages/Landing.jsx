import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Heart, MessageSquare, DollarSign, Shield, Zap, Users, Star, CheckCircle } from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Heart,
      title: 'Meaningful Connections',
      description: 'Connect with creators and fans who share your interests and passions',
    },
    {
      icon: MessageSquare,
      title: 'Real-Time Messaging',
      description: 'Engage in instant conversations with your favorite creators',
    },
    {
      icon: DollarSign,
      title: 'Monetize Your Content',
      description: 'Creators earn directly from their interactions and content',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Advanced security with 2FA and fraud detection to keep you safe',
    },
    {
      icon: Zap,
      title: 'Instant Payouts',
      description: 'Get paid quickly with our seamless payout system',
    },
    {
      icon: Users,
      title: 'Growing Community',
      description: 'Join thousands of creators and fans building meaningful relationships',
    },
  ];

  const stats = [
    { value: '10,000+', label: 'Active Creators' },
    { value: '$2M+', label: 'Creator Earnings' },
    { value: '50,000+', label: 'Connections Made' },
    { value: '4.9/5', label: 'User Rating' },
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'Content Creator',
      image: 'https://i.pravatar.cc/150?img=1',
      quote: 'Pairly has transformed how I connect with my audience. The earnings are amazing!',
      rating: 5,
    },
    {
      name: 'Mike Chen',
      role: 'Fan',
      image: 'https://i.pravatar.cc/150?img=3',
      quote: 'Finally, a platform where I can have real conversations with my favorite creators.',
      rating: 5,
    },
    {
      name: 'Emily Rodriguez',
      role: 'Content Creator',
      image: 'https://i.pravatar.cc/150?img=5',
      quote: 'The security features give me peace of mind. Highly recommend for creators!',
      rating: 5,
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/90 backdrop-blur-md border-b z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="text-3xl font-bold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
              Pairly
            </Link>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900 transition">
                Features
              </a>
              <a href="#how-it-works" className="text-gray-600 hover:text-gray-900 transition">
                How It Works
              </a>
              <a href="#testimonials" className="text-gray-600 hover:text-gray-900 transition">
                Testimonials
              </a>
              <a href="#pricing" className="text-gray-600 hover:text-gray-900 transition">
                Pricing
              </a>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={() => navigate('/login')}>
                Log In
              </Button>
              <Button onClick={() => navigate('/signup')} className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700">
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <Badge className="bg-pink-100 text-pink-700 hover:bg-pink-100">
                ✨ The Future of Creator Connections
              </Badge>
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight">
                Creator is now a
                <span className="block bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
                  career
                </span>
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed">
                Connect with creators you love. Support their journey. Build meaningful relationships. Start earning from your passion today.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  onClick={() => navigate('/signup')}
                  className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-lg px-8 py-6"
                >
                  Start Creating
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/discovery')}
                  className="text-lg px-8 py-6"
                >
                  Explore Creators
                </Button>
              </div>
              <div className="flex items-center space-x-8 pt-4">
                <div className="flex -space-x-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <img
                      key={i}
                      src={`https://i.pravatar.cc/40?img=${i}`}
                      alt="User"
                      className="w-10 h-10 rounded-full border-2 border-white"
                    />
                  ))}
                </div>
                <div>
                  <p className="text-sm font-semibold">Join 10,000+ creators</p>
                  <p className="text-xs text-gray-500">Earning on Pairly</p>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="aspect-square rounded-3xl bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-500 overflow-hidden shadow-2xl">
                <img
                  src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800&h=800&fit=crop"
                  alt="Creator"
                  className="w-full h-full object-cover mix-blend-overlay opacity-90"
                />
              </div>
              <div className="absolute -bottom-6 -left-6 bg-white p-6 rounded-2xl shadow-xl">
                <p className="text-sm text-gray-600 mb-1">Monthly Earnings</p>
                <p className="text-3xl font-bold text-green-600">$12,450</p>
              </div>
              <div className="absolute -top-6 -right-6 bg-white p-6 rounded-2xl shadow-xl">
                <p className="text-sm text-gray-600 mb-1">Active Fans</p>
                <p className="text-3xl font-bold text-blue-600">2,345</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <p className="text-4xl font-bold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-gray-600 mt-2">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-100 text-purple-700 hover:bg-purple-100">
              Features
            </Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Everything you need to succeed</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful tools designed for creators and fans to build lasting connections
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow border-2">
                  <CardContent className="pt-6">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center mb-4">
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-pink-100 text-pink-700 hover:bg-pink-100">
              How It Works
            </Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Start earning in minutes</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Three simple steps to launch your creator career
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Create Your Profile',
                description: 'Sign up and build your creator profile with photos and bio',
              },
              {
                step: '02',
                title: 'Set Your Prices',
                description: 'Choose your message pricing and start connecting with fans',
              },
              {
                step: '03',
                title: 'Start Earning',
                description: 'Get paid instantly for every message and interaction',
              },
            ].map((step, index) => (
              <div key={index} className="relative">
                <div className="text-7xl font-bold text-pink-100 mb-4">{step.step}</div>
                <h3 className="text-2xl font-semibold mb-3">{step.title}</h3>
                <p className="text-gray-600 text-lg">{step.description}</p>
                {index < 2 && (
                  <div className="hidden md:block absolute top-12 -right-4 w-8 h-0.5 bg-pink-200" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-100 text-purple-700 hover:bg-purple-100">
              Testimonials
            </Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Loved by creators and fans</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              See what our community has to say about their experience
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <div className="flex items-center mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
                  <div className="flex items-center">
                    <img
                      src={testimonial.image}
                      alt={testimonial.name}
                      className="w-12 h-12 rounded-full mr-4"
                    />
                    <div>
                      <p className="font-semibold">{testimonial.name}</p>
                      <p className="text-sm text-gray-500">{testimonial.role}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-pink-100 text-pink-700 hover:bg-pink-100">
              Pricing
            </Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Simple, transparent pricing</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Pay only for what you use. No hidden fees.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <Card className="border-2">
              <CardContent className="pt-6">
                <h3 className="text-2xl font-bold mb-2">For Fans</h3>
                <p className="text-gray-600 mb-6">Connect with your favorite creators</p>
                <div className="mb-6">
                  <span className="text-5xl font-bold">$0</span>
                  <span className="text-gray-600">/month</span>
                </div>
                <ul className="space-y-3 mb-6">
                  {[
                    'Free to join',
                    'Buy credits as needed',
                    'No subscription required',
                    'Secure payments',
                    'Cancel anytime',
                  ].map((item, i) => (
                    <li key={i} className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
                <Button onClick={() => navigate('/signup')} className="w-full" variant="outline">
                  Sign Up as Fan
                </Button>
              </CardContent>
            </Card>

            <Card className="border-2 border-pink-500 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-pink-500 text-white px-4 py-1 text-sm font-semibold">
                Popular
              </div>
              <CardContent className="pt-6">
                <h3 className="text-2xl font-bold mb-2">For Creators</h3>
                <p className="text-gray-600 mb-6">Start earning from your content</p>
                <div className="mb-6">
                  <span className="text-5xl font-bold">80%</span>
                  <span className="text-gray-600">/revenue share</span>
                </div>
                <ul className="space-y-3 mb-6">
                  {[
                    'Keep 80% of earnings',
                    'Instant payouts',
                    'Set your own prices',
                    'Real-time analytics',
                    'Priority support',
                  ].map((item, i) => (
                    <li key={i} className="flex items-center">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  onClick={() => navigate('/signup')}
                  className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700"
                >
                  Start Creating
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-pink-600 to-purple-600 rounded-3xl p-12 text-white">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Ready to start your journey?</h2>
            <p className="text-xl mb-8 opacity-90">
              Join thousands of creators and fans building meaningful connections on Pairly
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/signup')}
                className="bg-white text-pink-600 hover:bg-gray-100 text-lg px-8 py-6"
              >
                Get Started Free
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate('/discovery')}
                className="border-white text-white hover:bg-white/10 text-lg px-8 py-6"
              >
                Explore Creators
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent mb-4">
                Pairly
              </h3>
              <p className="text-gray-400">
                The premier platform for creator connections and monetization.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition">How It Works</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white transition">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Pairly. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;