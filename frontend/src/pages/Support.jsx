import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
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
      <Navbar />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-6 bg-blue-100 text-blue-700">
            <HelpCircle className="h-4 w-4 mr-2 inline" />
            Help Center
          </Badge>
          <h1 className="text-5xl sm:text-6xl font-bold mb-6 text-slate-900">
            How can we
            <span className="block bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent">
              help you?
            </span>
          </h1>
          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <Input 
              placeholder="Search for answers..." 
              className="pl-12 py-6 text-lg rounded-full border-slate-300"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-slate-900">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {filteredFaqs.map((faq, index) => (
              <Card key={index} className="overflow-hidden border-slate-200">
                <button
                  className="w-full p-6 text-left flex justify-between items-center hover:bg-slate-50 transition"
                  onClick={() => setOpenFaq(openFaq === index ? null : index)}
                >
                  <span className="font-semibold text-lg text-slate-900">{faq.question}</span>
                  {openFaq === index ? (
                    <ChevronUp className="h-5 w-5 text-slate-500" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-slate-500" />
                  )}
                </button>
                {openFaq === index && (
                  <CardContent className="pt-0 pb-6 px-6">
                    <p className="text-slate-600">{faq.answer}</p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-slate-900">Still need help?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center hover:shadow-lg transition-shadow border-slate-200">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-slate-900">Live Chat</h3>
                <p className="text-slate-600 mb-4">Chat with our support team in real-time</p>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">Start Chat</Button>
              </CardContent>
            </Card>
            <Card className="text-center hover:shadow-lg transition-shadow border-slate-200">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-8 w-8 text-emerald-600" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-slate-900">Email Us</h3>
                <p className="text-slate-600 mb-4">We'll respond within 24 hours</p>
                <Button variant="outline" className="w-full">support@pairly.com</Button>
              </CardContent>
            </Card>
            <Card className="text-center hover:shadow-lg transition-shadow border-slate-200">
              <CardContent className="p-8">
                <div className="w-16 h-16 rounded-full bg-violet-100 flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-8 w-8 text-violet-600" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-slate-900">Call Us</h3>
                <p className="text-slate-600 mb-4">Mon-Fri, 9am-6pm EST</p>
                <Button variant="outline" className="w-full">1-800-PAIRLY</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-slate-900">Send us a message</h2>
          <Card className="border-slate-200">
            <CardContent className="p-8">
              <form className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 text-slate-700">Name</label>
                    <Input placeholder="Your name" className="border-slate-300" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 text-slate-700">Email</label>
                    <Input type="email" placeholder="your@email.com" className="border-slate-300" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-slate-700">Subject</label>
                  <Input placeholder="How can we help?" className="border-slate-300" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2 text-slate-700">Message</label>
                  <Textarea placeholder="Tell us more..." rows={5} className="border-slate-300" />
                </div>
                <Button className="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700">
                  Send Message
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Support;
