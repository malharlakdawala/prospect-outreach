"""Base agent class using Claude Code CLI (uses your Max plan, no API key needed)."""

import json
import re
import subprocess
import time

from config import MAX_RETRIES, RETRY_BASE_DELAY, API_DELAY


class BaseAgent:
    def __init__(self, name: str, model: str, max_tokens: int):
        self.name = name
        self.model = model
        self.max_tokens = max_tokens

    def run(self, system_prompt: str, user_message: str) -> dict:
        """Call Claude via Claude Code CLI. Returns parsed JSON dict."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                # Build the claude CLI command
                # Pipe user message via stdin to handle long prompts safely
                cmd = [
                    "claude",
                    "-p",                          # print mode (non-interactive)
                    "--output-format", "text",     # get raw text output
                    "--system-prompt", system_prompt,
                    "--model", self.model,
                    "--no-session-persistence",     # don't save these as sessions
                ]

                result = subprocess.run(
                    cmd,
                    input=user_message,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minute timeout per call
                )

                if result.returncode != 0:
                    last_error = f"Claude CLI error: {result.stderr.strip()}"
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BASE_DELAY * (2 ** attempt))
                    continue

                text = result.stdout.strip()

                if not text:
                    last_error = "Empty response from Claude CLI"
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BASE_DELAY)
                    continue

                # Parse JSON from response
                parsed = self._parse_json(text)

                # Token usage not available via CLI, set to 0
                parsed["_tokens_used"] = 0

                time.sleep(API_DELAY)
                return parsed

            except subprocess.TimeoutExpired:
                last_error = "Claude CLI timed out after 120 seconds"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BASE_DELAY)

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BASE_DELAY)

        return {"error": last_error or "Max retries exceeded", "_tokens_used": 0}

    def _parse_json(self, text: str) -> dict:
        """Extract and parse JSON from response text."""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return {"raw_text": text, "parse_error": "Could not extract JSON from response"}
