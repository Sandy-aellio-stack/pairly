import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function LandingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const root = document.getElementById("landing-root");
    if (!root) return;

    // prevent stacking + freeze
    root.innerHTML = "";

    fetch("app.html")
      .then(res => res.text())
      .then(html => {
        root.innerHTML = html;

        // remove heavy inline scripts that cause freeze
        root.querySelectorAll("script").forEach(s => s.remove());

        // scroll reset
        window.scrollTo(0, 0);
      });

    const clickHandler = (e) => {
      const link = e.target.closest("a");
      if (!link) return;

      const href = link.getAttribute("href") || "";

      // LOGIN
      if (href.includes("/login")) {
        e.preventDefault();
        navigate("/login");
        return;
      }

      // SIGNUP
      if (href.includes("/signup")) {
        e.preventDefault();
        navigate("/signup");
        return;
      }

      // LOGO → HOME
      if (href === "/" || link.innerText.toLowerCase().includes("luveloop")) {
        e.preventDefault();
        navigate("/");
        return;
      }
    };

    document.addEventListener("click", clickHandler);

    return () => {
      document.removeEventListener("click", clickHandler);
    };
  }, [location.pathname, navigate]);

  return <div id="landing-root"></div>;
}
