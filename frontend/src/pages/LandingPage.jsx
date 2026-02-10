import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function LandingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const rootRef = useRef(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    // Track if this effect is still current
    let isCurrent = true;

    // decide file
    let file = "/landing/index.html";
    if (location.pathname === "/stories") file = "/landing/stories/index.html";
    if (location.pathname === "/pricing") file = "/landing/pricing/index.html";
    if (location.pathname === "/blogs") file = "/landing/blogs/index.html";

    fetch(file)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP error: ${r.status}`);
        return r.text();
      })
      .then(html => {
        // Check if this effect is still current before updating DOM
        if (!isCurrent) return;

        // Use DOMParser to safely parse and clean HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        
        // Remove all script tags to prevent freeze
        const scripts = doc.querySelectorAll("script");
        scripts.forEach(script => script.remove());
        
        // Extract the body content (or full document if needed)
        const bodyContent = doc.body ? doc.body.innerHTML : doc.documentElement.innerHTML;
        root.innerHTML = bodyContent;

        // Handle navigation using event delegation
        const handleClick = (e) => {
          const link = e.target.closest("a[href]");
          if (link) {
            const href = link.getAttribute("href");
            if (href && href.startsWith("/")) {
              e.preventDefault();
              navigate(href);
            }
          }
        };

        root.addEventListener("click", handleClick);

        // Store cleanup function
        return () => {
          root.removeEventListener("click", handleClick);
        };
      })
      .catch(err => {
        if (!isCurrent) return;
        console.error("Failed to load landing page:", err);
        root.innerHTML = "<p>Could not load page</p>";
      });

    // Cleanup function to mark effect as stale
    return () => {
      isCurrent = false;
    };
  }, [location.pathname, navigate]);

  return <div id="landing-root" ref={rootRef}></div>;
}
