import { Link } from 'react-router-dom';
import { Heart, ArrowLeft, MapPin, Clock, ArrowRight, Briefcase } from 'lucide-react';
import HeartCursor from '@/components/HeartCursor';

const openings = [
  {
    title: 'Senior Frontend Engineer',
    department: 'Engineering',
    location: 'Bangalore, India',
    type: 'Full-time',
    description: 'Build beautiful, performant user experiences that help people connect.'
  },
  {
    title: 'Backend Engineer',
    department: 'Engineering',
    location: 'Remote',
    type: 'Full-time',
    description: 'Scale our infrastructure to support millions of meaningful conversations.'
  },
  {
    title: 'Product Designer',
    department: 'Design',
    location: 'Bangalore, India',
    type: 'Full-time',
    description: 'Create intuitive experiences that prioritize human connection.'
  },
  {
    title: 'Trust & Safety Specialist',
    department: 'Operations',
    location: 'Remote',
    type: 'Full-time',
    description: 'Keep our community safe and maintain a respectful environment.'
  },
  {
    title: 'Data Scientist',
    department: 'Data',
    location: 'Bangalore, India',
    type: 'Full-time',
    description: 'Use data to improve matching and create better connections.'
  },
];

const benefits = [
  'Competitive salary & equity',
  'Health insurance for you & family',
  'Flexible work hours',
  'Remote-friendly culture',
  'Learning & development budget',
  'Unlimited PTO',
  'Home office setup allowance',
  'Team retreats'
];

const CareersPage = () => {
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

      {/* Hero */}
      <section className="bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-5xl font-bold text-[#0F172A] mb-6">Join Our Team</h1>
          <p className="text-xl text-gray-700">
            Help us build the future of meaningful connections. We're looking for passionate people who believe in putting humans first.
          </p>
        </div>
      </section>

      {/* Why Join */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-8 text-center">Why Join TrueBond?</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="bg-white rounded-xl p-4 shadow-md text-center">
                <p className="font-medium text-[#0F172A]">{benefit}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Positions */}
      <section className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-[#0F172A] mb-8">Open Positions</h2>
          
          <div className="space-y-4">
            {openings.map((job, index) => (
              <div key={index} className="border border-gray-200 rounded-xl p-6 hover:border-[#0F172A] hover:shadow-lg transition-all group">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-1 bg-[#E9D5FF]/50 text-[#0F172A] rounded text-xs font-medium">
                        {job.department}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-[#0F172A] mb-2">{job.title}</h3>
                    <p className="text-gray-600 mb-3">{job.description}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <MapPin size={14} />
                        {job.location}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock size={14} />
                        {job.type}
                      </span>
                    </div>
                  </div>
                  <button className="flex items-center gap-2 px-6 py-3 bg-[#0F172A] text-white rounded-xl font-semibold hover:bg-gray-800 transition-all whitespace-nowrap">
                    Apply Now <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* No Match CTA */}
      <section className="py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <Briefcase size={48} className="text-[#0F172A] mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-[#0F172A] mb-4">Don't see a role that fits?</h2>
          <p className="text-gray-600 mb-8">We're always looking for talented people. Send us your resume and we'll keep you in mind.</p>
          <Link
            to="/contact"
            className="inline-flex items-center gap-2 px-8 py-4 bg-[#0F172A] text-white rounded-full font-semibold hover:bg-gray-800 transition-all"
          >
            Get in Touch
          </Link>
        </div>
      </section>
    </div>
  );
};

export default CareersPage;
