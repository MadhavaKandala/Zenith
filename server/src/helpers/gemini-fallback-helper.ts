interface GeminiGenerateContentResponse {
  candidates?: Array<{
    content?: {
      parts?: Array<{
        text?: string
      }>
    }
  }>
}

interface FetchResponseLike {
  json(): Promise<GeminiGenerateContentResponse>
}

declare const fetch: (
  input: string,
  init?: {
    method?: string
    headers?: Record<string, string>
    body?: string
  }
) => Promise<FetchResponseLike>

export async function getGeminiFallbackAnswer(
  utterance: string
): Promise<string> {
  const apiKey = process.env['GOOGLE_API_KEY']

  if (!apiKey) {
    return 'I need a Google API key to answer that, sir.'
  }

  try {
    const geminiRes = await Promise.race<FetchResponseLike>([
      fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
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
          })
        },
      ),
      new Promise<never>((_resolve, reject) => {
        setTimeout(() => {
          reject(new Error('Gemini fallback timed out'))
        }, 20_000)
      })
    ])
    const data = (await geminiRes.json()) as GeminiGenerateContentResponse

    return (
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      'I encountered an issue processing that request, sir.'
    )
  } catch {
    return "I'm having trouble connecting to my AI systems, sir."
  }
}
