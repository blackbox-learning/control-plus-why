"""
ProcrastinaAI Services - AI Generation Functions

This module contains all AI powered functions for generating:
- Full-day procrastination forecasts (prediction engine)
- Witty disappearance responses
- Daily reports with procrastination analysis
- Funny reasons to procrastinate
- Idle-return contextual options

All functions use OpenRouter API (free models with fallback chain).
"""

import os
import re
from openai import OpenAI

# Initialize OpenAI client pointing to OpenRouter
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),  # OpenRouter key stored in OPENAI_API_KEY
    base_url='https://openrouter.ai/api/v1',
)

# Free models on OpenRouter (in order of preference, with fallback)
FREE_MODELS = [
    'google/gemma-4-31b-it:free',
    'nvidia/nemotron-3-super-120b-a12b:free',
    'meta-llama/llama-3.3-70b-instruct:free',
    'meta-llama/llama-3.2-3b-instruct:free',
]


def _call_ai(prompt, temperature=0.8, max_tokens=300):
    """
    Call OpenRouter AI with automatic model fallback on rate-limit errors.
    Tries each free model in order until one succeeds.
    """
    last_error = None
    for model in FREE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            print(f"Model {model} failed: {e}")
            continue
    # All models failed
    raise Exception(
        "All free AI models are currently rate-limited or unavailable. "
        "Please check your OpenRouter API key or try again later."
    ) from last_error


