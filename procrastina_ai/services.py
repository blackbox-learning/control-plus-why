"""
ProcrastinaAI Services - AI Generation Functions

This module contains all AI-powered functions for generating:
- Procrastination predictions
- Witty disappearance responses
- Daily reports with procrastination analysis
- Funny reasons to procrastinate

All functions use OpenRouter API (free Google Gemini model).
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


def generate_prediction(mood, interests, tasks):
    """
    Generate a funny procrastination prediction journey.
    
    Args:
        mood (str): User's mood (e.g., 'sleepy', 'lazy')
        interests (list): User's interests (e.g., ['YouTube', 'AI', 'Gaming'])
        tasks (list): Tasks user planned to do
    
    Returns:
        dict: {
            'success': bool,
            'data': list of prediction steps,
            'confidence': int (0-100),
            'error': str (if failed)
        }
    
    Example:
        result = generate_prediction('sleepy', ['YouTube'], ['Record Video'])
        if result['success']:
            print(result['data'])  # ['Step 1...', 'Step 2...', ...]
    """
    try:
        # Create a personalized prompt
        prompt = f"""You are a funny friend who knows exactly how someone will procrastinate today.

Their mood: {mood}
Their interests: {', '.join(interests)}
Tasks they planned: {', '.join(tasks)}

Write a 5-7 step procrastination journey. Show how they start working, get distracted step by step, and end up doing something completely unrelated.

RULES:
- Each step = ONE short line (3-8 words max)
- Use simple words a kid would understand
- Be specific to their interests
- Be funny but kind — tease, don't insult
- End with something absurd or relatable
- Format as a numbered list: "1. Open the project"

EXAMPLES OF GOOD STYLE:
"Open laptop"
"Check one email"
"Fall into YouTube"
"Forget why you opened laptop"

Only return the numbered list. No intro, no explanation."""

        # Call OpenRouter AI with fallback
        prediction_text = _call_ai(prompt, temperature=0.8, max_tokens=300)
        steps = [
            re.sub(r'^\d+\.\s*', '', line).strip() 
            for line in prediction_text.split('\n') 
            if line.strip()
        ]

        return {
            'success': True,
            'data': steps,
            'confidence': 94,
        }
    
    except Exception as e:
        print(f"Error generating prediction: {str(e)}")
        return {
            'success': False,
            'error': str(e),
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


def generate_daily_report(tasks_planned, tasks_completed, disappearances, common_excuse):
    """
    Generate a daily procrastination report with AI analysis.
    
    Args:
        tasks_planned (int): Number of tasks planned
        tasks_completed (int): Number of tasks completed
        disappearances (int): Number of disappearances
        common_excuse (str): Most common excuse/reason
    
    Returns:
        dict: {
            'success': bool,
            'data': str (AI summary),
            'score': int (0-100 procrastination score),
            'error': str (if failed)
        }
    
    Example:
        result = generate_daily_report(4, 1, 7, 'Researching workflow')
        if result['success']:
            print(f"Score: {result['score']}")
            print(f"Summary: {result['data']}")
    """
    try:
        prompt = f"""You are a funny friend writing someone's end-of-day summary.

Today's stats:
- Tasks planned: {tasks_planned}
- Tasks completed: {tasks_completed}
- Times they got distracted: {disappearances}
- Go-to distraction: {common_excuse}

Write a SHORT summary (3-5 lines max).

RULES:
- Each line = one short sentence
- Use line breaks between lines
- Use simple words a kid would understand
- Be funny but kind
- Tease them, don't make them feel bad
- Add a tiny compliment or "respect" moment
- Sound like a friend commenting on their day

EXAMPLES OF GOOD STYLE:
"You planned 5 things.
You finished zero.
But you did become an expert in laptop reviews.
Respect the dedication."

Only return the summary. No intro, no labels."""

        ai_text = _call_ai(prompt, temperature=0.8, max_tokens=200)

        # Calculate procrastination score
        if tasks_planned > 0:
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

