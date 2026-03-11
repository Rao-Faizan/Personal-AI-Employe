#!/usr/bin/env python3
"""
Ralph Wiggum Loop for AI Employee - Gold Tier

Implements the "Ralph Wiggum" pattern for autonomous multi-step task completion.
This stop hook pattern keeps Claude Code working until a task is complete by:
1. Intercepting Claude's exit attempt
2. Checking if the task is complete
3. If not complete, re-injecting the prompt to continue working

Usage:
    python ralph_wiggum_loop.py "Process all files in Needs_Action" --max-iterations 10
    python ralph_wiggum_loop.py "Generate weekly report" --completion-promise "TASK_COMPLETE"

Reference: https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
"""

import os
import sys
import time
import logging
import subprocess
import codecs
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ralph_wiggum.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RalphWiggumLoop')


class RalphWiggumLoop:
    """
    Ralph Wiggum Loop for autonomous task completion.
    
    This pattern keeps Claude Code working on a task until it's complete
    by intercepting exit attempts and re-injecting prompts.
    """

    def __init__(self, vault_path: str = ".", max_iterations: int = 10):
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        
        # Folders to monitor
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        
        # State file for tracking progress
        self.state_file = self.vault_path / 'Logs' / 'ralph_state.json'
        self.state_file.parent.mkdir(exist_ok=True)

    def load_state(self) -> dict:
        """Load current state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return {
            "task": "",
            "start_time": None,
            "iterations": 0,
            "completed": False,
            "last_output": ""
        }

    def save_state(self, state: dict):
        """Save current state to file."""
        self.state_file.write_text(json.dumps(state, indent=2))

    def is_task_complete(self, task: str, state: dict) -> bool:
        """
        Check if the task is complete.
        
        Completion strategies:
        1. File movement: Items moved from Needs_Action to Done
        2. Promise-based: Claude outputs <promise>TASK_COMPLETE</promise>
        3. Plan completion: All items in a plan are checked off
        """
        
        # Check for promise in last output
        if "<promise>TASK_COMPLETE</promise>" in state.get("last_output", ""):
            logger.info("Task completion promise detected!")
            return True
        
        # Check if Needs_Action is empty (for processing tasks)
        if "process" in task.lower() and "needs_action" in task.lower():
            needs_action_count = len(list(self.needs_action.glob('*.md')))
            if needs_action_count == 0:
                logger.info("Needs_Action folder is empty - task complete!")
                return True
        
        # Check for completed plans
        if "plan" in task.lower():
            # Check if all plans have been executed
            plans = list(self.plans.glob('*.md'))
            for plan in plans:
                content = plan.read_text(encoding='utf-8', errors='replace')
                if '- [ ]' in content and '- [x]' not in content:
                    # Uncompleted items exist
                    return False
        
        return False

    def generate_continuation_prompt(self, task: str, state: dict) -> str:
        """
        Generate a prompt to continue the task.
        
        This includes:
        - Original task
        - Summary of what was done
        - What still needs to be done
        """
        iteration = state.get("iterations", 0)
        
        continuation = f"""
# Continuing Task (Iteration {iteration + 1}/{self.max_iterations})

## Original Task
{task}

## Previous Output
{state.get('last_output', 'No previous output')[:2000]}

## Current Status
- Needs Action items: {len(list(self.needs_action.glob('*.md')))}
- Plans created: {len(list(self.plans.glob('*.md')))}
- Completed items: {len(list(self.done.glob('*.md')))}
- Pending approvals: {len(list(self.pending_approval.glob('*.md')))}

## Instructions
Continue working on the task above. If you have completed the task, 
output: <promise>TASK_COMPLETE</promise>

