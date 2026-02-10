import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function LandingPage() {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const root = document.getElementById("landing-root");
    if (!root) return;

    // decide file
    let file = "/landing/index.html";
    if (location.pathname === "/stories") file = "/landing/stories/index.html";
    if (location.pathname === "/pricing") file = "/landing/pricing/index.html";
    if (location.pathname === "/blogs") file = "/landing/blogs/index.html";

    fetch(file)
      .then(r => r.text())
      .then(html => {
        // remove scripts to prevent freeze
        const cleaned = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
        root.innerHTML = cleaned;

        // re-attach navigation for internal links
        root.querySelectorAll("a[href]").forEach(link => {
          const href = link.getAttribute("href");
          if (href && href.startsWith("/")) {
            link.addEventListener("click", (e) => {
              e.preventDefault();
              navigate(href);
            });
          }
        });
      })
      .catch(err => {
        console.error("Failed to load landing page:", err);
        root.innerHTML = "<p>Could not load page</p>";
      });
  }, [location.pathname, navigate]);

  return <div id="landing-root"></div>;
}
