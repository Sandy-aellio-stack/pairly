import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Heart, Shield, Lock, Eye, AlertTriangle, CheckCircle,
  UserCheck, Phone, Flag, Ban, ArrowRight
} from 'lucide-react';

const Safety = () => {
  const navigate = useNavigate();

  const safetyFeatures = [
    {
      icon: UserCheck,
      title: 'Photo Verification',
      description: 'Verify your photos to get a blue checkmark and show others you\'re real.',
    },
    {
      icon: Shield,
      title: 'ID Verification',
      description: 'Optional ID verification for an extra layer of trust and safety.',
    },
    {
      icon: Lock,
      title: 'End-to-End Encryption',
      description: 'Your messages are encrypted and can only be read by you and your match.',
    },
    {
      icon: Eye,
      title: 'Private Mode',
      description: 'Browse profiles without being seen. Control who can view your profile.',
    },
    {
      icon: Flag,
      title: 'Easy Reporting',
      description: 'Report inappropriate behavior quickly. Our team reviews reports 24/7.',
    },
    {
      icon: Ban,
      title: 'Block & Unmatch',
      description: 'Block users instantly. They won\'t be able to contact you again.',
    },
  ];

  const safetyTips = [
    'Never share financial information',
    'Video chat before meeting in person',
    'Meet in public places first',
    'Tell a friend about your plans',
    'Trust your instincts',
    'Report suspicious behavior',
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
              <Link to="/safety" className="text-amber-600 font-medium">Safety</Link>
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
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-green-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-green-100 text-green-700">
            <Shield className="h-4 w-4 mr-2 inline" />
            Your Safety Matters
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6">
            Date with
            <span className="block bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
              confidence
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            We're committed to creating a safe space for meaningful connections. 
            Your security is built into everything we do.
          </p>
        </div>
      </section>

      {/* Safety Features */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Built-in Safety Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {safetyFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="border-2 border-green-100 hover:border-green-300 transition-colors">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center mb-4">
                      <Icon className="h-6 w-6 text-green-600" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Safety Tips */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-amber-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Safety Tips</h2>
            <p className="text-gray-600">Follow these guidelines for a safer dating experience</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {safetyTips.map((tip, index) => (
              <div key={index} className="flex items-center gap-3 bg-white p-4 rounded-xl shadow-sm">
                <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                <span className="font-medium">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Emergency */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-red-50 border-red-200">
            <CardContent className="p-8 text-center">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold mb-4">Need Help?</h3>
              <p className="text-gray-600 mb-6">
                If you're in immediate danger, please contact emergency services.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button variant="outline" className="border-red-300 text-red-600 hover:bg-red-100">
                  <Phone className="mr-2 h-4 w-4" />
                  Emergency: 911
                </Button>
                <Button className="bg-red-500 hover:bg-red-600">
                  Contact Safety Team
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Safety;
