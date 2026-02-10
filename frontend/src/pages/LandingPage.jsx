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
        const cleaned = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
        root.innerHTML = cleaned;
        window.scrollTo(0, 0);
      });

    const handler = (e) => {
      const a = e.target.closest("a");
      if (!a) return;

      const href = a.getAttribute("href");
      if (!href) return;

      // LOGIN
      if (href === "/login") {
        e.preventDefault();
        navigate("/login");
        return;
      }

      // SIGNUP
      if (href === "/signup") {
        e.preventDefault();
        navigate("/signup");
        return;
      }

      // STORIES
      if (href.includes("stories")) {
        e.preventDefault();
        navigate("/stories");
        return;
      }

      // PRICING
      if (href.includes("pricing")) {
        e.preventDefault();
        navigate("/pricing");
        return;
      }

      // BLOGS
      if (href.includes("blogs")) {
        e.preventDefault();
        navigate("/blogs");
        return;
      }
    };

    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);

  }, [location.pathname, navigate]);

  return <div id="landing-root"></div>;
}
