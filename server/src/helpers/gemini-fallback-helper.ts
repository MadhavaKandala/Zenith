import axios from 'axios'

export async function getGeminiFallbackAnswer(
  utterance: string
): Promise<string> {
  const apiKey = process.env['GOOGLE_API_KEY']

  if (!apiKey) {
    return 'I need a Google API key to answer that, sir.'
  }

  try {
    const { data } = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      {
        contents: [
          {
            parts: [
              {
                text:
                  'You are Zenith, a personal AI assistant like JARVIS from Iron Man.\n' +
                  'Be concise, helpful, and address user as "sir".\n' +
                  'Answer in 1-3 sentences maximum.\n\n' +
                  `User: ${utterance}`
              }
            ]
          }
        ]
      },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 20_000
      }
    )

    return (
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      'I encountered an issue processing that request, sir.'
    )
  } catch {
    return "I'm having trouble connecting to my AI systems, sir."
  }
}
