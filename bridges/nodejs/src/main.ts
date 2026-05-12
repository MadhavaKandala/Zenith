import { VERSION } from './version'
import { spawn, ChildProcess } from 'child_process'
import * as path from 'path'
import * as fs from 'fs'

/**
 * Zenith Node.js Bridge
 *
 * Routes skill execution requests from the server to the appropriate
 * Python skill modules. Handles inter-process communication between
 * the Node.js server and the Python skill runtime.
 */

interface IntentObject {
  domain: string
  skill: string
  action: string
  lang: string
  utterance: string
  entities: Record<string, unknown>[]
  slots: Record<string, unknown>
  current_entities: Record<string, unknown>[]
  current_resolvers: Record<string, unknown>[]
  resolvers: Record<string, unknown>[]
}

interface SkillExecutionResult {
  success: boolean
  output: string
  executionTime: number
  error?: string
}

interface SkillRoute {
  domain: string
  skill: string
  bridge: 'python' | 'nodejs'
  configPath: string
}

/**
 * Discover available skills by scanning the skills directory.
 */
function discoverSkills(skillsDir: string): SkillRoute[] {
  const routes: SkillRoute[] = []

  if (!fs.existsSync(skillsDir)) {
    console.warn(`[Bridge] Skills directory not found: ${skillsDir}`)
    return routes
  }

  const domains = fs.readdirSync(skillsDir, { withFileTypes: true })
    .filter(d => d.isDirectory())

  for (const domain of domains) {
    const domainPath = path.join(skillsDir, domain.name)
    const skills = fs.readdirSync(domainPath, { withFileTypes: true })
      .filter(d => d.isDirectory())

    for (const skill of skills) {
      const skillPath = path.join(domainPath, skill.name)
      const configPath = path.join(skillPath, 'skill.json')

      if (fs.existsSync(configPath)) {
        routes.push({
          domain: domain.name,
          skill: skill.name,
          bridge: 'python', // Default to Python bridge
          configPath,
        })
      }
    }
  }

  return routes
}

/**
 * Execute a Python skill via the Python bridge.
 */
function executePythonSkill(intentObj: IntentObject): Promise<SkillExecutionResult> {
  return new Promise((resolve) => {
    const startTime = Date.now()
    const pipfile = path.join('bridges', 'python', 'src', 'Pipfile')
    const mainScript = path.join('bridges', 'python', 'src', 'main.py')

    // Write intent object to a temporary file for the Python bridge
    const tmpDir = path.join('server', 'src', 'tmp')
    if (!fs.existsSync(tmpDir)) {
      fs.mkdirSync(tmpDir, { recursive: true })
    }
    const intentFilePath = path.join(tmpDir, 'intent-object.json')
    fs.writeFileSync(intentFilePath, JSON.stringify(intentObj, null, 2))

    const pythonProcess: ChildProcess = spawn(
      `pipenv run python ${mainScript} ${intentFilePath}`,
      {
        shell: true,
        env: { ...process.env, PIPENV_PIPFILE: pipfile },
      }
    )

    let stdout = ''
    let stderr = ''

    pythonProcess.stdout?.on('data', (data: Buffer) => {
      stdout += data.toString()
    })

    pythonProcess.stderr?.on('data', (data: Buffer) => {
      stderr += data.toString()
    })

    pythonProcess.on('close', (code: number | null) => {
      const executionTime = Date.now() - startTime

      if (code === 0) {
        resolve({
          success: true,
          output: stdout.trim(),
          executionTime,
        })
      } else {
        resolve({
          success: false,
          output: stdout.trim(),
          executionTime,
          error: stderr.trim() || `Process exited with code ${code}`,
        })
      }
    })

    pythonProcess.on('error', (err: Error) => {
      resolve({
        success: false,
        output: '',
        executionTime: Date.now() - startTime,
        error: err.message,
      })
    })
  })
}

/**
 * Route an intent to the correct skill handler.
 */
async function routeIntent(intentObj: IntentObject): Promise<SkillExecutionResult> {
  const skillsDir = path.join(process.cwd(), 'skills')
  const routes = discoverSkills(skillsDir)

  const matchedRoute = routes.find(
    r => r.domain === intentObj.domain && r.skill === intentObj.skill
  )

  if (!matchedRoute) {
    return {
      success: false,
      output: '',
      executionTime: 0,
      error: `No skill found for ${intentObj.domain}.${intentObj.skill}`,
    }
  }

  console.log(
    `[Bridge] Routing ${intentObj.domain}.${intentObj.skill}.${intentObj.action} via ${matchedRoute.bridge}`
  )

  return executePythonSkill(intentObj)
}

/**
 * Print bridge status summary.
 */
function printBridgeSummary(): void {
  const skillsDir = path.join(process.cwd(), 'skills')
  const routes = discoverSkills(skillsDir)

  console.log('[Zenith] Node.js Bridge')
  console.log(`  version: ${VERSION}`)
  console.log(`  runtime: ${process.version}`)
  console.log(`  skills discovered: ${routes.length}`)
  console.log(`  status: ready`)

  if (routes.length > 0) {
    console.log('  registered skills:')
    for (const route of routes) {
      console.log(`    - ${route.domain}/${route.skill} (${route.bridge})`)
    }
  }
}

// ── Main Entry Point ──────────────────────────────────────────────────

printBridgeSummary()

// Handle IPC messages from the server
process.on('message', async (msg: { type: string; payload: IntentObject }) => {
  if (msg.type === 'execute_skill') {
    const result = await routeIntent(msg.payload)
    if (process.send) {
      process.send({ type: 'skill_result', payload: result })
    }
  }
})

// Export for testing
export { discoverSkills, routeIntent, executePythonSkill, IntentObject, SkillExecutionResult }
