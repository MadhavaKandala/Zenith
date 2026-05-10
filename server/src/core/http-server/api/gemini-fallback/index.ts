import type { FastifyPluginAsync } from 'fastify'

import { postGeminiFallback } from '@/core/http-server/api/gemini-fallback/post'
import type { APIOptions } from '@/core/http-server/http-server'

export const geminiFallbackPlugin: FastifyPluginAsync<APIOptions> = async (
  fastify,
  options
) => {
  await fastify.register(postGeminiFallback, options)
}
