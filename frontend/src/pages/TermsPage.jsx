import { Link } from 'react-router-dom';
import { Heart, ArrowLeft } from 'lucide-react';
import HeartCursor from '@/components/HeartCursor';

const TermsPage = () => {
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
            <span className="text-xl font-bold text-[#0F172A]">Luveloop</span>
          </Link>
          <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-[#0F172A]">
            <ArrowLeft size={20} />
            Back to Home
          </Link>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold text-[#0F172A] mb-4">Terms of Service</h1>
        <p className="text-gray-600 mb-8">Last updated: December 2024</p>

        <div className="prose prose-lg max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing or using Luveloop, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our platform. Luveloop is designed for individuals seeking meaningful, genuine connections.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">2. Eligibility</h2>
            <p className="text-gray-700 leading-relaxed">
              You must be at least 18 years old to use Luveloop. By using our service, you represent and warrant that you meet this age requirement and have the legal capacity to enter into these terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">3. Account Registration</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              To use Luveloop, you must create an account with accurate and complete information. You are responsible for:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Maintaining the confidentiality of your account credentials</li>
              <li>All activities that occur under your account</li>
              <li>Notifying us immediately of any unauthorized use</li>
              <li>Keeping your profile information accurate and up-to-date</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">4. Coin System & Payments</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              Luveloop uses a coin-based messaging system:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>1 Coin = 1 Message (conversation-first approach)</li>
              <li>₹1 = 1 Coin (simple pricing)</li>
              <li>Minimum purchase: 100 coins (₹100)</li>
              <li>Bulk discounts available for larger purchases</li>
              <li>New users receive 10 free coins upon signup</li>
              <li>Coins are non-refundable and non-transferable</li>
              <li>Unused coins never expire</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">5. User Conduct</h2>
            <p className="text-gray-700 leading-relaxed mb-4">
              Luveloop is built on trust and respect. Users must not:
            </p>
            <ul className="list-disc pl-6 text-gray-700 space-y-2">
              <li>Create fake or misleading profiles</li>
              <li>Harass, threaten, or abuse other users</li>
              <li>Share inappropriate or explicit content</li>
              <li>Spam or send unsolicited commercial messages</li>
              <li>Attempt to manipulate or exploit other users</li>
              <li>Use automated systems or bots</li>
              <li>Violate any applicable laws or regulations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">6. Safety & Moderation</h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to review, moderate, and remove any content or accounts that violate these terms. We may suspend or terminate accounts without notice for violations. Our 24/7 moderation team works to maintain a safe environment.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">7. Intellectual Property</h2>
            <p className="text-gray-700 leading-relaxed">
              Luveloop and its content, features, and functionality are owned by Luveloop and protected by intellectual property laws. You retain ownership of content you post but grant us a license to use it for operating the service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">8. Limitation of Liability</h2>
            <p className="text-gray-700 leading-relaxed">
              Luveloop is provided "as is" without warranties. We are not liable for any indirect, incidental, or consequential damages arising from your use of the platform. We do not guarantee matches or relationship outcomes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">9. Changes to Terms</h2>
            <p className="text-gray-700 leading-relaxed">
              We may update these terms from time to time. We will notify users of significant changes. Continued use of Luveloop after changes constitutes acceptance of the new terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-[#0F172A] mb-4">10. Contact Us</h2>
            <p className="text-gray-700 leading-relaxed">
              If you have questions about these Terms of Service, please contact us at:
              <br /><br />
              <strong>Email:</strong> legal@luveloop.com<br />
              <strong>Support:</strong> support@luveloop.com
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;