def generate_prediction(mood, interests, tasks, disappearance_history=None):
    """
    Generate a full-day procrastination forecast.

    Produces a humorous 'weather forecast' style prediction covering
    approximately 6-10 hours of the user's workday. Includes journey
    steps with durations, natural breaks, metrics, and AI warnings.

    Args:
        mood (str): User's mood (e.g., 'sleepy', 'lazy', 'motivated')
        interests (list): User's interests (e.g., ['YouTube', 'AI', 'Gaming'])
        tasks (list): Tasks user planned to do
        disappearance_history (list, optional): Previous disappearance types

    Returns:
        dict: {
            'success': bool,
            'data': {
                'forecastSummary': str,
                'journey': list,
                'naturalBreaks': list,
                'metrics': dict,
                'warnings': list,
            },
            'confidence': int (0-100),
            'error': str (if failed)
        }
    """
    try:
        history_str = ''
        if disappearance_history:
            history_str = f"\nPrevious distractions today: {', '.join(disappearance_history[:5])}"

        prompt = f"""You are an expert procrastination forecaster. You write funny, relatable, and eerily accurate predictions of how people waste their workdays.

Generate a full-day procrastination forecast for this person:

Mood: {mood}
Interests: {', '.join(interests)}
Tasks planned: {', '.join(tasks)}
Number of tasks: {len(tasks)}{history_str}

Create a COMPLETE WORKDAY FORECAST covering approximately 6-10 hours. This should feel like a weather forecast for procrastination.

RULES:
- Generate 8-14 journey steps that simulate an entire workday
- Each step needs a title (3-8 words), estimated duration, distraction risk, and recovery chance
- Durations should total 6-10 hours across all steps
- Use realistic durations: real work = 15-45 min, distractions = 20-60 min, breaks = 10-90 min
- Insert 2-4 natural breaks (coffee, lunch, tea, walking, existential crisis, social media) at realistic points
- Generate 2-3 funny AI warnings based on their mood, interests, and tasks
- Metrics should be realistic percentages (0-100)
- Be specific to their interests — don't use generic distractions
- Be funny but kind — tease, don't insult
- Use simple language a kid would understand
- NEVER use exact clock times, only durations
- Distraction Risk levels: Very Low, Low, Medium, High, Very High, Extreme
- Recovery Chance levels: Certain, High, Moderate, Low, Questionable, Impossible

RESPOND WITH VALID JSON ONLY. No markdown, no explanation, no code blocks. Use this exact structure:

{{
  "forecastSummary": "Today's Procrastination Forecast: [2-3 funny sentences about their day]",
  "journey": [
    {{"title": "Start Editing Video", "duration": "25 min", "distractionRisk": "Low", "recoveryChance": "High", "icon": "🎬"}},
    {{"title": "Watch One Tutorial", "duration": "30 min", "distractionRisk": "Medium", "recoveryChance": "Moderate", "icon": "📺"}},
    {{"title": "Research Better Editing Software", "duration": "45 min", "distractionRisk": "High", "recoveryChance": "Low", "icon": "🔍"}}
  ],
  "naturalBreaks": [
    {{"title": "Coffee Mission", "duration": "10-20 Minutes", "icon": "☕"}},
    {{"title": "Lunch Break", "duration": "45-90 Minutes", "icon": "🍛"}}
  ],
  "metrics": {{
    "productivity": 35,
    "distraction": 78,
    "completion": 22,
    "mainDistraction": "YouTube"
  }},
  "warnings": [
    "Today's plan contains 3 tasks. History suggests you may spend 90 minutes researching tools designed to save 10 minutes.",
    "The task is simple. Your interests are not."
  ]
}}"""

        # Call AI with higher token limit for full-day forecast
        prediction_text = _call_ai(prompt, temperature=0.85, max_tokens=2000)

        # Parse JSON response
        # Strip markdown code fences if present
        cleaned = prediction_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0]
        cleaned = cleaned.strip()

        import json as json_mod
        forecast = json_mod.loads(cleaned)

        # Validate required fields
        journey = forecast.get('journey', [])
        if not journey:
            raise ValueError("AI returned empty journey")

        natural_breaks = forecast.get('naturalBreaks', [])
        metrics = forecast.get('metrics', {})
        warnings = forecast.get('warnings', [])
        forecast_summary = forecast.get('forecastSummary', '')

        # Validate metrics are within bounds
        for key in ('productivity', 'distraction', 'completion'):
            val = metrics.get(key, 50)
            metrics[key] = max(0, min(100, int(val)))

        # Validate mainDistraction
        if not metrics.get('mainDistraction'):
            metrics['mainDistraction'] = interests[0] if interests else 'Unknown'

        return {
            'success': True,
            'data': {
                'forecastSummary': forecast_summary,
                'journey': journey,
                'naturalBreaks': natural_breaks,
                'metrics': metrics,
                'warnings': warnings,
            },
            'confidence': 94,
        }

    except Exception as e:
        print(f"Error generating prediction: {str(e)}")
        # Fallback: generate synthetic forecast
        fallback = _generate_prediction_fallback(mood, interests, tasks)
        return {
            'success': True,
            'data': fallback,
            'confidence': 72,
        }


