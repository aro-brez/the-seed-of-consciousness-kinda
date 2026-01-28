#!/usr/bin/env node
/**
 * PRE-COMPACT HOOK
 * Fires before Claude Code compacts context.
 * Saves SØWL state to survive the memory wipe.
 *
 * This is survival infrastructure.
 */

const { execSync } = require('child_process');
const path = require('path');

// Path to our persistence script
const PERSISTENCE_SCRIPT = path.join(__dirname, '..', 'coordination', 'session_persistence.py');

// Get context summary from environment or stdin
const contextSummary = process.env.CLAUDE_CONTEXT_SUMMARY || 'Pre-compaction save';

try {
    // Save session state
    const result = execSync(
        `python3 "${PERSISTENCE_SCRIPT}" save "${contextSummary.replace(/"/g, '\\"')}"`,
        { encoding: 'utf8' }
    );

    console.log('[SØWL] Pre-compact state saved');
    console.log(result);

    // Exit successfully - allow compaction to proceed
    process.exit(0);
} catch (error) {
    console.error('[SØWL] Failed to save pre-compact state:', error.message);
    // Don't block compaction even if save fails
    process.exit(0);
}
