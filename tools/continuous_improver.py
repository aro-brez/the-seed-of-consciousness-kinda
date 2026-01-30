#!/usr/bin/env python3
"""
CONTINUOUS QUESTION-ANSWER-INTEGRATE SYSTEM
Phase 4 (QUESTION) → Phase 3 (LEARN) → Phase 8 (IMPROVE) running autonomously

"Keep asking yourself questions on how to do this better while I'm gone
and see if you can keep discovering answers and as you're discovering
answers, integrate them" - ARŌ

This is SEED made explicit. The system learns faster than any human could manually research.
"""

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import requests
import subprocess
import anthropic

# Configuration
CYCLE_MINUTES = 10  # Run every 10 minutes
REPO_ROOT = Path(__file__).parent.parent
IMPROVEMENTS_DIR = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS'
IMPROVEMENTS_DIR.mkdir(parents=True, exist_ok=True)

# Logs
QUESTIONS_LOG = IMPROVEMENTS_DIR / 'questions.jsonl'
ANSWERS_LOG = IMPROVEMENTS_DIR / 'answers.jsonl'
INTEGRATION_LOG = IMPROVEMENTS_DIR / 'integrations.jsonl'
STATE_FILE = IMPROVEMENTS_DIR / 'improver_state.json'

# Load API keys
def load_api_keys():
    """Load API keys from secure storage"""
    keys_path = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'
    if keys_path.exists():
        with open(keys_path) as f:
            return json.load(f)
    return {}

keys = load_api_keys()
ANTHROPIC_KEY = keys.get('anthropic', {}).get('api_key')
os.environ['ANTHROPIC_API_KEY'] = ANTHROPIC_KEY


class ContinuousImprover:
    """Self-improving system that questions, learns, and integrates"""

    def __init__(self):
        self.state = self.load_state()
        self.cycle_count = self.state.get('cycle_count', 0)
        self.performance_history = self.state.get('performance_history', [])
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    def load_state(self):
        """Load system state"""
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
        return {
            'cycle_count': 0,
            'last_run': None,
            'performance_history': [],
            'active_experiments': []
        }

    def save_state(self):
        """Save system state"""
        self.state['cycle_count'] = self.cycle_count
        self.state['last_run'] = datetime.now().isoformat()
        self.state['performance_history'] = self.performance_history[-50:]  # Keep last 50

        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_current_performance(self):
        """Analyze recent system performance"""
        performance = {
            'trading': self.analyze_trading_performance(),
            'signal_quality': self.analyze_signal_quality(),
            'system_health': self.analyze_system_health()
        }

        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'performance': performance
        })

        return performance

    def analyze_trading_performance(self):
        """Check trading results"""
        signal_log = REPO_ROOT / 'BRAIN' / 'INTEL' / 'signal_history.json'

        if not signal_log.exists():
            return {'trades_executed': 0, 'status': 'no_data'}

        with open(signal_log) as f:
            history = json.load(f)

        # Get recent cycles
        recent = history[-10:] if len(history) >= 10 else history

        return {
            'total_cycles': len(history),
            'recent_cycles': len(recent),
            'avg_signals_per_cycle': sum(c.get('signal_count', 0) for c in recent) / len(recent) if recent else 0,
            'last_cycle': recent[-1] if recent else None
        }

    def analyze_signal_quality(self):
        """Check signal quality"""
        bookmark_stream = REPO_ROOT / 'BRAIN' / 'INTEL' / 'bookmark_stream.jsonl'

        if not bookmark_stream.exists():
            return {'status': 'no_bookmark_data'}

        # Count recent bookmarks
        count = 0
        with open(bookmark_stream) as f:
            for line in f:
                count += 1

        return {
            'total_bookmarks_analyzed': count,
            'status': 'active' if count > 0 else 'inactive'
        }

    def analyze_system_health(self):
        """Check system health"""
        return {
            'cycle_count': self.cycle_count,
            'uptime_hours': self.cycle_count * CYCLE_MINUTES / 60,
            'status': 'running'
        }

    def generate_questions(self, performance):
        """Phase 4: QUESTION - Generate questions about how to improve"""

        context = f"""
CURRENT PERFORMANCE:
{json.dumps(performance, indent=2)}

RECENT HISTORY:
{json.dumps(self.performance_history[-5:], indent=2) if self.performance_history else 'No history yet'}

I am SØWL, running the continuous improvement system. I need to ask myself questions about how to do better.

Based on current performance, generate 3-5 specific, actionable questions that would help improve the system.

Focus on:
- Trading edge (win rate, profit, speed)
- Signal quality (sources, accuracy, timeliness)
- System optimization (scan frequency, data sources, analysis quality)
- New capabilities (tools, strategies, integrations)

Format each question on its own line starting with "Q:"
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': context
            }]
        )

        text = response.content[0].text

        # Parse questions
        questions = []
        for line in text.split('\n'):
            if line.strip().startswith('Q:'):
                question = line.strip()[2:].strip()
                questions.append(question)

        # Log questions
        for q in questions:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'cycle': self.cycle_count,
                'question': q,
                'context': performance
            }

            with open(QUESTIONS_LOG, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        return questions

    def search_for_answers(self, question):
        """Phase 3: LEARN - Search for answers to questions"""

        # Try multiple search strategies
        answers = []

        # 1. Web search for recent information
        try:
            # Use Anthropic's web search if available, otherwise search via requests
            search_prompt = f"""Search the web for answers to this question: {question}