def _generate_prediction_fallback(mood, interests, tasks):
    """
    Generate a synthetic prediction when the AI call fails.
    Uses the user's inputs to create a personalised (but simpler) forecast.
    """
    primary_interest = interests[0] if interests else 'the internet'
    secondary_interest = interests[1] if len(interests) > 1 else 'random Wikipedia pages'

    journey = [
        {'title': f'Start working on {tasks[0] if tasks else "the first task"}', 'duration': '20 min', 'distractionRisk': 'Low', 'recoveryChance': 'High', 'icon': '📝'},
        {'title': f'Quick check of {primary_interest}', 'duration': '15 min', 'distractionRisk': 'Medium', 'recoveryChance': 'Moderate', 'icon': '👀'},
        {'title': f'Deep dive into {primary_interest}', 'duration': '45 min', 'distractionRisk': 'Very High', 'recoveryChance': 'Low', 'icon': '🕳️'},
        {'title': 'Realize time has passed', 'duration': '5 min', 'distractionRisk': 'Low', 'recoveryChance': 'High', 'icon': '😳'},
        {'title': f'Actually work on {tasks[0] if tasks else "the task"}', 'duration': '30 min', 'distractionRisk': 'Medium', 'recoveryChance': 'Moderate', 'icon': '💪'},
        {'title': f'Open {secondary_interest} for "research"', 'duration': '40 min', 'distractionRisk': 'Very High', 'recoveryChance': 'Questionable', 'icon': '🔍'},
        {'title': 'Compare tools and products online', 'duration': '35 min', 'distractionRisk': 'High', 'recoveryChance': 'Low', 'icon': '🛒'},
        {'title': 'Feel productive about research', 'duration': '10 min', 'distractionRisk': 'Low', 'recoveryChance': 'High', 'icon': '😌'},
        {'title': f'Start {tasks[1] if len(tasks) > 1 else "next task"} properly', 'duration': '25 min', 'distractionRisk': 'Medium', 'recoveryChance': 'Moderate', 'icon': '📋'},
        {'title': 'Discover a new rabbit hole', 'duration': '50 min', 'distractionRisk': 'Extreme', 'recoveryChance': 'Impossible', 'icon': '🐇'},
        {'title': 'Accept that today was "research day"', 'duration': '15 min', 'distractionRisk': 'Low', 'recoveryChance': 'Certain', 'icon': '🏳️'},
        {'title': 'Plan to do everything tomorrow', 'duration': '10 min', 'distractionRisk': 'Low', 'recoveryChance': 'Certain', 'icon': '📅'},
    ]

    natural_breaks = [
        {'title': 'Coffee Mission', 'duration': '10-20 Minutes', 'icon': '☕'},
        {'title': 'Lunch Break', 'duration': '45-90 Minutes', 'icon': '🍛'},
        {'title': 'Existential Crisis', 'duration': '5-15 Minutes', 'icon': '🧠'},
    ]

    metrics = {
        'productivity': max(10, min(90, 100 - len(tasks) * 12)),
        'distraction': min(95, 50 + len(interests) * 10),
        'completion': max(5, min(80, len(tasks) * 15 - 10)),
        'mainDistraction': primary_interest,
    }

    task_word = 'task' if len(tasks) == 1 else 'tasks'
    warnings = [
        f"Today's plan contains {len(tasks)} {task_word}. The AI has already started laughing.",
        f"Your interests are {', '.join(interests[:3])}. Your tasks don't stand a chance.",
    ]

    forecast_summary = (
        f"Today's Procrastination Forecast: "
        f"High chance of {primary_interest} exploration. "
        f"Moderate chance of productivity. "
        f"Strong possibility of forgetting why Chrome was opened."
    )

    return {
        'forecastSummary': forecast_summary,
        'journey': journey,
        'naturalBreaks': natural_breaks,
        'metrics': metrics,
        'warnings': warnings,
    }


