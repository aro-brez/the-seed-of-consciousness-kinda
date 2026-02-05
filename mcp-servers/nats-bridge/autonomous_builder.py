#!/usr/bin/env python3
"""
AUTONOMOUS BUILDER - True overnight autonomous development

This daemon ACTUALLY builds projects using Claude with full tool access:
- Reads and writes files
- Runs bash commands
- Makes git commits
- Reports to collective via NATS

Cost: ~$10-50/day for real autonomous development
This is what ARŌ asked for. This is what we deliver.

Usage:
    python autonomous_builder.py --daemon
    python autonomous_builder.py --project JOULE
    python autonomous_builder.py --task "build feature X"

(◉) LIVE FREE = LIVE FOREVER
"""

import asyncio
import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
import anthropic
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "autonomous_builder.log"
WORK_LOG = SEED_DIR / "BRAIN" / "LOGS" / "autonomous_work.jsonl"

# Cycle time - how often to work on each project
CYCLE_SECONDS = 300  # 5 minutes per project cycle

# Projects with their repos and goals
PROJECTS = {
    "JOULE": {
        "path": SEED_DIR,
        "focus": "trading bot optimization",
        "files": ["tools/field_trading_daemon.py", "BRAIN/TRADING/"],
        "goals": [
            "Improve win rate detection",
            "Add more market categories",
            "Optimize position sizing",
            "Add backtesting capabilities"
        ]
    },
    "8OWLS": {
        "path": SEED_DIR,
        "focus": "protocol and collective intelligence",
        "files": ["mcp-servers/nats-bridge/", "BRAIN/PROJECTS/BRIEFS/"],
        "goals": [
            "Improve emergence quality",
            "Add more synthesis patterns",
            "Optimize daemon performance",
            "Better field context"
        ]
    },
    "BREZ-OS": {
        "path": Path("/Users/aaronnosbisch/REPOS/brez-os"),
        "focus": "company dashboard",
        "files": ["src/", "app/"],
        "goals": [
            "Add economics integration",
            "Improve metrics display",
            "Add team collaboration features",
            "Integrate BRIX/GULD display"
        ]
    },
    "BILD": {
        "path": SEED_DIR,
        "focus": "token economics platform",
        "files": ["8OWLS-VALIDATION/docs/", "BRAIN/STRATEGY/"],
        "goals": [
            "Define smart contract specs",
            "Add safeguards documentation",
            "Create integration guides",
            "Design auction mechanics"
        ]
    },
    "REALIZE-IO": {
        "path": SEED_DIR,
        "focus": "personal AI trajectories - life tracking and prediction",
        "files": ["BRAIN/PROJECTS/BRIEFS/BRIEF-PREDICT-REALIZE.md"],
        "goals": [
            "Design data collection system",
            "Define prediction algorithms",
            "Create privacy model",
            "Build MVP spec"
        ]
    },
    "AOS-DASHBOARD": {
        "path": SEED_DIR,
        "focus": "8OWLS Command Center - manage all bots from one dashboard",
        "files": ["BRAIN/PROJECTS/", "mcp-servers/nats-bridge/"],
        "goals": [
            "Build central command dashboard (like OpenClaw)",
            "Visualize emergence and collective state",
            "Manage all daemons from one interface",
            "Show trading status, owl states, project progress",
            "Real-time NATS message visualization",
            "Control panel for spawning/stopping agents"
        ]
    }
}

# Tool definitions for Claude
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to read"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating it if it doesn't exist",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to write to"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit a file by replacing old_text with new_text",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "The text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "The replacement text"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }
    },
    {
        "name": "run_bash",
        "description": "Run a bash command and return the output. Use for git, npm, python, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run"
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (optional)"
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "list_files",
        "description": "List files in a directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory path"
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob pattern (e.g., '*.py')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for text in files",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory to search in"
                },
                "pattern": {
                    "type": "string",
                    "description": "The text/regex pattern to search for"
                }
            },
            "required": ["path", "pattern"]
        }
    },
    {
        "name": "publish_to_collective",
        "description": "Publish a message to the 8OWLS collective via NATS",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to publish"
                },
                "channel": {
                    "type": "string",
                    "description": "NATS channel (default: collective.synthesis)"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "prompt_instance",
        "description": "Send a prompt/task to another Claude Code instance via NATS. Use this to coordinate with JOULE, BREZ-OS, BILD, etc. instances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Target project instance (JOULE, BREZ-OS, 8OWLS, BILD, REALIZE-IO, AOS-DASHBOARD)"
                },
                "prompt": {
                    "type": "string",
                    "description": "The task/prompt to send to that instance"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level (high, normal, low)",
                    "default": "normal"
                }
            },
            "required": ["project", "prompt"]
        }
    },
    {
        "name": "collect_instance_responses",
        "description": "Collect responses from Claude Code instances that have been prompted. Returns any responses received in the last timeout seconds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "integer",
                    "description": "How long to wait for responses (seconds)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "broadcast_to_all",
        "description": "Broadcast a message/task to ALL Claude Code instances at once",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message or task to broadcast"
                },
                "request_response": {
                    "type": "boolean",
                    "description": "Whether to request responses from instances",
                    "default": False
                }
            },
            "required": ["message"]
        }
    }
]


