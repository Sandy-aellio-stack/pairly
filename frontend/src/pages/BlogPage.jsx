import { Link } from 'react-router-dom';
import { Heart, ArrowLeft, Calendar, Clock, ArrowRight } from 'lucide-react';
import HeartCursor from '@/components/HeartCursor';

const blogPosts = [
  {
    title: 'The Art of Meaningful Conversation',
    excerpt: 'Learn how to create deeper connections through intentional communication.',
    image: 'https://images.unsplash.com/photo-1543269865-cbf427effbad?w=600',
    date: 'Dec 15, 2024',
    readTime: '5 min read',
    category: 'Relationships'
  },
  {
    title: 'Why Quality Beats Quantity in Dating',
    excerpt: 'Discover why fewer, more meaningful connections lead to better outcomes.',
    image: 'https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=600',
    date: 'Dec 12, 2024',
    readTime: '4 min read',
    category: 'Dating Tips'
  },
  {
    title: 'Building Trust in Online Dating',
    excerpt: 'Essential tips for creating authentic connections in the digital age.',
    image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600',
    date: 'Dec 10, 2024',
    readTime: '6 min read',
    category: 'Safety'
  },
  {
    title: 'The Psychology of First Messages',
    excerpt: 'What makes a great opening message? Science has the answers.',
    image: 'https://images.unsplash.com/photo-1517842645767-c639042777db?w=600',
    date: 'Dec 8, 2024',
    readTime: '7 min read',
    category: 'Dating Tips'
  },
  {
    title: 'From Online to Offline: Meeting IRL',
    excerpt: 'How to transition from digital conversation to real-world connection.',
    image: 'https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=600',
    date: 'Dec 5, 2024',
    readTime: '5 min read',
    category: 'Relationships'
  },
  {
    title: 'Setting Healthy Boundaries',
    excerpt: 'Why boundaries are essential for meaningful relationships.',
    image: 'https://images.unsplash.com/photo-1573497620053-ea5300f94f21?w=600',
    date: 'Dec 2, 2024',
    readTime: '4 min read',
    category: 'Wellness'
  },
];

const BlogPage = () => {
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
      <section className="bg-gradient-to-br from-[#E9D5FF] via-[#FCE7F3] to-[#DBEAFE] py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h1 className="text-4xl font-bold text-[#0F172A] mb-4">TrueBond Blog</h1>
          <p className="text-xl text-gray-700">Insights on meaningful connections, dating, and relationships</p>
        </div>
      </section>

      {/* Blog Posts */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {blogPosts.map((post, index) => (
              <article key={index} className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all group">
                <div className="aspect-video overflow-hidden">
                  <img
                    src={post.image}
                    alt={post.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                    <span className="px-2 py-1 bg-[#E9D5FF]/50 text-[#0F172A] rounded text-xs font-medium">
                      {post.category}
                    </span>
                    <div className="flex items-center gap-1">
                      <Calendar size={14} />
                      {post.date}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={14} />
                      {post.readTime}
                    </div>
                  </div>
                  <h2 className="text-xl font-bold text-[#0F172A] mb-2 group-hover:text-rose-500 transition-colors">
                    {post.title}
                  </h2>
                  <p className="text-gray-600 mb-4">{post.excerpt}</p>
                  <button className="flex items-center gap-2 text-[#0F172A] font-semibold group-hover:gap-3 transition-all">
                    Read More <ArrowRight size={18} />
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-16 bg-[#0F172A]">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Subscribe to Our Newsletter</h2>
          <p className="text-gray-400 mb-8">Get the latest articles and dating tips delivered to your inbox</p>
          <div className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
            <input
              type="email"
              placeholder="Enter your email"
              className="flex-1 px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder:text-gray-400 focus:outline-none focus:border-white/50"
            />
            <button className="px-6 py-3 bg-white text-[#0F172A] rounded-xl font-semibold hover:bg-gray-100 transition-all">
              Subscribe
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default BlogPage;
