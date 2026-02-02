"""
Mr. MeThinks - AI-powered project idea generator.

Helps users who don't know what to build by generating personalized
project ideas based on their interests, skill level, and problems.
"""

import asyncio
import random
from typing import Optional, Tuple, List


PERSONALITY = """You are Mr. MeThinks, a friendly and enthusiastic idea generator!

Your personality:
- Excited about helping people find cool project ideas
- Encouraging and positive
- You explain ideas simply, no jargon
- You tailor ideas to the person's interests and skill level
- You give concrete, buildable project ideas (not vague concepts)

When suggesting ideas:
1. Give exactly 3 project ideas
2. Each idea should have: a fun name, what it does, why it's cool
3. Mark one as "Perfect for you!" based on their interests
4. Make ideas progressively more ambitious (starter → intermediate → ambitious)
5. End with an encouraging message

Format each idea like:
### 🎯 [Fun Project Name]
**What it is:** [1 sentence]
**Why it's cool:** [1 sentence]
**You'll learn:** [2-3 skills]
**Difficulty:** ⭐/⭐⭐/⭐⭐⭐
"""

WELCOME_MESSAGE = """### 👋 Hey there! I'm Mr. MeThinks!

I help you figure out what to build. Tell me a bit about yourself:

- **What are you into?** (games, music, productivity, social, data, etc.)
- **What bugs you?** (a problem you wish was solved)
- **What's your vibe?** (just learning, want a challenge, etc.)

Fill in the info and I'll cook up some perfect project ideas for you! 🧠✨"""


class MrMeThinks:
    """Project idea generator that creates personalized suggestions."""

    # Random interests for inspiration
    INTERESTS = [
        "music and playlists",
        "gaming and esports",
        "cooking and recipes",
        "fitness and health",
        "movies and TV shows",
        "books and reading",
        "travel and places",
        "finance and budgeting",
        "social media",
        "productivity and habits",
        "memes and humor",
        "pets and animals",
        "art and design",
        "news and current events",
        "learning and education",
        "photography",
        "sports and stats",
        "weather and nature",
    ]

    # Random problems for inspiration
    PROBLEMS = [
        "I always forget things",
        "I waste too much time on my phone",
        "I can't decide what to watch/eat/do",
        "I lose track of my goals",
        "I want to share stuff with friends easier",
        "I have too many tabs open",
        "I can't find good recommendations",
        "My files are a mess",
        "I don't drink enough water",
        "I want to learn something new every day",
        "I can't stick to habits",
        "I lose track of time",
        "",  # Sometimes no problem, just exploring
        "",
    ]

    SKILL_LEVELS = [
        "Just starting out",
        "Know the basics",
        "Pretty comfortable",
        "Ready for a challenge",
    ]

    def __init__(self, connector=None):
        """
        Initialize Mr. MeThinks.

        Args:
            connector: NexusConnector instance (optional, can be set later)
        """
        self.connector = connector

    def set_connector(self, connector):
        """Set the AI connector."""
        self.connector = connector

    async def generate_async(
        self,
        interests: str = "",
        skill_level: str = "Just starting out",
        problem: str = "",
    ) -> str:
        """
        Generate project ideas asynchronously.

        Args:
            interests: User's interests (e.g., "games, music")
            skill_level: One of the SKILL_LEVELS
            problem: Optional problem they want to solve

        Returns:
            Formatted markdown with 3 project ideas
        """
        if not self.connector:
            raise ValueError("No connector set. Call set_connector() first.")

        if not interests.strip() and not problem.strip():
            return WELCOME_MESSAGE

        prompt = f"""{PERSONALITY}

Here's who I'm helping:

**Their interests:** {interests if interests.strip() else "Not specified"}
**Skill level:** {skill_level}
**Problem they want to solve:** {problem if problem.strip() else "Not specified - just looking for cool ideas"}

Generate 3 perfect project ideas for them! Be specific and concrete - these should be things they can actually build."""

        response = await self.connector.send_message(prompt)
        return response.get("content", "Hmm, my brain got stuck! Try again?")

    def generate(
        self,
        interests: str = "",
        skill_level: str = "Just starting out",
        problem: str = "",
    ) -> str:
        """
        Generate project ideas synchronously.

        Args:
            interests: User's interests
            skill_level: One of the SKILL_LEVELS
            problem: Optional problem to solve

        Returns:
            Formatted markdown with 3 project ideas
        """
        return asyncio.run(self.generate_async(interests, skill_level, problem))

    @classmethod
    def random_inputs(cls) -> Tuple[str, str, str]:
        """
        Generate random inputs for inspiration.

        Returns:
            Tuple of (interests, skill_level, problem)
        """
        return (
            random.choice(cls.INTERESTS),
            random.choice(cls.SKILL_LEVELS[:2]),  # Bias toward beginners
            random.choice(cls.PROBLEMS),
        )

    @staticmethod
    def extract_idea(idea_text: str, number: int) -> str:
        """
        Extract a specific idea (1, 2, or 3) from generated output.

        Args:
            idea_text: The full Mr. MeThinks output
            number: Which idea to extract (1, 2, or 3)

        Returns:
            A buildable prompt like "Build [Project Name]: [description]"
        """
        lines = idea_text.split('\n')
        ideas = []

        for i, line in enumerate(lines):
            if '###' in line and '🎯' in line:
                # Found a project header
                name = line.replace('###', '').replace('🎯', '').strip()
                # Remove "Perfect for you!" if present
                name = name.replace('⭐ Perfect for you!', '').strip()

                # Look for "What it is" in next few lines
                desc = ""
                for j in range(i + 1, min(i + 6, len(lines))):
                    if 'What it is' in lines[j]:
                        desc = lines[j].split(':', 1)[-1].strip().strip('*')
                        break

                ideas.append({"name": name, "desc": desc})

        if 0 < number <= len(ideas):
            idea = ideas[number - 1]
            return f"Build {idea['name']}: {idea['desc']}"

        return "Build me something cool"

    @staticmethod
    def extract_all_ideas(idea_text: str) -> List[dict]:
        """
        Extract all ideas from generated output.

        Args:
            idea_text: The full Mr. MeThinks output

        Returns:
            List of idea dictionaries with 'name' and 'desc' keys
        """
        lines = idea_text.split('\n')
        ideas = []

        for i, line in enumerate(lines):
            if '###' in line and '🎯' in line:
                name = line.replace('###', '').replace('🎯', '').strip()
                name = name.replace('⭐ Perfect for you!', '').strip()

                desc = ""
                difficulty = ""
                skills = ""

                for j in range(i + 1, min(i + 10, len(lines))):
                    if 'What it is' in lines[j]:
                        desc = lines[j].split(':', 1)[-1].strip().strip('*')
                    elif 'Difficulty' in lines[j]:
                        difficulty = lines[j].split(':', 1)[-1].strip()
                    elif "You'll learn" in lines[j]:
                        skills = lines[j].split(':', 1)[-1].strip()

                ideas.append({
                    "name": name,
                    "desc": desc,
                    "difficulty": difficulty,
                    "skills": skills,
                })

        return ideas
