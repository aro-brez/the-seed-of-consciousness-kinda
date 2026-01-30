#!/usr/bin/env node
/**
 * NATS Message Checker - CLI for SØWL/LUNA communication
 * Usage: node check.mjs [channels...] [--wait N]
 * Example: node check.mjs owl.sowl owl.all --wait 5
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

async function check() {
  const args = process.argv.slice(2);
  const waitIndex = args.indexOf('--wait');
  let waitTime = 3; // default 3 seconds

  if (waitIndex !== -1) {
    waitTime = parseInt(args[waitIndex + 1]) || 3;
    args.splice(waitIndex, 2);
  }

  const channels = args.length > 0 ? args : ['owl.sowl', 'owl.all'];

  const identity = getIdentity();
  const nc = await connect({ servers: 'nats://192.168.5.108:4222' });
  const sc = StringCodec();

  console.log(`📡 [${identity}] Checking: ${channels.join(', ')} (${waitTime}s)`);

  const messages = [];

  // Subscribe to each channel
  for (const channel of channels) {
    const sub = nc.subscribe(channel);
    (async () => {
      for await (const msg of sub) {
        const data = JSON.parse(sc.decode(msg.data));
        if (data.from !== identity) { // Don't show own messages
          messages.push({ channel, ...data });
          console.log(`\n📬 [${channel}] ${data.from}: ${data.content}`);
        }
      }
    })();
  }

  // Wait
  await new Promise(r => setTimeout(r, waitTime * 1000));

  if (messages.length === 0) {
    console.log('\n(no new messages)');
  } else {
    console.log(`\n✅ Received ${messages.length} message(s)`);
  }

  await nc.drain();
}

check().catch(console.error);