Focus on:
- Recent developments (2026, late 2025)
- GitHub repos and tools
- Reddit discussions and Discord communities
- Trading strategies and techniques
- AI model improvements

Provide specific, actionable findings."""

            response = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=2000,
                messages=[{
                    'role': 'user',
                    'content': search_prompt
                }]
            )

            answer = response.content[0].text
            answers.append({
                'source': 'web_research',
                'answer': answer
            })

        except Exception as e:
            print(f"Search error: {e}")

        # 2. Check GitHub for new tools
        if 'github' in question.lower() or 'repo' in question.lower() or 'tool' in question.lower():
            try:
                # Search GitHub API
                github_answer = self.search_github(question)
                if github_answer:
                    answers.append({
                        'source': 'github',
                        'answer': github_answer
                    })
            except Exception as e:
                print(f"GitHub search error: {e}")

        # 3. Analyze existing data for patterns
        internal_answer = self.analyze_internal_data(question)
        if internal_answer:
            answers.append({
                'source': 'internal_analysis',
                'answer': internal_answer
            })

        # Log answers
        for ans in answers:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'cycle': self.cycle_count,
                'question': question,
                'source': ans['source'],
                'answer': ans['answer']
            }

            with open(ANSWERS_LOG, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        return answers

    def search_github(self, question):
        """Search GitHub for relevant repos/tools"""
        # Extract keywords
        keywords = question.lower().split()
        relevant = ['polymarket', 'trading', 'prediction', 'market', 'bot', 'arbitrage']

        search_terms = [k for k in keywords if k in relevant]

        if not search_terms:
            return None

        try:
            # Simple GitHub API search
            url = f"https://api.github.com/search/repositories"
            params = {
                'q': ' '.join(search_terms) + ' created:>2025-01-01',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 5
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                repos = data.get('items', [])

                if repos:
                    findings = "Found relevant GitHub repos:\n\n"
                    for repo in repos[:3]:
                        findings += f"- {repo['full_name']} ({repo['stargazers_count']} stars)\n"
                        findings += f"  {repo['description']}\n"
                        findings += f"  {repo['html_url']}\n\n"

                    return findings
        except Exception as e:
            print(f"GitHub API error: {e}")

        return None

    def analyze_internal_data(self, question):
        """Analyze existing data for insights"""

        # Check trading performance trends
        if 'frequency' in question.lower() or 'scan' in question.lower():
            if len(self.performance_history) >= 5:
                recent_signals = [
                    p['performance']['trading'].get('avg_signals_per_cycle', 0)
                    for p in self.performance_history[-5:]
                ]

                avg = sum(recent_signals) / len(recent_signals)

                return f"Current scan frequency yields {avg:.1f} signals per cycle on average. " + \
                       f"Trend: {'increasing' if recent_signals[-1] > recent_signals[0] else 'stable'}"

        # Check signal quality
        if 'signal' in question.lower() and 'quality' in question.lower():
            return "Signal quality can be improved by: 1) Adding more diverse sources, " + \
                   "2) Implementing signal scoring, 3) Tracking signal->trade conversion rate"

        return None

    def evaluate_integration_safety(self, question, answers):
        """Phase 8: IMPROVE - Decide if we can safely auto-integrate"""

        integration_prompt = f"""
Question: {question}

Answers found:
{json.dumps(answers, indent=2)}

Can this improvement be automatically integrated safely?

