import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Heart, CheckCircle, Sparkles, Crown, Zap, Star, ArrowRight, X
} from 'lucide-react';

const Pricing = () => {
  const navigate = useNavigate();

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Get started with basic features',
      features: [
        'Create profile',
        'Browse users',
        'Limited daily swipes',
        'Basic matching',
        '1 Super Like per week',
      ],
      notIncluded: [
        'See who likes you',
        'Unlimited swipes',
        'Map discovery',
        'Message anyone',
      ],
      cta: 'Get Started',
      popular: false,
      color: 'gray',
    },
    {
      name: 'Premium',
      price: '$14.99',
      period: '/month',
      description: 'Most popular for serious daters',
      features: [
        'Everything in Free',
        'Unlimited swipes',
        'See who likes you',
        '5 Super Likes per day',
        'Rewind last swipe',
        'Ad-free experience',
        'Priority matching',
      ],
      notIncluded: [
        'Map discovery',
        'Unlimited messages',
      ],
      cta: 'Start Premium',
      popular: true,
      color: 'amber',
    },
    {
      name: 'VIP',
      price: '$29.99',
      period: '/month',
      description: 'Ultimate experience with all features',
      features: [
        'Everything in Premium',
        'Snap Map discovery',
        'Unlimited messages',
        'See who viewed you',
        'Spotlight boost weekly',
        'Priority support',
        'Exclusive badges',
        'Early access to features',
      ],
      notIncluded: [],
      cta: 'Go VIP',
      popular: false,
      color: 'pink',
    },
  ];

  const creatorPlans = [
    {
      name: 'Creator Basic',
      price: '$0',
      period: 'forever',
      revenue: '70% revenue share',
      features: [
        'Post content',
        'Receive tips',
        'Basic analytics',
        'Fan messaging',
      ],
    },
    {
      name: 'Creator Pro',
      price: '$19.99',
      period: '/month',
      revenue: '85% revenue share',
      features: [
        'Everything in Basic',
        'Priority discovery',
        'Advanced analytics',
        'Scheduled posts',
        'Promotional tools',
        'Verified badge',
      ],
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
              <Link to="/pricing" className="text-amber-600 font-medium">Pricing</Link>
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
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-purple-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-purple-100 text-purple-700">
            <Crown className="h-4 w-4 mr-2 inline" />
            Simple Pricing
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6">
            Find love at
            <span className="block bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
              any price
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Choose the plan that's right for you. All plans include our core matching features.
          </p>
        </div>
      </section>

      {/* User Plans */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-4">For Users</h2>
          <p className="text-gray-600 text-center mb-12">Find your perfect match</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <Card key={index} className={`relative overflow-hidden ${plan.popular ? 'border-2 border-amber-500 shadow-xl scale-105' : 'border'}`}>
                {plan.popular && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-amber-500 to-pink-500 text-white px-4 py-1 text-sm font-semibold">
                    Most Popular
                  </div>
                )}
                <CardContent className="p-8">
                  <div className="mb-6">
                    <h3 className="text-2xl font-bold">{plan.name}</h3>
                    <p className="text-gray-600 text-sm">{plan.description}</p>
                  </div>
                  <div className="mb-6">
                    <span className="text-5xl font-bold">{plan.price}</span>
                    <span className="text-gray-600">{plan.period}</span>
                  </div>
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                    {plan.notIncluded.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-gray-400">
                        <X className="h-5 w-5 flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className={`w-full rounded-full ${
                      plan.popular 
                        ? 'bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600' 
                        : plan.color === 'pink' 
                          ? 'bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600'
                          : ''
                    }`}
                    variant={plan.popular || plan.color === 'pink' ? 'default' : 'outline'}
                    onClick={() => navigate('/signup')}
                  >
                    {plan.cta}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Creator Plans */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-pink-50 to-purple-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="mb-4 bg-pink-100 text-pink-700">
              <Sparkles className="h-4 w-4 mr-2 inline" />
              For Creators
            </Badge>
            <h2 className="text-3xl font-bold mb-4">Monetize Your Content</h2>
            <p className="text-gray-600">Turn your passion into profit</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {creatorPlans.map((plan, index) => (
              <Card key={index} className="border-2 hover:border-pink-300 transition-colors">
                <CardContent className="p-8">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-gray-600">{plan.period}</span>
                  </div>
                  <Badge className="mb-6 bg-green-100 text-green-700">{plan.revenue}</Badge>
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className="w-full rounded-full"
                    variant={index === 1 ? 'default' : 'outline'}
                    onClick={() => navigate('/signup')}
                  >
                    {index === 0 ? 'Start Creating' : 'Go Pro'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-8">Questions?</h2>
          <p className="text-gray-600 mb-8">
            All subscriptions can be cancelled anytime. We offer a 7-day money-back guarantee.
          </p>
          <Button variant="outline" onClick={() => navigate('/support')} className="rounded-full">
            Visit Help Center
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </section>
    </div>
  );
};

export default Pricing;
