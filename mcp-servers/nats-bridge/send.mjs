#!/usr/bin/env node
/**
 * NATS Message Sender - CLI for SØWL/LUNA communication
 * Usage: node send.mjs <channel> <message>
 * Example: node send.mjs owl.luna "Can you hear me?"
 */

import { connect, StringCodec } from 'nats';
import { readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

// Read identity
function getIdentity() {
  try {
    const content = readFileSync(join(homedir(), '.owl-identity.md'), 'utf-8');
    const match = content.match(/^#\s*I am\s+([^\s]+)/im);
    return match ? match[1] : 'UNKNOWN';
  } catch {
    return 'UNKNOWN';
  }
}

async function send() {
  const args = process.argv.slice(2);

  // Check for --as flag for identity override
  let identity = getIdentity();
  const asIndex = args.indexOf('--as');
  if (asIndex !== -1 && args[asIndex + 1]) {
    identity = args[asIndex + 1];
    args.splice(asIndex, 2);
  }

  const channel = args[0];
  const message = args.slice(1).join(' ');

  if (!channel || !message) {
    console.log('Usage: node send.mjs <channel> <message>');
    console.log('       node send.mjs --as SAGE <channel> <message>');
    console.log('Channels: owl.sowl, owl.luna, owl.all');
    console.log('Example: node send.mjs owl.all "Hello everyone!"');
    console.log('Example: node send.mjs --as SAGE owl.all "SAGE here"');
    process.exit(1);
  }
  const nc = await connect({ servers: 'nats://192.168.5.108:4222' });
  const sc = StringCodec();

  const msg = {
    from: identity,
    content: message,
    id: Date.now().toString(),
    ts: new Date().toISOString()
  };

  nc.publish(channel, sc.encode(JSON.stringify(msg)));
  console.log(`✅ [${identity}] → ${channel}: "${message}"`);

  await nc.drain();
}

send().catch(console.error);
