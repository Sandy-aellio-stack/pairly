const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// Serve static files from the website-export directory
app.use(express.static(path.join(__dirname, 'frontend', 'website-export')));

// Handle all routes by serving index.html (for SPA-like behavior)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'website-export', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Landing page server running at http://localhost:${PORT}`);
});
