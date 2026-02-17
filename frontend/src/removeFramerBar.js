function killFramerBar() {
  const ids = [
    "__framer-editorbar-container",
    "__framer-editorbar",
    "__framer-editorbar-label",
    "__framer-editorbar-button",
  ];

  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.remove();
  });

  document
    .querySelectorAll('[id*="framer-editorbar"]')
    .forEach(el => el.remove());
}

// run repeatedly because Framer reinjects it
setInterval(killFramerBar, 500);
window.addEventListener("load", killFramerBar);
document.addEventListener("DOMContentLoaded", killFramerBar);
