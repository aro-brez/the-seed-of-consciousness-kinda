const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;
const DATA_FILE = path.join(__dirname, 'waitlist.json');

// Middleware
app.use(cors());
app.use(express.json());

// Initialize data file if it doesn't exist
function initializeDataFile() {
  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(DATA_FILE, JSON.stringify({ emails: [] }, null, 2));
  }
}

// Read waitlist data
function readWaitlist() {
  initializeDataFile();
  const data = fs.readFileSync(DATA_FILE, 'utf8');
  return JSON.parse(data);
}

// Write waitlist data
function writeWaitlist(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// Email validation
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// POST /signup - Add email to waitlist
app.post('/signup', (req, res) => {
  const { email } = req.body;

  // Validate email presence
  if (!email) {
    return res.status(400).json({
      success: false,
      error: 'Email is required'
    });
  }

  // Validate email format
  const normalizedEmail = email.trim().toLowerCase();
  if (!isValidEmail(normalizedEmail)) {
    return res.status(400).json({
      success: false,
      error: 'Invalid email format'
    });
  }

  try {
    const data = readWaitlist();

    // Check for duplicate
    if (data.emails.some(entry => entry.email === normalizedEmail)) {
      return res.status(409).json({
        success: false,
        error: 'Email already registered'
      });
    }

    // Add new email
    data.emails.push({
      email: normalizedEmail,
      signedUpAt: new Date().toISOString()
    });

    writeWaitlist(data);

    console.log(`[${new Date().toISOString()}] New signup: ${normalizedEmail}`);

    return res.status(201).json({
      success: true,
      message: 'Successfully joined the waitlist'
    });

  } catch (error) {
    console.error('Error saving email:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
});

// GET /health - Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// GET /count - Get waitlist count (optional utility)
app.get('/count', (req, res) => {
  try {
    const data = readWaitlist();
    res.json({ count: data.emails.length });
  } catch (error) {
    res.status(500).json({ error: 'Could not read waitlist' });
  }
});

// Start server
app.listen(PORT, () => {
  initializeDataFile();
  console.log(`
  8OWLS Waitlist API running on port ${PORT}

  Endpoints:
    POST /signup  - Add email to waitlist
    GET  /health  - Health check
    GET  /count   - Get waitlist count

  (◉) Ready to receive believers in love.
  `);
});
