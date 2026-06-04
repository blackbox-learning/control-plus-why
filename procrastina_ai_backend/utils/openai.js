const { OpenAI } = require('openai');
require('dotenv').config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Generate procrastination prediction with journey
const generatePrediction = async (mood, interests, tasks) => {
  try {
    const prompt = `You are a humorous AI that predicts procrastination paths.

User Profile:
- Mood: ${mood}
- Interests: ${interests.join(', ')}
- Tasks to do: ${tasks.join(', ')}

Generate a 5-7 step procrastination journey showing EXACTLY how this user will procrastinate. 
Be hilarious and specific to their interests. 

Format your response as a numbered list, one step per line.
Each step should be 5-10 words max. 
Example: "1. Open email, ignore important message"

IMPORTANT: Only return the numbered steps, nothing else.`;

    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.8,
      max_tokens: 300
    });

    return {
      success: true,
      data: response.choices[0].message.content,
      tokens: response.usage.total_tokens
    };
  } catch (error) {
    console.error('OpenAI Prediction Error:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
};

// Generate funny response for where user disappeared
const generateDisappearanceResponse = async (disappearanceType, mood, interests) => {
  try {
    const prompt = `You are a sarcastic AI roasting someone for procrastinating.

User disappeared to: ${disappearanceType}
User mood: ${mood}
User interests: ${interests.join(', ')}

Generate ONE witty, sarcastic response (2-3 sentences max) about where they went.
Be funny, slightly judgmental, and reference their interests if relevant.
Keep it under 15 words per sentence.

IMPORTANT: Only return the roast, nothing else.`;

    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.9,
      max_tokens: 150
    });

    return {
      success: true,
      data: response.choices[0].message.content,
      tokens: response.usage.total_tokens
    };
  } catch (error) {
    console.error('OpenAI Disappearance Error:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
};

// Generate daily report summary
const generateReport = async (tasksPlanned, tasksCompleted, disappearances, commonExcuse) => {
  try {
    const prompt = `You are a witty AI generating a sarcastic daily procrastination report.

Report Stats:
- Tasks planned: ${tasksPlanned}
- Tasks completed: ${tasksCompleted}
- Disappearances: ${disappearances}
- Most common excuse: ${commonExcuse}

Generate a 3-4 sentence humorous summary of their procrastination day.
Be sarcastic but supportive. Reference the stats where relevant.

IMPORTANT: Only return the summary, nothing else.`;

    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.8,
      max_tokens: 200
    });

    return {
      success: true,
      data: response.choices[0].message.content,
      tokens: response.usage.total_tokens
    };
  } catch (error) {
    console.error('OpenAI Report Error:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
};

// Generate funny reasons to procrastinate on a task
const generateFunnyReasons = async (taskName, mood) => {
  try {
    const prompt = `You are a creative AI generating hilarious reasons to procrastinate.

Task: ${taskName}
User Mood: ${mood}

Generate 3-4 FUNNY, CREATIVE reasons why someone should procrastinate on this task instead of doing it.
Make them absurd, funny, and reference common procrastination habits.
Each reason should be 1-2 sentences max.

Format: 
- Reason 1
- Reason 2
- Reason 3

IMPORTANT: Only return the reasons list, nothing else.`;

    const response = await openai.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.9,
      max_tokens: 250
    });

    return {
      success: true,
      data: response.choices[0].message.content,
      tokens: response.usage.total_tokens
    };
  } catch (error) {
    console.error('OpenAI Reasons Error:', error.message);
    return {
      success: false,
      error: error.message
    };
  }
};

module.exports = {
  generatePrediction,
  generateDisappearanceResponse,
  generateReport,
  generateFunnyReasons
};
