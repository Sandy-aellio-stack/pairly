import { useEffect } from 'react';

export default function RedirectToLanding() {
  useEffect(() => {
    // Full page redirect to static landing page
    window.location.replace('/landing/index.html');
  }, []);

  return null;
}
