import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { 
  Heart, HelpCircle, MessageSquare, Mail, Phone,
  ChevronDown, ChevronUp, Search
} from 'lucide-react';

const Support = () => {
  const navigate = useNavigate();
  const [openFaq, setOpenFaq] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const faqs = [
    {
      question: 'How do I create an account?',
      answer: 'Click "Join Now" and follow the signup process. You can sign up as a Fan to discover creators or as a Creator to share content and earn.',
    },
    {
      question: 'How does the map feature work?',
      answer: 'Our Snap Map-style feature shows nearby users in real-time. Enable location sharing to see who\'s around you. A subscription is required to interact with nearby users.',
    },
    {
      question: 'What\'s the difference between Fan and Creator accounts?',
      answer: 'Fans can browse, discover, and interact with creators. Creators get additional features like content posting, analytics, and the ability to earn from their content.',
    },
    {
      question: 'How do subscriptions work?',
      answer: 'Subscribe to unlock premium features like unlimited messaging, map interactions, and exclusive content. Plans start at $9.99/month.',
    },
    {
      question: 'How do I verify my profile?',
      answer: 'Go to Settings > Verification. Take a selfie following our pose guide. Our team will review and verify within 24 hours.',
    },
    {
      question: 'How can I report someone?',
      answer: 'Tap the three dots on any profile or conversation and select "Report". Our safety team reviews all reports within 24 hours.',
    },
  ];

  const filteredFaqs = faqs.filter(faq => 
    faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
    faq.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
              <Link to="/support" className="text-amber-600 font-medium">Support</Link>
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
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-blue-100 text-blue-700">
            <HelpCircle className="h-4 w-4 mr-2 inline" />
            Help Center
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6">
            How can we
            <span className="block bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent">
              help you?
            </span>
          </h1>
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input 
              placeholder="Search for answers..." 
              className="pl-12 py-6 text-lg rounded-full"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {filteredFaqs.map((faq, index) => (
              <Card key={index} className="overflow-hidden">
                <button
                  className="w-full p-6 text-left flex justify-between items-center"
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                >
                  <span className="font-semibold text-lg">{faq.question}</span>
                  {openFaq === index ? (
                    <ChevronUp className="h-5 w-5 text-gray-500" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-500" />
                  )}
                </button>
                {openFaq === index && (
                  <CardContent className="pt-0 pb-6 px-6">
                    <p className="text-gray-600">{faq.answer}</p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Still need help?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">Live Chat</h3>
                <p className="text-gray-600 mb-4">Chat with our support team in real-time</p>
                <Button className="w-full">Start Chat</Button>
              </CardContent>
            </Card>
            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">Email Us</h3>
                <p className="text-gray-600 mb-4">We'll respond within 24 hours</p>
                <Button variant="outline" className="w-full">support@pairly.com</Button>
              </CardContent>
            </Card>
            <Card className="text-center hover:shadow-lg transition-shadow">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-8 w-8 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">Call Us</h3>
                <p className="text-gray-600 mb-4">Mon-Fri, 9am-6pm EST</p>
                <Button variant="outline" className="w-full">1-800-PAIRLY</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8">Send us a message</h2>
          <Card>
            <CardContent className="p-8">
              <form className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Name</label>
                    <Input placeholder="Your name" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Email</label>
                    <Input type="email" placeholder="your@email.com" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Subject</label>
                  <Input placeholder="How can we help?" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Message</label>
                  <Textarea placeholder="Tell us more..." rows={5} />
                </div>
                <Button className="w-full bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-600 hover:to-pink-600">
                  Send Message
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Support;