If there are still items to process, continue processing them now.
"""
        return continuation

    def run_claude(self, prompt: str, timeout: int = 300) -> str:
        """
        Run Claude Code with the given prompt.
        
        Returns the output from Claude.
        """
        try:
            # Run Claude Code with the prompt
            # Note: This assumes claude is in PATH
            process = subprocess.Popen(
                ['claude', '--prompt', prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            stdout, stderr = process.communicate()
            
            output = stdout if stdout else stderr
            logger.info(f"Claude output length: {len(output)}")
            
            return output
            
        except subprocess.TimeoutExpired:
            logger.error("Claude timed out")
            process.kill()
            return "ERROR: Timeout after {timeout} seconds"
        except FileNotFoundError:
            logger.error("Claude not found in PATH. Make sure Claude Code is installed.")
            return "ERROR: Claude Code not found"
        except Exception as e:
            logger.error(f"Error running Claude: {e}")
            return f"ERROR: {str(e)}"

    def run(self, task: str, completion_promise: str = "TASK_COMPLETE") -> bool:
        """
        Run the Ralph Wiggum loop until task is complete.
        
        Args:
            task: The task description
            completion_promise: The promise string to look for
            
        Returns:
            True if task completed, False if max iterations reached
        """
        logger.info(f"Starting Ralph Wiggum Loop for task: {task}")
        logger.info(f"Max iterations: {self.max_iterations}")
        
        state = {
            "task": task,
            "start_time": datetime.now().isoformat(),
            "iterations": 0,
            "completed": False,
            "last_output": ""
        }
        
        current_prompt = task
        
        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1
            state["iterations"] = self.current_iteration
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {self.current_iteration}/{self.max_iterations}")
            logger.info(f"{'='*60}")
            
            # Run Claude with current prompt
            logger.info("Running Claude...")
            output = self.run_claude(current_prompt)
            state["last_output"] = output
            
            # Check for completion
            if completion_promise in output or self.is_task_complete(task, state):
                logger.info("\n[OK] Task completed!")
                state["completed"] = True
                self.save_state(state)
                return True
            
            # Generate continuation prompt
            current_prompt = self.generate_continuation_prompt(task, state)
            
            # Save state
            self.save_state(state)
            
            # Brief pause between iterations
            time.sleep(2)
        
        logger.warning(f"\n[WARNING] Max iterations ({self.max_iterations}) reached without completion")
        state["completed"] = False
        self.save_state(state)
        return False


class FileBasedRalphLoop:
    """
    File-based Ralph Wiggum Loop.
    
    Instead of running Claude directly, this monitors state files
    and creates prompts for Claude to process.
    """

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.state_file = self.vault_path / 'Logs' / 'ralph_file_state.json'
        self.task_file = self.vault_path / 'Needs_Action' / 'RALPH_TASK.md'
        
    def create_task(self, task_description: str) -> Path:
        """Create a task file for Ralph loop processing."""
        content = f"""---
type: ralph_task
created: {datetime.now().isoformat()}
status: in_progress
iterations: 0
max_iterations: 10
---

# Ralph Wiggum Autonomous Task

## Task Description
{task_description}

## Instructions for AI
1. Read this task file
2. Process the task according to company guidelines
3. When complete, update status to 'completed'
4. If more iterations needed, update iteration count

## Progress Log
"""
        
        self.task_file.write_text(content, encoding='utf-8')
        return self.task_file

    def check_completion(self) -> bool:
        """Check if the Ralph task is complete."""
        if not self.task_file.exists():
            return True
        
        content = self.task_file.read_text(encoding='utf-8')
        return "status: completed" in content

    def get_iteration_count(self) -> int:
        """Get current iteration count."""
        if not self.task_file.exists():
            return 0
        
        content = self.task_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if 'iterations:' in line:
                try:
                    return int(line.split(':')[1].strip())
                except:
                    pass
        return 0

    def update_iteration(self, count: int, notes: str = ""):
        """Update iteration count in task file."""
        if not self.task_file.exists():
            return
        
        content = self.task_file.read_text(encoding='utf-8')
        
        # Update iteration count
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'iterations:' in line:
                lines[i] = f"iterations: {count}"
        
        # Add progress note
        if notes:
            lines.append(f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {notes}")
        
        self.task_file.write_text('\n'.join(lines), encoding='utf-8')


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop for Autonomous Tasks')
    parser.add_argument('task', type=str, help='Task description')
    parser.add_argument('--max-iterations', type=int, default=10, help='Maximum iterations')
    parser.add_argument('--completion-promise', type=str, default='TASK_COMPLETE', 
                        help='Promise string to detect completion')
    parser.add_argument('--vault', default='.', help='Path to vault')
    parser.add_argument('--file-mode', action='store_true', help='Use file-based mode')

    args = parser.parse_args()

    print("Ralph Wiggum Loop - Gold Tier")
    print("=" * 50)
    print(f"Task: {args.task}")
    print(f"Max iterations: {args.max_iterations}")
    print()

    if args.file_mode:
        # File-based mode
        loop = FileBasedRalphLoop(vault_path=args.vault)
        task_file = loop.create_task(args.task)
        print(f"[OK] Task file created: {task_file}")
        print("\nNext steps:")
        print("1. Run Claude Code to process the task")
        print("2. Claude will update the task file as it works")
        print("3. When complete, status will be 'completed'")
        print("\nMonitor with: python ralph_wiggum_loop.py --status")
    else:
        # Direct mode (requires Claude Code in PATH)
        loop = RalphWiggumLoop(vault_path=args.vault, max_iterations=args.max_iterations)
        
        print("Starting autonomous task execution...")
        print("(This will run Claude Code repeatedly until task is complete)")
        print()
        
        success = loop.run(args.task, args.completion_promise)
        
        if success:
            print("\n[OK] Task completed successfully!")
        else:
            print(f"\n[WARNING] Task not completed after {args.max_iterations} iterations")
            print("Consider increasing --max-iterations or breaking task into smaller steps")


if __name__ == "__main__":
    main()
