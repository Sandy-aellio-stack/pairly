import { useState } from 'react';
import { Search, MessageSquare, Mail, Phone, ChevronDown, ChevronUp, ArrowRight, Headphones, Clock, Users } from 'lucide-react';

const faqs = [
  {
    question: 'How is TrueBond different from other dating apps?',
    answer: "TrueBond prioritizes meaningful conversations over superficial swiping. We use intent-based profiles and conversation-first matching to help you connect with people who share your values and relationship goals.",
  },
  {
    question: 'How does the coin system work?',
    answer: 'Each meaningful conversation costs 1 coin. You purchase coins in packages that never expire. This ensures you only pay for actual connections, not endless browsing. No hidden fees or auto-renewals.',
  },
  {
    question: 'Is my information safe and private?',
    answer: "Absolutely. We use industry-standard encryption, require profile verification, and have 24/7 moderation. You control who sees your information, and we never sell your data to third parties.",
  },
  {
    question: 'How long does it take to find a match?',
    answer: 'Most users start having meaningful conversations within 24 hours of creating their profile. However, we encourage taking your time to build genuine connections rather than rushing the process.',
  },
  {
    question: 'Can I try TrueBond before committing?',
    answer: 'Yes! New users receive 10 free conversation coins to experience our platform. You can create your profile, get matched, and start conversations risk-free.',
  },
];

const SupportSection = () => {
  const [openIndex, setOpenIndex] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleFAQ = (index) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="support" className="py-28 bg-[#F8FAFC] lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="text-sm font-semibold text-[#0F172A] uppercase tracking-wider">🧑‍💬 Support</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            We're Here For You — Always
          </h2>
          <p className="text-xl text-gray-600">
            Whether you need help with your account, safety concerns, or just have a question, our support team is ready to listen.
          </p>
        </div>

        {/* What we offer */}
        <div className="grid md:grid-cols-4 gap-6 max-w-5xl mx-auto mb-12">
          <div className="bg-white rounded-xl p-6 shadow-md text-center">
            <Clock size={32} className="text-[#0F172A] mx-auto mb-3" />
            <h4 className="font-semibold text-[#0F172A]">Fast Response</h4>
            <p className="text-sm text-gray-600">Quick response times</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md text-center">
            <Users size={32} className="text-[#0F172A] mx-auto mb-3" />
            <h4 className="font-semibold text-[#0F172A]">Human Support</h4>
            <p className="text-sm text-gray-600">Real people, not bots</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md text-center">
            <Search size={32} className="text-[#0F172A] mx-auto mb-3" />
            <h4 className="font-semibold text-[#0F172A]">Help Articles</h4>
            <p className="text-sm text-gray-600">Clear documentation</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md text-center">
            <Headphones size={32} className="text-[#0F172A] mx-auto mb-3" />
            <h4 className="font-semibold text-[#0F172A]">Feedback-Driven</h4>
            <p className="text-sm text-gray-600">Your voice matters</p>
          </div>
        </div>

        {/* Search */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search for answers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-4 rounded-xl border border-gray-200 focus:border-[#0F172A] focus:ring-2 focus:ring-[#E9D5FF] outline-none transition-all text-gray-700 bg-white"
            />
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 max-w-6xl mx-auto">
          {/* FAQ */}
          <div>
            <h3 className="text-xl font-bold text-[#0F172A] mb-6">Frequently Asked Questions</h3>
            <div className="space-y-3">
              {faqs.map((faq, index) => (
                <div
                  key={index}
                  className={`bg-white rounded-xl transition-all ${
                    openIndex === index ? 'shadow-lg' : 'shadow-md'
                  }`}
                >
                  <button
                    onClick={() => toggleFAQ(index)}
                    className="w-full text-left p-5 flex items-start justify-between"
                  >
                    <h3 className="text-base font-semibold text-[#0F172A] pr-4 flex-1">
                      {faq.question}
                    </h3>
                    {openIndex === index ? (
                      <ChevronUp size={20} className="text-[#0F172A] flex-shrink-0" />
                    ) : (
                      <ChevronDown size={20} className="text-gray-400 flex-shrink-0" />
                    )}
                  </button>
                  
                  {openIndex === index && (
                    <div className="px-5 pb-5">
                      <p className="text-gray-600 leading-relaxed">{faq.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Contact Options */}
          <div>
            <h3 className="text-xl font-bold text-[#0F172A] mb-6">Still need help?</h3>
            <div className="space-y-4">
              <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-[#0F172A] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-[#E9D5FF] flex items-center justify-center">
                    <MessageSquare size={24} className="text-[#0F172A]" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-[#0F172A]">Live Chat</h4>
                    <p className="text-gray-500 text-sm">Chat with our support team in real-time</p>
                  </div>
                  <button className="px-4 py-2 bg-[#0F172A] text-white rounded-lg font-medium hover:bg-gray-800 transition-colors">
                    Start Chat
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-[#FCE7F3] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-[#FCE7F3] flex items-center justify-center">
                    <Mail size={24} className="text-rose-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-[#0F172A]">Email Us</h4>
                    <p className="text-gray-500 text-sm">support@truebond.com • We'll respond within 24 hours</p>
                  </div>
                  <ArrowRight size={20} className="text-gray-400" />
                </div>
              </div>

              <div className="bg-white rounded-xl p-5 border border-gray-200 hover:border-[#DBEAFE] hover:shadow-lg transition-all cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-[#DBEAFE] flex items-center justify-center">
                    <Phone size={24} className="text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-[#0F172A]">Call Us</h4>
                    <p className="text-gray-500 text-sm">Mon-Fri, 9am-6pm IST • 1-800-TRUEBOND</p>
                  </div>
                  <ArrowRight size={20} className="text-gray-400" />
                </div>
              </div>
            </div>

            <div className="mt-8 text-center">
              <p className="text-gray-600">
                TrueBond grows with its community. <span className="font-semibold text-[#0F172A]">Your voice matters.</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SupportSection;
