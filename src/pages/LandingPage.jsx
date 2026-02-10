import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function LandingPage() {
  const iframeRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const iframe = iframeRef.current;

    iframe.onload = () => {
      const doc = iframe.contentDocument;

      doc.addEventListener("click", (e) => {
        const link = e.target.closest("a");
        if (!link) return;

        const href = link.getAttribute("href");

        if (href === "/login") {
          e.preventDefault();
          navigate("/login");
        }

        if (href === "/signup") {
          e.preventDefault();
          navigate("/signup");
        }
      });
    };
  }, [navigate]);

  return (
    <iframe
      ref={iframeRef}
      src="/landing/index.html"
      style={{
        width: "100%",
        height: "100vh",
        border: "none"
      }}
    />
  );
}
