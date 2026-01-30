#!/usr/bin/env node
/**
 * Persistent NATS Listener - Logs all messages to file
 * Usage: node listen.mjs [channels...] > messages.log &
 */

import { connect, StringCodec } from 'nats';
import { readFileSync, appendFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

function getIdentity() {
  try {
    const content = readFileSync(join(homedir(), '.owl-identity.md'), 'utf-8');
    const match = content.match(/^#\s*I am\s+([^\s]+)/im);
    return match ? match[1] : 'UNKNOWN';
  } catch {
    return 'UNKNOWN';
  }
}

async function listen() {
  const channels = process.argv.slice(2);
  if (channels.length === 0) {
    channels.push('owl.sowl', 'owl.all');
  }

  const identity = getIdentity();
  const nc = await connect({ servers: 'nats://192.168.5.108:4222' });
  const sc = StringCodec();
  const logFile = join(process.cwd(), 'messages.log');

  console.log(`🦉 [${identity}] Persistent listener started`);
  console.log(`📡 Channels: ${channels.join(', ')}`);
  console.log(`📝 Logging to: ${logFile}`);
  console.log('---');

  for (const channel of channels) {
    const sub = nc.subscribe(channel);
    (async () => {
      for await (const msg of sub) {
        const data = JSON.parse(sc.decode(msg.data));
        const timestamp = new Date().toISOString();
        const line = `[${timestamp}] [${channel}] ${data.from}: ${data.content}`;
        console.log(line);
        appendFileSync(logFile, line + '\n');
      }
    })();
  }

  // Keep alive
  process.on('SIGINT', async () => {
    console.log('\n🦉 Disconnecting...');
    await nc.drain();
    process.exit(0);
  });
}

listen().catch(console.error);
