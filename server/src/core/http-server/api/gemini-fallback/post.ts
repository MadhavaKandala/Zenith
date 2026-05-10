import type { FastifyPluginAsync, FastifySchema } from 'fastify'
import { Type } from '@sinclair/typebox'
import type { Static } from '@sinclair/typebox'

import { LogHelper } from '@/helpers/log-helper'
import { getGeminiFallbackAnswer } from '@/helpers/gemini-fallback-helper'
import type { APIOptions } from '@/core/http-server/http-server'

const postGeminiFallbackSchema = {
  body: Type.Object({
    utterance: Type.String()
  })
} satisfies FastifySchema

interface PostGeminiFallbackSchema {
  body: Static<typeof postGeminiFallbackSchema.body>
}

export const postGeminiFallback: FastifyPluginAsync<APIOptions> = async (
  fastify
) => {
  fastify.route<{
    Body: PostGeminiFallbackSchema['body']
  }>({
    method: 'POST',
    url: '/api/gemini-fallback',
    schema: postGeminiFallbackSchema,
    handler: async (request, reply) => {
      LogHelper.title('POST /gemini-fallback')

      const answer = await getGeminiFallbackAnswer(request.body.utterance)

      reply.send({ answer })
    }
  })
}