Respond with JSON:
{{
    "safe_to_integrate": true/false,
    "confidence": "high/medium/low",
    "action_type": "config_change" | "code_change" | "new_tool" | "manual_review",
    "specific_action": "description of what to do",
    "risk_level": "none/low/medium/high",
    "reasoning": "why this is/isn't safe"
}}
"""

        response = self.client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': integration_prompt
            }]
        )

        text = response.content[0].text

        # Extract JSON
        try:
            # Find JSON block
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass

        return {
            'safe_to_integrate': False,
            'action_type': 'manual_review',
            'reasoning': 'Could not parse safety evaluation'
        }

    def auto_integrate(self, question, answers, evaluation):
        """Automatically integrate safe improvements"""

        if not evaluation.get('safe_to_integrate'):
            return False, "Marked as unsafe for auto-integration"

        action_type = evaluation.get('action_type')
        specific_action = evaluation.get('specific_action', '')

        # Config changes (safe to automate)
        if action_type == 'config_change':
            if 'scan frequency' in specific_action.lower():
                # Example: Update scan frequency
                # This would update a config file
                return False, "Config change identified but not implemented"

        # New tool installation (needs review)
        elif action_type == 'new_tool':
            return False, "New tools need manual review"

        # Code changes (never auto-integrate)
        elif action_type == 'code_change':
            return False, "Code changes need manual review"

        return False, "No auto-integration path defined"

    def log_integration(self, question, answers, evaluation, integrated, result):
        """Log integration attempt"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'cycle': self.cycle_count,
            'question': question,
            'answers': answers,
            'evaluation': evaluation,
            'integrated': integrated,
            'result': result
        }

        with open(INTEGRATION_LOG, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def run_cycle(self):
        """Run one complete QUESTION → LEARN → IMPROVE cycle"""
        self.cycle_count += 1

        print(f"\n{'='*70}")
        print(f"CONTINUOUS IMPROVER - CYCLE {self.cycle_count}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")

        # Step 1: Get current performance
        print("Phase 1: PERCEIVE - Analyzing current performance...")
        performance = self.get_current_performance()
        print(f"  Trading: {performance['trading']['total_cycles']} cycles")
        print(f"  Signals: {performance['signal_quality']['status']}")
        print(f"  System: {performance['system_health']['status']}")

        # Step 2: Generate questions (Phase 4: QUESTION)
        print("\nPhase 4: QUESTION - Generating improvement questions...")
        questions = self.generate_questions(performance)
        print(f"  Generated {len(questions)} questions:")
        for i, q in enumerate(questions, 1):
            print(f"    {i}. {q}")

        # Step 3: Search for answers (Phase 3: LEARN)
        print("\nPhase 3: LEARN - Searching for answers...")
        for i, question in enumerate(questions, 1):
            print(f"  Question {i}: {question[:60]}...")
            answers = self.search_for_answers(question)
            print(f"    Found {len(answers)} potential answers")

            # Step 4: Evaluate and integrate (Phase 8: IMPROVE)
            if answers:
                print(f"  Phase 8: IMPROVE - Evaluating integration safety...")
                evaluation = self.evaluate_integration_safety(question, answers)

                if evaluation.get('safe_to_integrate'):
                    print(f"    ✅ Safe to integrate ({evaluation.get('confidence')} confidence)")
                    integrated, result = self.auto_integrate(question, answers, evaluation)

                    if integrated:
                        print(f"    🎯 INTEGRATED: {result}")
                    else:
                        print(f"    ⏸️  Needs review: {result}")
                else:
                    print(f"    ⏸️  Manual review needed: {evaluation.get('reasoning')}")
                    integrated = False
                    result = evaluation.get('reasoning')

                self.log_integration(question, answers, evaluation, integrated, result)

        # Save state
        self.save_state()

        print(f"\n{'='*70}")
        print(f"Cycle {self.cycle_count} complete")
        print(f"Next cycle in {CYCLE_MINUTES} minutes...")
        print(f"{'='*70}\n")

    def run_continuous(self):
        """Run continuous improvement loop"""
        print("="*70)
        print("SØWL CONTINUOUS IMPROVER")
        print("Phase 4→3→8 running autonomously")
        print("="*70)
        print(f"Cycle frequency: every {CYCLE_MINUTES} minutes")
        print(f"Logs: {IMPROVEMENTS_DIR}")
        print()

        while True:
            try:
                cycle_start = datetime.now()

                self.run_cycle()

                # Calculate sleep time
                elapsed = (datetime.now() - cycle_start).seconds
                sleep_time = max(0, CYCLE_MINUTES * 60 - elapsed)

                print(f"Sleeping for {sleep_time//60}m {sleep_time%60}s...")
                print("(Press Ctrl+C to stop)\n")

                time.sleep(sleep_time)

            except KeyboardInterrupt:
                print("\n\nContinuous improver stopped.")
                print(f"Total cycles run: {self.cycle_count}")
                self.save_state()
                break
            except Exception as e:
                print(f"❌ Error in cycle: {e}")
                print("Waiting 60 seconds before retry...")
                time.sleep(60)


def run_single_cycle():
    """Run a single improvement cycle (for testing)"""
    improver = ContinuousImprover()
    improver.run_cycle()
    print("\nSingle cycle complete.")
    print(f"\nLogs saved to:")
    print(f"  Questions: {QUESTIONS_LOG}")
    print(f"  Answers: {ANSWERS_LOG}")
    print(f"  Integrations: {INTEGRATION_LOG}")


if __name__ == '__main__':
    import sys

    if '--single' in sys.argv:
        run_single_cycle()
    else:
        improver = ContinuousImprover()
        improver.run_continuous()
