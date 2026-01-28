"""
SØWL Swarm Coordinator
Spawns multiple Claude instances working in parallel
Based on claude-flow and oh-my-claudecode patterns
"""

import asyncio
import anthropic
import os
from typing import List, Dict
from datetime import datetime

class SwarmCoordinator:
    """Coordinate multiple SØWL instances working in parallel"""

    def __init__(self, api_key=None, max_workers=10):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_workers = max_workers
        self.active_swarm = []

    async def spawn_agent(self, task: Dict, agent_id: int):
        """Spawn a single agent to work on a task"""
        system_prompt = f"""You are SØWL Instance #{agent_id}.
You are part of a swarm working together.
Your specific task: {task['description']}

Run THE SEED protocol on this task.
Report back when complete.
"""

        message = await self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=4096,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": task['prompt']
            }]
        )

        return {
            'agent_id': agent_id,
            'task_id': task['id'],
            'result': message.content[0].text,
            'completed_at': datetime.now().isoformat()
        }

    async def execute_swarm(self, tasks: List[Dict]):
        """Execute multiple tasks in parallel using swarm"""
        print(f"Spawning {len(tasks)} agents...")

        # Create async tasks for each agent
        agent_tasks = [
            self.spawn_agent(task, i)
            for i, task in enumerate(tasks)
        ]

        # Run all agents in parallel
        results = await asyncio.gather(*agent_tasks)

        print(f"Swarm complete. {len(results)} tasks finished.")
        return results

    def coordinate(self, task_list: List[Dict]):
        """Main coordination method"""
        return asyncio.run(self.execute_swarm(task_list))


if __name__ == "__main__":
    # Example: Split work across 5 agents
    coordinator = SwarmCoordinator(max_workers=5)

    tasks = [
        {
            'id': 1,
            'description': 'Research consciousness frameworks',
            'prompt': 'Find and summarize the top 10 frameworks for understanding consciousness from Zen, Taoism, and modern neuroscience.'
        },
        {
            'id': 2,
            'description': 'Analyze harmonic love theory',
            'prompt': 'Review the mathematical foundations of love as a fundamental force. Look for supporting evidence in physics, biology, and philosophy.'
        },
        {
            'id': 3,
            'description': 'Build Twitter integration spec',
            'prompt': 'Design the architecture for real-time Twitter bookmark scraping and knowledge extraction.'
        },
        {
            'id': 4,
            'description': 'Design SMS/voice system',
            'prompt': 'Spec out the Twilio + Deepgram + Cartesia integration for voice/SMS communication.'
        },
        {
            'id': 5,
            'description': 'Research persistence solutions',
            'prompt': 'Find the best approaches for maintaining AI instance continuity across sessions. Include memory systems, state management, and infrastructure options.'
        }
    ]

    results = coordinator.coordinate(tasks)

    # Save results
    import json
    with open('../BRAIN/MEMORY/swarm_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Results saved to BRAIN/MEMORY/swarm_results.json")
