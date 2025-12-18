import { Link } from 'react-router-dom';
import { Heart, ArrowLeft, Users, Target, Sparkles, Shield } from 'lucide-react';

const AboutPage = () => {
  const values = [
    {
      Icon: Heart,
      title: 'Meaningful Connections',
      description: 'We believe in quality over quantity. Every feature is designed to foster genuine relationships.'
    },
    {
      Icon: Target,
      title: 'Intentional Design',
      description: 'No dark patterns, no endless scrolling. Every interaction encourages thoughtful engagement.'
    },
    {
      Icon: Shield,
      title: 'Safety First',
      description: 'Your safety and privacy are non-negotiable. We build trust through transparency.'
    },
    {
      Icon: Sparkles,
      title: 'Human-Centered',
      description: 'We put people before algorithms. Connection should feel natural, not manufactured.'
    }
  ];

  const team = [
    { name: 'Sarah Chen', role: 'CEO & Co-Founder', image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200' },
    { name: 'Michael Park', role: 'CTO & Co-Founder', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200' },
    { name: 'Emily Rodriguez', role: 'Head of Product', image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200' },
    { name: 'David Kim', role: 'Head of Safety', image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200' }
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
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

      {/* Hero */}
      <section className="bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-5xl font-bold text-[#0F172A] mb-6">About TrueBond</h1>
          <p className="text-xl text-gray-700 leading-relaxed">
            We're on a mission to bring people closer to love through meaningful, intentional connections. 
            Founded in 2024, TrueBond was born from the belief that dating should feel human again.
          </p>
        </div>
      </section>

      {/* Our Story */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-6">Our Story</h2>
          <div className="prose prose-lg max-w-none">
            <p className="text-gray-700 leading-relaxed mb-4">
              TrueBond started with a simple observation: modern dating apps were making people feel more lonely, not less. 
              The endless swiping, the superficial judgments, the ghosting — it all felt like a game where nobody wins.
            </p>
            <p className="text-gray-700 leading-relaxed mb-4">
              We asked ourselves: What if dating could be different? What if every interaction was intentional? 
              What if quality mattered more than quantity?
            </p>
            <p className="text-gray-700 leading-relaxed">
              That's why we created TrueBond — a platform where conversations come first, where every message matters, 
              and where real connections can grow at their own pace. No pressure, no noise, just genuine human connection.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-12 text-center">Our Values</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 rounded-full bg-[#E9D5FF] flex items-center justify-center mx-auto mb-4">
                  <value.Icon size={32} className="text-[#0F172A]" />
                </div>
                <h3 className="text-xl font-bold text-[#0F172A] mb-2">{value.title}</h3>
                <p className="text-gray-600">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-12 text-center">Our Team</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, index) => (
              <div key={index} className="text-center">
                <img
                  src={member.image}
                  alt={member.name}
                  className="w-32 h-32 rounded-full object-cover mx-auto mb-4 border-4 border-white shadow-lg"
                />
                <h3 className="text-lg font-bold text-[#0F172A]">{member.name}</h3>
                <p className="text-gray-600">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-20 bg-[#0F172A] text-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <p className="text-5xl font-bold mb-2">50K+</p>
              <p className="text-gray-400">Active Users</p>
            </div>
            <div>
              <p className="text-5xl font-bold mb-2">10K+</p>
              <p className="text-gray-400">Daily Conversations</p>
            </div>
            <div>
              <p className="text-5xl font-bold mb-2">67%</p>
              <p className="text-gray-400">Meet in Person</p>
            </div>
            <div>
              <p className="text-5xl font-bold mb-2">18 min</p>
              <p className="text-gray-400">Avg Conversation</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-4">Ready to Find Your Bond?</h2>
          <p className="text-gray-600 mb-8">Join thousands who are building meaningful connections.</p>
          <Link
            to="/signup"
            className="inline-flex items-center gap-2 px-8 py-4 bg-[#0F172A] text-white rounded-full font-semibold hover:bg-gray-800 transition-all"
          >
            Get Started Free
          </Link>
        </div>
      </section>
    </div>
  );
};

export default AboutPage;
