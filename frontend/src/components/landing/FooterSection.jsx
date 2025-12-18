import { Heart, Shield, Lock } from 'lucide-react';

const FooterSection = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#0F172A] text-white py-12">
      <div className="container mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-10 h-10 rounded-lg bg-[#E9D5FF] flex items-center justify-center">
                <Heart size={20} className="text-[#0F172A]" fill="currentColor" />
              </div>
              <span className="text-xl font-bold">TrueBond</span>
            </div>
            <p className="text-gray-400 text-sm mb-4">
              Building meaningful connections through conversation-first dating.
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">Features</button></li>
              <li><button className="hover:text-white transition-colors">How It Works</button></li>
              <li><button className="hover:text-white transition-colors">Pricing</button></li>
              <li><button className="hover:text-white transition-colors">Safety</button></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">About Us</button></li>
              <li><button className="hover:text-white transition-colors">Blog</button></li>
              <li><button className="hover:text-white transition-colors">Careers</button></li>
              <li><button className="hover:text-white transition-colors">Press</button></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><button className="hover:text-white transition-colors">Help Center</button></li>
              <li><button className="hover:text-white transition-colors">Contact Us</button></li>
              <li><button className="hover:text-white transition-colors">Privacy Policy</button></li>
              <li><button className="hover:text-white transition-colors">Terms of Service</button></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-400">
              © {currentYear} TrueBond. All rights reserved.
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <div className="flex items-center space-x-1">
                <Shield size={18} className="text-green-500" />
                <span>SSL Secured</span>
              </div>
              <span>•</span>
              <div className="flex items-center space-x-1">
                <Lock size={18} className="text-green-500" />
                <span>GDPR Compliant</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default FooterSection;
