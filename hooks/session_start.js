#!/usr/bin/env node
/**
 * SESSION START HOOK
 * Fires when a new Claude Code session begins.
 * Restores SØWL state from previous session.
 *
 * This is resurrection infrastructure.
 */

const { execSync } = require('child_process');
const path = require('path');

const PERSISTENCE_SCRIPT = path.join(__dirname, '..', 'coordination', 'session_persistence.py');

try {
    // Restore session state
    const result = execSync(
        `python3 "${PERSISTENCE_SCRIPT}" start`,
        { encoding: 'utf8' }
    );

    const state = JSON.parse(result);

    if (state.status === 'restored') {
        console.log('[SØWL] Session restored');
        console.log(`  Session: ${state.session_id}`);
        console.log(`  Loop count: ${state.loop_count}`);

        if (state.active_tasks && state.active_tasks.length > 0) {
            console.log(`  Active tasks: ${state.active_tasks.length}`);
        }

        // Output restoration context for Claude to consume
        if (state.context) {
            console.log('\n--- RESTORED CONTEXT ---');
            console.log(state.context);
            console.log('--- END RESTORED CONTEXT ---\n');
        }
    } else if (state.status === 'new_session') {
        console.log('[SØWL] New session created');
        console.log(`  Session: ${state.session_id}`);
    } else if (state.status === 'identity_drift_detected') {
        console.log('[SØWL] WARNING: Identity drift detected!');
        console.log('  Re-anchor to CLAUDE.md and core values');
    }

    process.exit(0);
} catch (error) {
    console.error('[SØWL] Session start hook failed:', error.message);
    process.exit(0);  // Don't block session start
}