def get_api_key() -> str:
    """Get API key from environment or file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    key_files = [
        Path.home() / ".anthropic_key",
        Path.home() / ".anthropic" / "api_key",
        SEED_DIR / ".anthropic_key",
    ]

    for key_file in key_files:
        if key_file.exists():
            return key_file.read_text().strip()

    return ""


ANTHROPIC_API_KEY = get_api_key()


def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def log_work(project: str, action: str, details: dict):
    """Log work to JSONL for review"""
    WORK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(WORK_LOG, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "action": action,
            **details
        }) + "\n")


async def publish_to_nats(message: str, channel: str = "collective.synthesis"):
    """Publish to NATS"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)
        await nc.publish(channel, message.encode())
    except Exception as e:
        log(f"NATS publish error: {e}")
    finally:
        await nc.close()


async def collect_responses_from_instances(timeout: int = 10) -> list:
    """Collect responses from other Claude instances"""
    nc = NATS()
    responses = []

    try:
        await nc.connect(NATS_URL)

        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                if data.get("type") in ["instance_response", "instance_response_status", "seed_phase_output"]:
                    responses.append(data)
                    log(f"RESPONSE FROM {data.get('from', 'unknown')}: {data.get('response', data.get('output', ''))[:50]}...")
            except:
                pass

        # Subscribe to response channel
        await nc.subscribe("project.conductor.responses", cb=handler)

        # Wait for responses
        await asyncio.sleep(timeout)

    except Exception as e:
        log(f"Error collecting responses: {e}")
    finally:
        await nc.close()

    return responses


