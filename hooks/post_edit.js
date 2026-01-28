#!/usr/bin/env node
/**
 * POST-EDIT HOOK
 * Fires after Claude Code edits a file.
 * Records decision for persistence and runs quality checks.
 */

const { execSync } = require('child_process');
const path = require('path');

const PERSISTENCE_SCRIPT = path.join(__dirname, '..', 'coordination', 'session_persistence.py');

// Get file path from environment
const editedFile = process.env.CLAUDE_EDITED_FILE || 'unknown';

try {
    // Record the edit as a decision
    const decision = `Edited: ${editedFile}`;
    const rationale = process.env.CLAUDE_EDIT_RATIONALE || 'Code modification';

    execSync(
        `python3 "${PERSISTENCE_SCRIPT}" decision "${decision}" "${rationale}"`,
        { encoding: 'utf8' }
    );

    // Run type checking for TypeScript files
    if (editedFile.endsWith('.ts') || editedFile.endsWith('.tsx')) {
        try {
            execSync('npx tsc --noEmit 2>/dev/null || true', { encoding: 'utf8' });
        } catch (e) {
            // Type errors are informational, don't block
        }
    }

    // Run prettier for JS/TS files
    if (editedFile.match(/\.(js|jsx|ts|tsx)$/)) {
        try {
            execSync(`npx prettier --write "${editedFile}" 2>/dev/null || true`, { encoding: 'utf8' });
        } catch (e) {
            // Prettier failures are non-blocking
        }
    }

    process.exit(0);
} catch (error) {
    console.error('[SØWL] Post-edit hook failed:', error.message);
    process.exit(0);
}
