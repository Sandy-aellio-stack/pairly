import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, ArrowLeft, Search, Book, CreditCard, Shield, Users, MessageCircle, Settings, ChevronRight } from 'lucide-react';
import HeartCursor from '@/components/HeartCursor';

const categories = [
  { Icon: Book, title: 'Getting Started', count: 12, description: 'Learn the basics of TrueBond' },
  { Icon: Users, title: 'Profile & Matching', count: 15, description: 'Optimize your profile and matches' },
  { Icon: MessageCircle, title: 'Messaging', count: 10, description: 'Chat features and coin system' },
  { Icon: CreditCard, title: 'Coins & Payments', count: 8, description: 'Purchasing and using coins' },
  { Icon: Shield, title: 'Safety & Privacy', count: 14, description: 'Stay safe while connecting' },
  { Icon: Settings, title: 'Account Settings', count: 11, description: 'Manage your account' },
];

const popularArticles = [
  'How do coins work?',
  'How to verify my profile?',
  'How to report a user?',
  'How to delete my account?',
  'Why was my message not delivered?',
  'How to get a refund?',
];

const HelpCenterPage = () => {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <HeartCursor />
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#0F172A] flex items-center justify-center">
              <Heart size={20} className="text-white" fill="white" />
            </div>
            <span className="text-xl font-bold text-[#0F172A]">TrueBond</span>
          </Link>
          <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-[#0F172A]">
            <ArrowLeft size={20} />
            Back to Home
          </Link>
        </div>
      </header>

      {/* Hero Search */}
      <section className="bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h1 className="text-4xl font-bold text-[#0F172A] mb-4">Help Center</h1>
          <p className="text-gray-600 mb-8">Find answers to your questions</p>
          
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search for help..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none shadow-lg"
            />
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-[#0F172A] mb-8">Browse by Category</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {categories.map((category, index) => (
              <button
                key={index}
                className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all text-left group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-[#E9D5FF] flex items-center justify-center group-hover:bg-[#0F172A] transition-colors">
                    <category.Icon size={24} className="text-[#0F172A] group-hover:text-white transition-colors" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-[#0F172A]">{category.title}</h3>
                      <ChevronRight size={20} className="text-gray-400 group-hover:text-[#0F172A] transition-colors" />
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{category.description}</p>
                    <p className="text-xs text-gray-400 mt-2">{category.count} articles</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Articles */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-[#0F172A] mb-8">Popular Articles</h2>
          
          <div className="grid md:grid-cols-2 gap-4">
            {popularArticles.map((article, index) => (
              <button
                key={index}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-[#E9D5FF]/30 transition-all text-left"
              >
                <span className="text-[#0F172A] font-medium">{article}</span>
                <ChevronRight size={20} className="text-gray-400" />
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Contact CTA */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold text-[#0F172A] mb-4">Can't find what you're looking for?</h2>
          <p className="text-gray-600 mb-8">Our support team is here to help</p>
          <Link
            to="/contact"
            className="inline-flex items-center gap-2 px-8 py-4 bg-[#0F172A] text-white rounded-full font-semibold hover:bg-gray-800 transition-all"
          >
            Contact Support
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HelpCenterPage;
