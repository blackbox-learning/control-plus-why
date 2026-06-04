"""
ProcrastinaAI Services - AI Generation Functions

This module contains all AI-powered functions for generating:
- Procrastination predictions
- Witty disappearance responses
- Daily reports with procrastination analysis
- Funny reasons to procrastinate

All functions use OpenAI API (gpt-3.5-turbo model).
"""

import os
import re
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


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
        prompt = f"""You are a humorous AI that predicts procrastination paths.

User Profile:
- Mood: {mood}
- Interests: {', '.join(interests)}
- Tasks to do: {', '.join(tasks)}

Generate a 5-7 step procrastination journey showing EXACTLY how this user will procrastinate.
Be hilarious and specific to their interests.

Format your response as a numbered list, one step per line.
Each step should be 5-10 words max.
Example: "1. Open email, ignore important message"

IMPORTANT: Only return the numbered steps, nothing else."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.8,
            max_tokens=300
        )

        # Parse the response
        prediction_text = response.choices[0].message.content
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
        
        prompt = f"""You are a sarcastic AI roasting someone for procrastinating.

User disappeared to: {location}
User mood: {mood}
User interests: {', '.join(interests)}

Generate ONE witty, sarcastic response (2-3 sentences max) about where they went.
Be funny, slightly judgmental, and reference their interests if relevant.
Keep it under 15 words per sentence.

IMPORTANT: Only return the roast, nothing else."""

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.9,
            max_tokens=150
        )

        return {
            'success': True,
            'data': response.choices[0].message.content,
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
        prompt = f"""You are a witty AI generating a sarcastic daily procrastination report.

Report Stats:
- Tasks planned: {tasks_planned}
- Tasks completed: {tasks_completed}
- Disappearances: {disappearances}
- Most common excuse: {common_excuse}

Generate a 3-4 sentence humorous summary of their procrastination day.
Be sarcastic but supportive. Reference the stats where relevant.

IMPORTANT: Only return the summary, nothing else."""

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.8,
            max_tokens=200
        )

        # Calculate procrastination score
        if tasks_planned > 0:
            score = max(0, min(100, int(100 - (tasks_completed / tasks_planned) * 50 + disappearances * 3)))
        else:
            score = 0

        return {
            'success': True,
            'data': response.choices[0].message.content,
            'score': score,
        }
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        return {
            'success': False,
            'error': str(e),
        }


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
        prompt = f"""You are a creative AI generating hilarious reasons to procrastinate.

Task: {task_name}
User Mood: {mood}

Generate 3-4 FUNNY, CREATIVE reasons why someone should procrastinate on this task instead of doing it.
Make them absurd, funny, and reference common procrastination habits.
Each reason should be 1-2 sentences max.

Format: 
- Reason 1
- Reason 2
- Reason 3

IMPORTANT: Only return the reasons list, nothing else."""

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.9,
            max_tokens=250
        )

        # Parse response into list
        response_text = response.choices[0].message.content
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