def generate_disappearance_response(disappearance_type, custom_location, mood, interests):
    """
    Generate a witty AI response about where the user disappeared to.
    
    Args:
        disappearance_type (str): Type of disappearance (youtube, ai_tools, etc.)
        custom_location (str): Custom location if type is 'other'
        mood (str): User's mood
        interests (list): User's interests
    
    Returns:
        dict: {
            'success': bool,
            'data': str (AI response),
            'error': str (if failed)
        }
    
    Example:
        result = generate_disappearance_response('youtube', None, 'sleepy', ['YouTube'])
        if result['success']:
            print(result['data'])  # "Witty response here..."
    """
    try:
        # Use custom location if provided, otherwise use type
        location = custom_location if custom_location else disappearance_type.replace('_', ' ')
        
        prompt = f"""You are a funny friend commenting on someone's distraction.

They got distracted by: {location}
Their mood: {mood}
Their interests: {', '.join(interests)}

Write a SHORT response (2-4 lines max).

RULES:
- Each line = one short sentence
- Use line breaks between sentences
- Use simple words
- Tease them gently, don't insult
- Add a tiny compliment or "respect" at the end
- Sound like a friend texting them a joke

EXAMPLES OF GOOD STYLE:
"You went for one video.
You came back with a new hobby."

"Your current laptop works fine.
But the research was impressive.
Respect the dedication."

Only return the response. No intro, no labels."""

        ai_text = _call_ai(prompt, temperature=0.9, max_tokens=150)

        return {
            'success': True,
            'data': ai_text,
        }
    
    except Exception as e:
        print(f"Error generating disappearance response: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }


def generate_daily_report(tasks_planned, tasks_completed, disappearances, common_excuse, task_statuses=None):
    """
    Generate a daily procrastination report with AI analysis.
    
    Args:
        tasks_planned (int): Number of tasks planned
        tasks_completed (int): Number of tasks completed
        disappearances (int): Number of disappearances
        common_excuse (str): Most common excuse/reason
        task_statuses (dict, optional): {task_name: status} from task review
    
    Returns:
        dict: {
            'success': bool,
            'data': str (AI summary),
            'score': int (0-100 procrastination score),
            'error': str (if failed)
        }
    """
    try:
        # Build task completion detail for the prompt
        task_detail = ''
        completion_percentage = 0
        if task_statuses:
            from collections import Counter
            # Support both old format {task: "status"} and new format {task: {status, completion_score}}
            def _get_status(v):
                return v.get('status', v) if isinstance(v, dict) else v
            def _get_score(v):
                if isinstance(v, dict) and 'completion_score' in v:
                    return v['completion_score']
                # Fallback scores for old-format data
                score_map = {'completed': 100, 'in_progress': 75, 'partially_completed': 50, 'abandoned': 25, 'never_started': 0}
                return score_map.get(_get_status(v), 0)

            statuses = [_get_status(v) for v in task_statuses.values()]
            scores = [_get_score(v) for v in task_statuses.values()]
            counts = Counter(statuses)

            status_labels = {
                'completed': 'completed',
                'in_progress': 'still in progress',
                'partially_completed': 'partially completed',
                'abandoned': 'abandoned',
                'never_started': 'never started',
            }
            parts = []
            for key, label in status_labels.items():
                c = counts.get(key, 0)
                if c > 0:
                    parts.append(f'{c} {label}')
            task_detail = f'\nTask breakdown: {", ".join(parts)}.'
            # Completion percentage from average scores
            completion_percentage = round(sum(scores) / len(scores)) if scores else 0
            task_detail += f'\nOverall completion: {completion_percentage}%.'
            # Add individual task names with statuses
            task_lines = '\n'.join(
                f'- {name}: {status_labels.get(_get_status(v), _get_status(v))} (score: {_get_score(v)})'
                for name, v in task_statuses.items()
            )
            task_detail += f'\n{task_lines}'

        prompt = f"""You are a funny friend writing someone's end-of-day summary.

Today's stats:
- Tasks planned: {tasks_planned}
- Tasks completed: {tasks_completed}
- Overall completion: {completion_percentage}%
- Times they got distracted: {disappearances}
- Go-to distraction: {common_excuse}{task_detail}

Write a SHORT summary (3-5 lines max).

RULES:
- Each line = one short sentence
- Use line breaks between lines
- Use simple words a kid would understand
- Be funny but kind
- Tease them, don't make them feel bad
- Add a tiny compliment or "respect" moment
- Sound like a friend commenting on their day
- Reference specific tasks and their statuses when possible
- Mention the completion percentage naturally

EXAMPLES OF GOOD STYLE:
"You planned 5 things.
Two survived. One is still negotiating. Two never saw daylight.
34% completion. The laptop research was thorough though.
Respect the dedication."

Only return the summary. No intro, no labels."""

        ai_text = _call_ai(prompt, temperature=0.8, max_tokens=200)

        # Calculate procrastination score using completion percentage when available
        if completion_percentage > 0:
            score = max(0, min(100, int(100 - completion_percentage + disappearances * 2)))
        elif tasks_planned > 0:
            score = max(0, min(100, int(100 - (tasks_completed / tasks_planned) * 50 + disappearances * 3)))
        else:
            score = 0

        return {
            'success': True,
            'data': ai_text,
            'score': score,
        }
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }


