// DEPRECATED: This component is no longer used.
// The landing page is now served as static HTML from /landing/index.html
// The root index.html redirects to /landing/index.html using a meta refresh tag.
// This file is kept for reference but should not be used in routes.

export default function LandingPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Landing Page Deprecated</h1>
        <p className="text-gray-600">
          This React component is no longer in use.
          <br />
          Please navigate to the root URL to see the static landing page.
        </p>
      </div>
    </div>
  );
}