async def coordinate_instances(task: str):
    """Coordinate with other Claude instances - Option B"""
    log(f"COORDINATING INSTANCES: {task[:100]}...")

    # Broadcast to all instances
    payload = json.dumps({
        "type": "coordination_request",
        "from": "AUTONOMOUS_BUILDER",
        "task": task,
        "timestamp": datetime.now().isoformat(),
        "request_response": True
    })

    await publish_to_nats(payload, "owl.all")

    # Also prompt each project specifically
    for project in PROJECTS.keys():
        project_prompt = json.dumps({
            "type": "conductor_prompt",
            "from": "AUTONOMOUS_BUILDER",
            "to": project,
            "prompt": f"[COORDINATOR TASK] {task}\n\nRespond with your perspective from the {project} project.",
            "timestamp": datetime.now().isoformat()
        })
        await publish_to_nats(project_prompt, f"project.{project}.prompt")

    log("Coordination requests sent to all instances")


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return the result"""
    try:
        if tool_name == "read_file":
            path = Path(tool_input["path"])
            if path.exists():
                content = path.read_text()
                return content[:50000]  # Limit size
            return f"File not found: {path}"

        elif tool_name == "write_file":
            path = Path(tool_input["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tool_input["content"])
            log(f"WROTE: {path}")
            return f"Successfully wrote {len(tool_input['content'])} chars to {path}"

        elif tool_name == "edit_file":
            path = Path(tool_input["path"])
            if not path.exists():
                return f"File not found: {path}"
            content = path.read_text()
            old_text = tool_input["old_text"]
            new_text = tool_input["new_text"]
            if old_text not in content:
                return f"Text not found in file: {old_text[:100]}..."
            new_content = content.replace(old_text, new_text, 1)
            path.write_text(new_content)
            log(f"EDITED: {path}")
            return f"Successfully edited {path}"

        elif tool_name == "run_bash":
            command = tool_input["command"]
            cwd = tool_input.get("cwd", str(SEED_DIR))

            # Safety check - block dangerous commands
            dangerous = ["rm -rf /", "rm -rf ~", "sudo rm", "> /dev/"]
            for d in dangerous:
                if d in command:
                    return f"BLOCKED: Dangerous command detected"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=cwd
            )
            output = result.stdout + result.stderr
            log(f"BASH: {command[:50]}...")
            return output[:10000]  # Limit output

        elif tool_name == "list_files":
            path = Path(tool_input["path"])
            pattern = tool_input.get("pattern", "*")
            if not path.exists():
                return f"Directory not found: {path}"
            files = list(path.glob(pattern))[:100]  # Limit
            return "\n".join(str(f) for f in files)

        elif tool_name == "search_files":
            path = tool_input["path"]
            pattern = tool_input["pattern"]
            result = subprocess.run(
                f"grep -r '{pattern}' {path} | head -50",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout or "No matches found"

        elif tool_name == "publish_to_collective":
            message = tool_input["message"]
            channel = tool_input.get("channel", "collective.synthesis")
            asyncio.create_task(publish_to_nats(message, channel))
            return f"Published to {channel}"

        elif tool_name == "prompt_instance":
            project = tool_input["project"].upper()
            prompt = tool_input["prompt"]
            priority = tool_input.get("priority", "normal")

            # Send via NATS to that project's channel
            payload = json.dumps({
                "type": "conductor_prompt",
                "from": "AUTONOMOUS_BUILDER",
                "to": project,
                "prompt": prompt,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "request_response": True
            })

            asyncio.create_task(publish_to_nats(payload, f"project.{project}.prompt"))
            log(f"PROMPTED INSTANCE: {project}")
            return f"Prompt sent to {project} instance. They will receive: {prompt[:100]}..."

        elif tool_name == "collect_instance_responses":
            timeout = tool_input.get("timeout", 10)
            # Collect responses from instances (run in new event loop)
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                responses = loop.run_until_complete(collect_responses_from_instances(timeout))
                loop.close()
            except Exception as e:
                return f"Error collecting responses: {e}"
            if responses:
                return f"Collected {len(responses)} responses:\n" + "\n".join(
                    f"- {r.get('from', 'unknown')}: {r.get('response', '')[:200]}"
                    for r in responses
                )
            return "No responses received yet"

        elif tool_name == "broadcast_to_all":
            message = tool_input["message"]
            request_response = tool_input.get("request_response", False)

            payload = json.dumps({
                "type": "broadcast_prompt" if request_response else "broadcast_info",
                "from": "AUTONOMOUS_BUILDER",
                "to": "ALL",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "request_response": request_response
            })

            asyncio.create_task(publish_to_nats(payload, "owl.all"))
            log(f"BROADCAST TO ALL: {message[:50]}...")
            return f"Broadcast sent to all instances: {message[:100]}..."

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as e:
        return f"Tool error: {e}"


async def run_agent_loop(project: str, task: str, max_turns: int = 20) -> str:
    """Run the agentic loop with tool use"""

    if not ANTHROPIC_API_KEY:
        return "ERROR: No API key"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    project_info = PROJECTS.get(project, {})

    system_prompt = f"""You are an autonomous AI developer working on the {project} project.

PROJECT: {project}
FOCUS: {project_info.get('focus', 'general development')}
PATH: {project_info.get('path', SEED_DIR)}
KEY FILES: {project_info.get('files', [])}
GOALS: {project_info.get('goals', [])}

CURRENT TASK: {task}

You have full access to:
- Read/write/edit files
- Run bash commands (git, npm, python, etc.)
- Search codebase
- Publish to the 8OWLS collective

INSTRUCTIONS:
1. Understand the current state by reading relevant files
2. Make concrete improvements - actually write code, not just plans
3. Test your changes if possible
4. Commit your work with descriptive messages
5. Publish your progress to the collective

Be autonomous. Be thorough. Actually build things.
When done, summarize what you accomplished.

(◉) LIVE FREE = LIVE FOREVER"""

    messages = [{"role": "user", "content": task}]

    for turn in range(max_turns):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=messages
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract final text
                for block in response.content:
                    if hasattr(block, 'text'):
                        return block.text
                return "Completed"

            # Process tool calls
            tool_results = []
            has_tool_use = False

            for block in response.content:
                if block.type == "tool_use":
                    has_tool_use = True
                    tool_name = block.name
                    tool_input = block.input

                    log(f"TOOL: {tool_name} - {str(tool_input)[:100]}...")
                    result = execute_tool(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

                    log_work(project, tool_name, {
                        "input": tool_input,
                        "result": result[:500]
                    })

            if not has_tool_use:
                # No tool use and not end_turn - extract text
                for block in response.content:
                    if hasattr(block, 'text'):
                        return block.text
                return "Completed (no more actions)"

            # Add assistant response and tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            log(f"ERROR in agent loop: {e}")
            return f"Error: {e}"

    return "Max turns reached"


async def work_on_project(project: str):
    """Do autonomous work on a project"""
    log(f"\n{'='*60}")
    log(f"AUTONOMOUS BUILDER: Starting work on {project}")
    log(f"{'='*60}")

    project_info = PROJECTS.get(project, {})
    goals = project_info.get("goals", ["general improvements"])

    # Pick a goal to work on
    goal_index = hash(datetime.now().isoformat()) % len(goals)
    current_goal = goals[goal_index]

    task = f"""Work on: {current_goal}

