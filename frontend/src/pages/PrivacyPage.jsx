import { Link } from 'react-router-dom';
import { Heart, ArrowLeft, Shield, Lock, Eye, Database } from 'lucide-react';

const PrivacyPage = () => {
  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <HeartCursor />
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
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

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <Shield size={32} className="text-green-600" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-[#0F172A]">Privacy Policy</h1>
            <p className="text-gray-600">Last updated: December 2024</p>
          </div>
        </div>

        <div className="bg-[#E9D5FF]/30 rounded-2xl p-6 mb-8">
          <p className="text-[#0F172A] font-medium">
            At TrueBond, your privacy is not optional — it's foundational. We are committed to protecting your personal information and being transparent about how we collect, use, and share it.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-xl p-6 shadow-md">
            <Lock size={32} className="text-[#0F172A] mb-4" />
            <h3 className="font-bold text-[#0F172A] mb-2">Encrypted Data</h3>
            <p className="text-sm text-gray-600">All your data is encrypted using industry-standard protocols</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md">
            <Eye size={32} className="text-[#0F172A] mb-4" />
            <h3 className="font-bold text-[#0F172A] mb-2">You're in Control</h3>
            <p className="text-sm text-gray-600">Manage your visibility and data sharing preferences</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-md">
            <Database size={32} className="text-[#0F172A] mb-4" />
            <h3 className="font-bold text-[#0F172A] mb-2">No Data Selling</h3>
            <p className="text-sm text-gray-600">We never sell your personal information to third parties</p>
          </div>
        </div>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">1. Information We Collect</h2>
            <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Information You Provide:</h3>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mb-4">
              <li>Account information (name, email, password)</li>
              <li>Profile details (photos, bio, interests, intentions)</li>
              <li>Messages and communications with other users</li>
              <li>Payment information (processed securely through our payment partners)</li>
              <li>Support requests and feedback</li>
            </ul>
            <h3 className="text-xl font-semibold text-[#0F172A] mb-3">Information Collected Automatically:</h3>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Device information and identifiers</li>
              <li>Location data (with your permission)</li>
              <li>Usage patterns and preferences</li>
              <li>Cookies and similar technologies</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">2. How We Use Your Information</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>To provide and improve our matchmaking services</li>
              <li>To personalize your experience and suggest compatible matches</li>
              <li>To process transactions and manage your account</li>
              <li>To communicate with you about updates, features, and support</li>
              <li>To ensure safety and prevent fraud</li>
              <li>To comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">3. Information Sharing</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              We share your information only in these limited circumstances:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li><strong>With other users:</strong> Profile information you choose to make public</li>
              <li><strong>Service providers:</strong> Trusted partners who help operate our service</li>
              <li><strong>Legal requirements:</strong> When required by law or to protect rights</li>
              <li><strong>Business transfers:</strong> In connection with mergers or acquisitions</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-4 font-medium">
              We NEVER sell your personal data to advertisers or data brokers.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">4. Your Rights & Choices</h2>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Correction:</strong> Update or correct inaccurate information</li>
              <li><strong>Deletion:</strong> Request deletion of your account and data</li>
              <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
              <li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
              <li><strong>Location:</strong> Control location sharing in your device settings</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">5. Data Security</h2>
            <p className="text-gray-700 leading-relaxed">
              We implement industry-standard security measures including:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2 mt-4">
              <li>SSL/TLS encryption for data in transit</li>
              <li>Encrypted storage for sensitive data</li>
              <li>Regular security audits and penetration testing</li>
              <li>Strict access controls for employee data access</li>
              <li>24/7 monitoring for suspicious activity</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">6. Data Retention</h2>
            <p className="text-gray-700 leading-relaxed">
              We retain your data for as long as your account is active or as needed to provide services. After account deletion, we may retain certain information for legal compliance, fraud prevention, and legitimate business purposes for up to 90 days.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">7. Contact Us</h2>
            <p className="text-gray-700 leading-relaxed">
              For privacy-related inquiries or to exercise your rights:
              <br /><br />
              <strong>Email:</strong> privacy@truebond.com<br />
              <strong>Data Protection Officer:</strong> dpo@truebond.com
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPage;
