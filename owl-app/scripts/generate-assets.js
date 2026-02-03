#!/usr/bin/env node
/**
 * Asset Generator for OWL App
 *
 * This script creates placeholder PNG assets for the app.
 * In production, replace these with professionally designed assets.
 *
 * Run: node scripts/generate-assets.js
 */

const fs = require('fs');
const path = require('path');

// Simple 1x1 transparent PNG as base
const TRANSPARENT_1X1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64'
);

// Simple dark colored PNG (for icon/splash backgrounds)
const DARK_PIXEL = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNgYGD4HwABBAEAcv3YCQAAAABJRU5ErkJggg==',
  'base64'
);

const assetsDir = path.join(__dirname, '..', 'assets');

// Ensure assets directory exists
if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir, { recursive: true });
}

// Create placeholder files
const placeholders = [
  'icon.png',
  'splash.png',
  'adaptive-icon.png',
  'favicon.png'
];

placeholders.forEach(filename => {
  const filepath = path.join(assetsDir, filename);
  if (!fs.existsSync(filepath)) {
    fs.writeFileSync(filepath, DARK_PIXEL);
    console.log(`Created placeholder: ${filename}`);
  }
});

console.log('Asset placeholders created. Replace with real assets for production.');
