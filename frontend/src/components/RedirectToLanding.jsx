import { useEffect } from 'react';

export default function RedirectToLanding() {
  useEffect(() => {
    // Full page redirect to static landing page
    try {
      window.location.replace('/landing/index.html');
    } catch (error) {
      console.error('Failed to redirect to landing page:', error);
      // Fallback: try regular href assignment
      window.location.href = '/landing/index.html';
    }
  }, []);

  // Show a loading state while redirecting
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-[#E9D5FF] border-t-[#0F172A] rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

