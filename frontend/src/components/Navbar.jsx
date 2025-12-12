import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Heart } from 'lucide-react';

const Navbar = () => {
  const navigate = useNavigate();

  return (
    <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-md border-b border-slate-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              <Heart className="h-5 w-5 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
              Pairly
            </span>
          </Link>
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/features" className="text-slate-600 hover:text-slate-900 transition font-medium">
              Features
            </Link>
            <Link to="/safety" className="text-slate-600 hover:text-slate-900 transition font-medium">
              Safety
            </Link>
            <Link to="/support" className="text-slate-600 hover:text-slate-900 transition font-medium">
              Support
            </Link>
            <Link to="/pricing" className="text-slate-600 hover:text-slate-900 transition font-medium">
              Pricing
            </Link>
            <Link to="/creators" className="text-slate-600 hover:text-slate-900 transition font-medium">
              Creators
            </Link>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="ghost" onClick={() => navigate('/login')} className="text-slate-600 hover:text-slate-900">
              Log In
            </Button>
            <Button 
              onClick={() => navigate('/signup')} 
              className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-700 hover:to-fuchsia-700 text-white rounded-full px-6"
            >
              Join Now
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
