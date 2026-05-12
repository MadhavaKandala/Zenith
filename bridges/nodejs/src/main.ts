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

  let domains: fs.Dirent[] = []
  try {
    domains = fs.readdirSync(skillsDir, { withFileTypes: true }).filter(d => d.isDirectory())
  } catch (err) {
    console.error(`[Bridge] Error reading skills directory ${skillsDir}:`, err)
    return routes
  }

  for (const domain of domains) {
    const domainPath = path.join(skillsDir, domain.name)
    let skills: fs.Dirent[] = []
    try {
      skills = fs.readdirSync(domainPath, { withFileTypes: true }).filter(d => d.isDirectory())
    } catch (err) {
      console.error(`[Bridge] Error reading domain directory ${domainPath}:`, err)
      continue
    }

    for (const skill of skills) {
      const skillPath = path.join(domainPath, skill.name)
      const configPath = path.join(skillPath, 'skill.json')

      if (fs.existsSync(configPath)) {
        let bridge: 'python' | 'nodejs' = 'python'
        try {
          const configStr = fs.readFileSync(configPath, 'utf8')
          const config = JSON.parse(configStr)
          if (config.bridge === 'nodejs') bridge = 'nodejs'
        } catch (e) {
          // Default to python on error
        }

        routes.push({
          domain: domain.name,
          skill: skill.name,
          bridge,
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
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9)
    const intentFilePath = path.join(tmpDir, `intent-object-${uniqueSuffix}.json`)
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

    let timeoutId = setTimeout(() => {
      pythonProcess.kill()
      try { fs.promises.unlink(intentFilePath) } catch (e) {}
      resolve({
        success: false,
        output: '',
        executionTime: Date.now() - startTime,
        error: 'Python process timed out',
      })
    }, 30000)

    pythonProcess.on('close', (code: number | null) => {
      clearTimeout(timeoutId)
      try { fs.promises.unlink(intentFilePath) } catch (e) {}
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
      clearTimeout(timeoutId)
      try { fs.promises.unlink(intentFilePath) } catch (e) {}
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
 * Execute a Node.js skill natively.
 */
async function executeNodeJsSkill(intentObj: IntentObject): Promise<SkillExecutionResult> {
  const startTime = Date.now()
  try {
    const actionPathTs = path.join(process.cwd(), 'skills', intentObj.domain, intentObj.skill, 'src', 'actions', `${intentObj.action}.ts`)
    const actionPathJs = path.join(process.cwd(), 'skills', intentObj.domain, intentObj.skill, 'src', 'actions', `${intentObj.action}.js`)
    
    let actionPath = ''
    if (fs.existsSync(actionPathTs)) actionPath = actionPathTs
    else if (fs.existsSync(actionPathJs)) actionPath = actionPathJs
    else throw new Error(`Action module not found for ${intentObj.domain}.${intentObj.skill}.${intentObj.action}`)

    // Dynamically import the skill action module
    // We expect the module to export a function with the same name as the action, or a default function
    const module = await import(actionPath)
    const actionFn = module[intentObj.action] || module.default

    if (typeof actionFn !== 'function') {
      throw new Error(`Action function '${intentObj.action}' or default export not found in module`)
    }

    const result = await actionFn(intentObj)
    const outputStr = typeof result === 'string' ? result : JSON.stringify(result)

    return {
      success: true,
      output: outputStr,
      executionTime: Date.now() - startTime
    }
  } catch (err: any) {
    return {
      success: false,
      output: '',
      executionTime: Date.now() - startTime,
      error: err.message || String(err)
    }
  }
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

  if (matchedRoute.bridge === 'python') {
    return executePythonSkill(intentObj)
  } else if (matchedRoute.bridge === 'nodejs') {
    return executeNodeJsSkill(intentObj)
  } else {
    return {
      success: false,
      output: '',
      executionTime: 0,
      error: `Unknown bridge type ${matchedRoute.bridge}`,
    }
  }
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
export { discoverSkills, routeIntent, executePythonSkill, executeNodeJsSkill, IntentObject, SkillExecutionResult }
