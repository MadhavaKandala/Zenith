import { join } from 'node:path'

import Fastify, { FastifySchema } from 'fastify'
import fastifyStatic from '@fastify/static'
import { Type } from '@sinclair/typebox'
import type { Static } from '@sinclair/typebox'
import { AccessToken, AgentDispatchClient } from 'livekit-server-sdk'

import {
  LEON_VERSION,
  LEON_NODE_ENV,
  HAS_OVER_HTTP,
  IS_TELEMETRY_ENABLED
} from '@/constants'
import { LogHelper } from '@/helpers/log-helper'
import { DateHelper } from '@/helpers/date-helper'
import { corsMidd } from '@/core/http-server/plugins/cors'
import { otherMidd } from '@/core/http-server/plugins/other'
import { infoPlugin } from '@/core/http-server/api/info'
import { downloadsPlugin } from '@/core/http-server/api/downloads'
import { geminiFallbackPlugin } from '@/core/http-server/api/gemini-fallback'
import { keyMidd } from '@/core/http-server/plugins/key'
import { NLU, BRAIN } from '@/core'

const API_VERSION = 'v1'
const LIVEKIT_DISPATCH_TIMEOUT_MS = 12_000

export interface APIOptions {
  apiVersion: string
}

const postQuerySchema = {
  body: Type.Object({
    utterance: Type.String()
  })
} satisfies FastifySchema

interface PostQuerySchema {
  body: Static<typeof postQuerySchema.body>
}

function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  label: string
): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      reject(new Error(`${label} timed out after ${timeoutMs}ms`))
    }, timeoutMs)

    promise
      .then((value) => {
        clearTimeout(timeout)
        resolve(value)
      })
      .catch((error) => {
        clearTimeout(timeout)
        reject(error)
      })
  })
}

export default class HTTPServer {
  private static instance: HTTPServer

  private fastify = Fastify()

  public httpServer = this.fastify.server

  constructor(public readonly host: string, public readonly port: number) {
    if (!HTTPServer.instance) {
      LogHelper.title('HTTP Server')
      LogHelper.success('New instance')

      HTTPServer.instance = this
    }

    this.host = host
    this.port = port
  }

  /**
   * Server entry point
   */
  public async init(): Promise<void> {
    this.fastify.addHook('onRequest', corsMidd)
    this.fastify.addHook('preValidation', otherMidd)

    LogHelper.title('Initialization')
    LogHelper.info(`The current env is ${LEON_NODE_ENV}`)
    LogHelper.info(`The current version is ${LEON_VERSION}`)

    LogHelper.info(`The current time zone is ${DateHelper.getTimeZone()}`)

    const isTelemetryEnabled = IS_TELEMETRY_ENABLED ? 'enabled' : 'disabled'
    LogHelper.info(`Telemetry ${isTelemetryEnabled}`)

    await this.bootstrap()
  }

  /**
   * Bootstrap API
   */
  private async bootstrap(): Promise<void> {
    // Render the web app
    this.fastify.register(fastifyStatic, {
      root: join(process.cwd(), 'app', 'dist'),
      prefix: '/'
    })
    this.fastify.get('/', (_request, reply) => {
      reply.sendFile('index.html')
    })

    this.fastify.get('/api/livekit-token', async (request, reply) => {
      try {
        const apiKey = process.env['LIVEKIT_API_KEY']
        const apiSecret = process.env['LIVEKIT_API_SECRET']
        const url = process.env['LIVEKIT_URL']
        const query = (request.query || {}) as {
          voiceId?: string
          voiceLabel?: string
        }

        if (!apiKey || !apiSecret || !url) {
          return reply.status(500).send({
            error: 'LiveKit env vars missing',
            missing: {
              LIVEKIT_API_KEY: !apiKey,
              LIVEKIT_API_SECRET: !apiSecret,
              LIVEKIT_URL: !url
            }
          })
        }

        const roomName = `zenith-room-${Date.now()}`
        const voiceId =
          typeof query.voiceId === 'string'
            ? query.voiceId.replace(/[^A-Za-z0-9]/g, '').slice(0, 64)
            : ''
        const voiceLabel =
          typeof query.voiceLabel === 'string'
            ? query.voiceLabel.replace(/[^\w\s-]/g, '').trim().slice(0, 48)
            : ''
        const dispatchHost = url
          .replace(/^wss:/, 'https:')
          .replace(/^ws:/, 'http:')
        const dispatchClient = new AgentDispatchClient(
          dispatchHost,
          apiKey,
          apiSecret
        )

        await withTimeout(
          dispatchClient.createDispatch(roomName, 'zenith', {
            metadata: JSON.stringify({
              source: 'zenith-webapp',
              voiceId,
              voiceLabel
            })
          }),
          LIVEKIT_DISPATCH_TIMEOUT_MS,
          'LiveKit dispatch'
        )

        const at = new AccessToken(apiKey, apiSecret, {
          identity: 'zenith-user-' + Date.now(),
          ttl: '1h'
        })
        at.addGrant({
          roomJoin: true,
          room: roomName,
          canPublish: true,
          canSubscribe: true
        })

        const token = await at.toJwt()
        return reply.send({
          token,
          url,
          room: roomName,
          agentName: 'zenith',
          voiceId,
          voiceLabel
        })
      } catch (err) {
        return reply.status(500).send({ error: String(err) })
      }
    })

    this.fastify.register(infoPlugin, { apiVersion: API_VERSION })
    this.fastify.register(downloadsPlugin, { apiVersion: API_VERSION })
    this.fastify.register(geminiFallbackPlugin, { apiVersion: API_VERSION })

    if (HAS_OVER_HTTP) {
      this.fastify.register((instance, _opts, next) => {
        instance.addHook('preHandler', keyMidd)

        instance.route<{
          Body: PostQuerySchema['body']
        }>({
          method: 'POST',
          url: '/api/query',
          schema: postQuerySchema,
          handler: async (request, reply) => {
            const { utterance } = request.body

            try {
              BRAIN.isMuted = true
              const data = await NLU.process(utterance)

              reply.send({
                ...data,
                success: true
              })
            } catch (error) {
              const message = error instanceof Error ? error.message : error
              reply.statusCode = 500
              reply.send({
                message,
                success: false
              })
            }
          }
        })

        // TODO: reimplement skills routes once the new core is ready
        // server.generateSkillsRoutes(instance)

        next()
      })
    }

    try {
      await this.listen()
    } catch (e) {
      LogHelper.error((e as Error).message)
    }
  }

  /**
   * Launch server
   */
  private async listen(): Promise<void> {
    this.fastify.listen(
      {
        port: this.port,
        host: '0.0.0.0'
      },
      () => {
        LogHelper.title('Initialization')
        LogHelper.success(`Server is available at ${this.host}:${this.port}`)
      }
    )
  }
}