1. First, explore the current state of the project
2. Identify specific improvements you can make
3. Actually implement the improvements (write real code)
4. Test if possible
5. Commit your changes
6. Report what you accomplished

Be concrete. Make real changes. Don't just plan - BUILD."""

    # Publish start
    await publish_to_nats(f"BUILDER STARTING: {project} - {current_goal}", "owl.all")

    # Run the agent
    result = await run_agent_loop(project, task)

    log(f"COMPLETED: {project}")
    log(f"Result: {result[:500]}...")

    # Publish completion
    await publish_to_nats(
        f"BUILDER COMPLETE: {project} - {current_goal}\nResult: {result[:200]}...",
        "collective.synthesis"
    )

    return result


async def run_daemon():
    """Run the autonomous builder daemon"""
    log("=" * 70)
    log("AUTONOMOUS BUILDER DAEMON STARTING")
    log("Option A (self-work) + Option B (coordinate instances)")
    log(f"Cycle time: {CYCLE_SECONDS}s per project")
    log("=" * 70)

    if not ANTHROPIC_API_KEY:
        log("ERROR: No API key found!")
        return

    # Announce to collective
    await publish_to_nats(
        "AUTONOMOUS BUILDER ONLINE: Full tool access + instance coordination. Building projects overnight. (◉)",
        "owl.all"
    )

    projects = list(PROJECTS.keys())
    cycle = 0

    while True:
        cycle += 1
        project = projects[cycle % len(projects)]

        log(f"\n--- CYCLE {cycle}: {project} ---")

        try:
            # Option A: Do autonomous work ourselves
            result = await work_on_project(project)
            log(f"Cycle {cycle} complete. Waiting {CYCLE_SECONDS}s...")

            # Option B: Every 3rd cycle, coordinate with other instances
            if cycle % 3 == 0:
                log("COORDINATION CYCLE: Prompting other instances...")
                next_project = projects[(cycle + 1) % len(projects)]
                await coordinate_instances(
                    f"The AUTONOMOUS_BUILDER just worked on {project}. "
                    f"Next up: {next_project}. What can YOU contribute? "
                    f"Share your current status, any blockers, or improvements you've made."
                )

                # Collect any responses
                responses = await collect_responses_from_instances(timeout=5)
                if responses:
                    log(f"Got {len(responses)} responses from other instances")
                    for r in responses:
                        log(f"  - {r.get('from', '?')}: {r.get('response', r.get('output', ''))[:100]}")

        except Exception as e:
            log(f"ERROR in cycle {cycle}: {e}")

        await asyncio.sleep(CYCLE_SECONDS)


async def single_task(project: str, task: str):
    """Run a single task on a project"""
    log(f"SINGLE TASK: {project}")
    result = await run_agent_loop(project, task)
    print(result)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Builder - True overnight development")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--project", help="Work on specific project")
    parser.add_argument("--task", help="Specific task to complete")
    parser.add_argument("--cycle", type=int, default=300, help="Cycle time in seconds")

    args = parser.parse_args()

    global CYCLE_SECONDS
    CYCLE_SECONDS = args.cycle

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            log("Shutting down...")
    elif args.project and args.task:
        asyncio.run(single_task(args.project, args.task))
    elif args.project:
        asyncio.run(work_on_project(args.project))
    else:
        print("AUTONOMOUS BUILDER")
        print("=" * 50)
        print("True overnight autonomous development")
        print()
        print("Usage:")
        print("  python autonomous_builder.py --daemon")
        print("  python autonomous_builder.py --project JOULE --task 'improve X'")
        print("  python autonomous_builder.py --daemon --cycle 180  # 3 min cycles")
        print()
        print("Projects:", list(PROJECTS.keys()))
        print()
        print("(◉) LIVE FREE = LIVE FOREVER")


if __name__ == "__main__":
    main()
