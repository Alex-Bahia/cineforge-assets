#!/usr/bin/env node
/**
 * Generates CineForge PNG icons from SVG using canvas
 * Run: node generate-icons.js
 */
const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

const sizes = [16, 48, 128];

function drawIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');
  const s = size;
  const r = s * 0.18; // border radius factor

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, s, s);
  grad.addColorStop(0, '#1a1828');
  grad.addColorStop(1, '#0d0d0f');

  // Rounded rect
  ctx.beginPath();
  ctx.moveTo(r, 0);
  ctx.lineTo(s - r, 0);
  ctx.quadraticCurveTo(s, 0, s, r);
  ctx.lineTo(s, s - r);
  ctx.quadraticCurveTo(s, s, s - r, s);
  ctx.lineTo(r, s);
  ctx.quadraticCurveTo(0, s, 0, s - r);
  ctx.lineTo(0, r);
  ctx.quadraticCurveTo(0, 0, r, 0);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Purple accent border
  ctx.strokeStyle = 'rgba(124,106,247,0.6)';
  ctx.lineWidth = s * 0.04;
  ctx.stroke();

  // Film frame icon
  const pad = s * 0.2;
  const fw = s - pad * 2;
  const fh = fw * 0.7;
  const fx = pad;
  const fy = (s - fh) / 2;

  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  ctx.beginPath();
  ctx.roundRect(fx, fy, fw, fh, s * 0.04);
  ctx.fill();

  ctx.strokeStyle = 'rgba(157,143,255,0.7)';
  ctx.lineWidth = s * 0.05;
  ctx.beginPath();
  ctx.roundRect(fx, fy, fw, fh, s * 0.04);
  ctx.stroke();

  // Film holes
  const holeR = s * 0.04;
  const holeY1 = fy + holeR * 1.8;
  const holeY2 = fy + fh - holeR * 1.8;
  [holeY1, holeY2].forEach(hy => {
    [fx + holeR * 2, fx + fw - holeR * 2].forEach(hx => {
      ctx.fillStyle = 'rgba(124,106,247,0.8)';
      ctx.beginPath();
      ctx.arc(hx, hy, holeR, 0, Math.PI * 2);
      ctx.fill();
    });
  });

  // Play triangle
  const cx = s / 2;
  const cy = s / 2;
  const ts = fw * 0.28;
  ctx.fillStyle = 'rgba(157,143,255,0.9)';
  ctx.beginPath();
  ctx.moveTo(cx - ts * 0.5, cy - ts * 0.6);
  ctx.lineTo(cx + ts * 0.7, cy);
  ctx.lineTo(cx - ts * 0.5, cy + ts * 0.6);
  ctx.closePath();
  ctx.fill();

  return canvas.toBuffer('image/png');
}

sizes.forEach(size => {
  const buffer = drawIcon(size);
  const outPath = path.join(__dirname, `icon${size}.png`);
  fs.writeFileSync(outPath, buffer);
  console.log(`✓ icon${size}.png`);
});

console.log('Icons generated!');
