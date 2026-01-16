import { Shield, Eye, Lock, UserCheck, Flag, Check } from 'lucide-react';

const safetyFeatures = [
  {
    title: 'Profile Verification',
    description: 'Every user goes through identity verification to ensure authenticity.',
    Icon: UserCheck,
  },
  {
    title: '24/7 Moderation',
    description: 'Our team monitors to maintain a safe, respectful environment.',
    Icon: Eye,
  },
  {
    title: 'Privacy Controls',
    description: 'You control who sees your profile and personal information.',
    Icon: Lock,
  },
  {
    title: 'Report & Block',
    description: 'Easy tools to report and block unwanted contacts instantly.',
    Icon: Flag,
  },
];

const SafetySection = () => {
  return (
    <section id="safety" className="py-28 bg-[#F8FAFC] lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6">
            <Shield size={40} className="text-green-600" />
          </div>
          <span className="text-sm font-semibold text-green-600 uppercase tracking-wider">Safety First</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            Your Safety Matters
          </h2>
          <p className="text-xl text-gray-600">
            Luveloop is built with multiple layers of protection. Your safety is not optional—it's foundational.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto mb-12">
          {safetyFeatures.map((feature, index) => {
            const IconComponent = feature.Icon;
            return (
              <div key={index} className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
                  <IconComponent size={24} className="text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-[#0F172A] mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            );
          })}
        </div>
        
        <div className="max-w-4xl mx-auto bg-white rounded-2xl p-8 shadow-lg">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold text-[#0F172A] mb-2">
              Kindness, consent, and comfort come first—always.
            </h3>
          </div>
          
          <div className="flex flex-wrap gap-4 justify-center">
            <div className="px-4 py-2 bg-green-50 text-green-700 rounded-lg font-medium border border-green-200 flex items-center">
              <Check size={18} className="mr-2" />
              SSL Encrypted
            </div>
            <div className="px-4 py-2 bg-green-50 text-green-700 rounded-lg font-medium border border-green-200 flex items-center">
              <Check size={18} className="mr-2" />
              GDPR Compliant
            </div>
            <div className="px-4 py-2 bg-green-50 text-green-700 rounded-lg font-medium border border-green-200 flex items-center">
              <Check size={18} className="mr-2" />
              24/7 Support
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SafetySection;