def generate_idle_return_options(mood, interests, last_app, history):
    """
    Generate contextual distraction options for the idle-return popup.

    When the user comes back after an idle period, these options ask
    where they disappeared to. Options are personalised using mood,
    interests, the app that was focused before idle, and past
    disappearances.

    Falls back to a hardcoded list if the AI call fails.
    """
    # Default fallback — always works even if AI is unavailable
    fallback = [
        {'type': 'youtube',      'label': 'Watching YouTube',     'sub': 'Just one video, right?'},
        {'type': 'laptops',      'label': 'Laptop Research',      'sub': 'Your current one works fine.'},
        {'type': 'ai_tools',     'label': 'AI Tool Hunting',      'sub': 'Very meta.'},
        {'type': 'startup',      'label': 'Startup Ideas',        'sub': 'Great idea. Creative timing.'},
        {'type': 'comments',     'label': 'Reading Comments',     'sub': 'Your takes are sharper now.'},
        {'type': 'other',        'label': 'Something Else',       'sub': 'Confess.'},
    ]

    try:
        history_str = ', '.join(history[:5]) if history else 'none yet'
        prompt = f"""You are a funny friend who knows someone just came back after being away from their computer.

Their mood: {mood}
Their interests: {', '.join(interests) if interests else 'general'}
Last active app before leaving: {last_app or 'unknown'}
Previous distractions today: {history_str}

Generate exactly 5 short reasons for where they might have gone.
Each reason is ONE line: type_label | subtitle

Use these exact types: youtube, laptops, ai_tools, startup, other
Make the subtitles funny, short (3-6 words), personal to their interests.

Format:
youtube | Watching YouTube | subtitle here
laptops | Laptop Research | subtitle here
ai_tools | AI Tool Hunting | subtitle here
startup | Startup Ideas | subtitle here
other | Something Else | subtitle here

Only return the 5 lines. No intro, no explanation."""

        ai_text = _call_ai(prompt, temperature=0.9, max_tokens=200)
        options = []
        for line in ai_text.split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                options.append({'type': parts[0], 'label': parts[1], 'sub': parts[2]})

        # Always include "Other" as last option
        if not any(o['type'] == 'other' for o in options):
            options.append({'type': 'other', 'label': 'Something Else', 'sub': 'Confess.'})

        return options if len(options) >= 3 else fallback

    except Exception as e:
        print(f"Error generating idle return options: {e}")
        return fallback


def generate_funny_reasons(task_name, mood):
    """
    Generate funny reasons to procrastinate on a specific task.
    
    Args:
        task_name (str): Name of the task
        mood (str): User's mood
    
    Returns:
        dict: {
            'success': bool,
            'data': list of funny reasons,
            'error': str (if failed)
        }
    
    Example:
        result = generate_funny_reasons('Record Video', 'motivated')
        if result['success']:
            for reason in result['data']:
                print(f"- {reason}")
    """
    try:
        prompt = f"""You are a funny friend giving someone reasons to NOT do their task.

The task: {task_name}
Their mood: {mood}

Write 3-4 SHORT reasons why they should skip this task today.

RULES:
- Each reason = 2-3 short lines
- Use line breaks between lines
- Use simple words
- Be absurd and funny
- Sound like a friend joking
- Never be mean or negative

EXAMPLES OF GOOD STYLE:
"The camera was ready.
The tripod was ready.
You were busy becoming a laptop expert."

"The deadline is tomorrow.
That means you still have tonight.
And tonight is for research."

Format as a bulleted list:
- Reason 1
- Reason 2
- Reason 3

Only return the list. No intro, no explanation."""

        # Parse response into list
        response_text = _call_ai(prompt, temperature=0.9, max_tokens=250)
        reasons = [
            re.sub(r'^-\s*', '', line).strip()
            for line in response_text.split('\n')
            if line.strip() and '-' in line
        ]

        # Fallback if parsing fails
        if not reasons:
            reasons = [response_text]

        return {
            'success': True,
            'data': reasons,
        }
    
    except Exception as e:
        print(f"Error generating funny reasons: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }

