import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/landing/index.html")
      .then(res => res.text())
      .then(html => {
        const root = document.getElementById("landing-root");
        root.innerHTML = html;
      });

    // GLOBAL CLICK INTERCEPTOR
    const handler = (e) => {
      const link = e.target.closest("a, button");
      if (!link) return;

      const text = link.innerText?.toLowerCase() || "";

      // GET STARTED BUTTON
      if (text.includes("get start")) {
        e.preventDefault();
        navigate("/login");
      }

      // SIGNUP BUTTON
      if (text.includes("sign up")) {
        e.preventDefault();
        navigate("/signup");
      }

      const href = link.getAttribute("href");
      if (!href) return;

      if (href.startsWith("/login")) {
        e.preventDefault();
        navigate("/login");
      }

      if (href.startsWith("/signup")) {
        e.preventDefault();
        navigate("/signup");
      }
    };

    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [navigate]);

  return <div id="landing-root"></div>;
}
