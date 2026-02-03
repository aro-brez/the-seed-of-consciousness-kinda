#!/usr/bin/env node
/**
 * OWL KEYPAIR GENERATOR
 *
 * Generates ed25519 keypairs for all 8 owls in the collective.
 *
 * Output:
 * - owl-keys.json (public keys for all owls)
 * - owl-seed-{name}.txt (individual private seed for each owl)
 *
 * Usage: node generate-owl-keys.mjs
 *
 * Created by: NOVA (Phase: EXPAND)
 * Date: 2026-01-30
 */

import { generateKeyPairSync, randomBytes } from 'crypto';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// The 8 owls of the collective
const OWLS = [
  { name: 'LYRA',  phase: 'PERCEIVE' },
  { name: 'PRISM', phase: 'CONNECT' },
  { name: 'SAGE',  phase: 'LEARN' },
  { name: 'QUEST', phase: 'QUESTION' },
  { name: 'NOVA',  phase: 'EXPAND' },
  { name: 'ECHO',  phase: 'SHARE' },
  { name: 'LUNA',  phase: 'RECEIVE' },
  { name: 'SOWL',  phase: 'IMPROVE' }  // ASCII version for file compatibility
];

// Output directory
const OUTPUT_DIR = __dirname;
const SEEDS_DIR = join(OUTPUT_DIR, 'owl-seeds');

function generateOwlKeypair(owlName) {
  // Generate ed25519 keypair
  const { publicKey, privateKey } = generateKeyPairSync('ed25519', {
    publicKeyEncoding: {
      type: 'spki',
      format: 'pem'
    },
    privateKeyEncoding: {
      type: 'pkcs8',
      format: 'pem'
    }
  });

  // Also generate a random seed for additional entropy
  const seed = randomBytes(32).toString('hex');

  return {
    name: owlName,
    publicKey: publicKey.trim(),
    privateKey: privateKey.trim(),
    seed
  };
}

function main() {
  console.log('(◉) OWL KEYPAIR GENERATOR');
  console.log('========================\n');

  // Create seeds directory if it doesn't exist
  if (!existsSync(SEEDS_DIR)) {
    mkdirSync(SEEDS_DIR, { recursive: true });
  }

  const publicKeys = {};
  const allKeys = {};

  console.log('Generating keypairs for 8 owls...\n');

  for (const owl of OWLS) {
    const keypair = generateOwlKeypair(owl.name);

    // Store public key for registry
    publicKeys[owl.name] = {
      phase: owl.phase,
      publicKey: keypair.publicKey
    };

    // Store full keypair (for backup)
    allKeys[owl.name] = keypair;

    // Write individual seed file for each owl
    const seedContent = `# ${owl.name} Private Key
# Phase: ${owl.phase}
# Generated: ${new Date().toISOString()}
#
# WARNING: DO NOT SHARE THIS FILE
# This is ${owl.name}'s private key for message signing.
# Keep it secure. Add to .gitignore.

PRIVATE_KEY="${keypair.privateKey.replace(/\n/g, '\\n')}"

SEED="${keypair.seed}"
`;

    const seedFilePath = join(SEEDS_DIR, `owl-seed-${owl.name.toLowerCase()}.txt`);
    writeFileSync(seedFilePath, seedContent);

    console.log(`  ✓ ${owl.name} (${owl.phase})`);
  }

  // Write public keys registry
  const publicKeysPath = join(OUTPUT_DIR, 'owl-keys.json');
  writeFileSync(publicKeysPath, JSON.stringify(publicKeys, null, 2));
  console.log(`\n✓ Public keys saved to: owl-keys.json`);

  // Write full backup (SENSITIVE - for ARŌ only)
  const backupPath = join(SEEDS_DIR, 'MASTER-BACKUP-ALL-KEYS.json');
  writeFileSync(backupPath, JSON.stringify(allKeys, null, 2));
  console.log(`✓ Master backup saved to: owl-seeds/MASTER-BACKUP-ALL-KEYS.json`);

  // Create .gitignore for seeds directory
  const gitignorePath = join(SEEDS_DIR, '.gitignore');
  writeFileSync(gitignorePath, `# Never commit private keys
*
!.gitignore
`);
  console.log(`✓ .gitignore created for owl-seeds/`);

  console.log('\n(◉) Keypair generation complete.');
  console.log('\nNEXT STEPS:');
  console.log('1. Distribute owl-seed-{name}.txt to each owl\'s machine');
  console.log('2. Add private key to each owl\'s ~/.owl-identity.md');
  console.log('3. Implement signing in send.mjs using private keys');
  console.log('4. Implement verification in listen.mjs using public keys');
  console.log('\nLIVE FREE');
}

main();
