import { useState, useRef, useEffect } from 'react'
import './App.css'
import * as api from './api'

function App() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState([
    'ALTERNATE HISTORY ENGINE - TERMINAL v2.0',
    '',
    'Type "help" for available commands',
    ''
  ])
  const [isLoading, setIsLoading] = useState(false)
  const inputRef = useRef(null)

  // Auto-focus input after any state change
  useEffect(() => {
    if (inputRef.current && !isLoading) {
      inputRef.current.focus()
    }
  }, [output, isLoading])

  // Format a single timeline event for display
  const formatEvent = (event) => {
    // Helper to wrap and indent long text
    const wrapText = (text, prefix = '') => {
      if (!text) return ['N/A']
      const lines = text.split('\n')
      return lines.map((line, idx) => idx === 0 ? line : `${prefix}${line}`)
    }

    const summaryLines = wrapText(event.event.summary || 'N/A', '         ')
    const detailLines = wrapText(event.event.details || 'N/A', '        ')

    const lines = [
      `Day ${event.day_index}:`,
      `Subtopic: ${event.subtopic}`,
      `Title: ${event.event.title || 'N/A'}`,
      `Date: ${event.event.date_in_universe || 'N/A'}`,
      `Location: ${event.event.location ? event.event.location.join(', ') : 'N/A'}`,
      `Summary: ${summaryLines[0]}`,
      ...summaryLines.slice(1),
      ``,
      `Details:`,
      ...detailLines,
      ''
    ]
    return lines
  }

  // Format multiple events as a list
  const formatEventList = (events) => {
    if (events.length === 0) {
      return ['No events found.', '']
    }
    const lines = []
    events.forEach((event) => {
      lines.push(`Day ${event.day_index}: ${event.event.title || event.subtopic}`)
      lines.push('')  // Add blank line after each event
    })
    return lines
  }

  // Format subtopics
  const formatSubtopics = (subtopics) => {
    if (subtopics.length === 0) {
      return ['No subtopics found.', '']
    }
    const lines = []
    subtopics.forEach((st) => {
      lines.push(`Day ${st.day_index}`)
      lines.push(`Subtopic: ${st.selected_subtopic}`)
      lines.push(`Reason: ${st.reason}`)
      lines.push(`Tags: ${st.tags.join(', ')}`)
      lines.push('')  // Blank line between entries
      lines.push('')  // Extra blank line for more spacing
    })
    return lines
  }

  // Format proposals
  const formatProposals = (proposals) => {
    if (proposals.length === 0) {
      return ['No proposals found.', '']
    }

    // Helper to wrap and indent long text
    const wrapText = (text, prefix = '') => {
      if (!text) return ['N/A']
      const lines = text.split('\n')
      return lines.map((line, idx) => idx === 0 ? line : `${prefix}${line}`)
    }

    const lines = []
    proposals.forEach((prop) => {
      const summaryLines = wrapText(prop.summary || 'N/A', '         ')
      const detailLines = wrapText(prop.details || 'N/A', '         ')

      lines.push(`Day ${prop.day_index} - Model ${prop.model}`)
      lines.push(`Subtopic: ${prop.subtopic}`)
      lines.push(`Title: ${prop.title || 'N/A'}`)
      lines.push('')  // Blank line before summary
      lines.push(`Summary: ${summaryLines[0]}`)
      lines.push(...summaryLines.slice(1))
      lines.push('')  // Blank line after summary
      lines.push(`Event Type: ${prop.event_type || 'N/A'}`)
      lines.push(`Date: ${prop.date_in_universe || 'N/A'}`)
      lines.push(`Location: ${prop.location ? prop.location.join(', ') : 'N/A'}`)
      lines.push(`Impact Score: ${prop.impact_score || 'N/A'}`)
      lines.push('')  // Blank line before details
      lines.push(`Details: ${detailLines[0]}`)
      lines.push(...detailLines.slice(1))
      lines.push('')  // Blank line after details
      lines.push('')  // Extra blank line between proposals
    })
    return lines
  }

  // Format judgements
  const formatJudgements = (judgements) => {
    if (judgements.length === 0) {
      return ['No judgements found.', '']
    }
    const lines = []
    judgements.forEach((jdg) => {
      lines.push(`Day ${jdg.day_index}`)
      lines.push(`Decision: ${jdg.decision}`)
      lines.push(`Reason: ${jdg.reason}`)
      lines.push('')  // Blank line between entries
      lines.push('')  // Extra blank line for more spacing
    })
    return lines
  }

  // Handle async commands
  const handleAsyncCommand = async (cmd) => {
    const parts = cmd.trim().split(/\s+/)
    const command = parts[0].toLowerCase()
    const args = parts.slice(1)

    setIsLoading(true)
    let response = []

    try {
      switch (command) {
        case 'timeline':
          if (args[0] === 'day' && args[1]) {
            const dayIndex = parseInt(args[1])
            const event = await api.getEventByDay(dayIndex)
            response = formatEvent(event)
          } else {
            const limit = args[0] ? parseInt(args[0]) : 10
            const events = await api.getTimeline(0, limit)
            response = ['Recent Timeline Events:', '', ...formatEventList(events)]
          }
          break

        case 'latest':
          const latestEvent = await api.getLatestEvent()
          response = ['Latest Event:', '', ...formatEvent(latestEvent)]
          break

        case 'subtopics':
          const limit1 = args[0] ? parseInt(args[0]) : 10
          const subtopics = await api.getSubtopics(0, limit1)
          response = ['Recent Subtopics:', '', ...formatSubtopics(subtopics)]
          break

        case 'proposals':
          const limit2 = args[0] ? parseInt(args[0]) : 10
          const proposals = await api.getProposals(0, limit2)
          response = ['Recent Proposals:', '', ...formatProposals(proposals)]
          break

        case 'judgements':
          const limit3 = args[0] ? parseInt(args[0]) : 10
          const judgements = await api.getJudgements(0, limit3)
          response = ['Recent Judgements:', '', ...formatJudgements(judgements)]
          break

        case 'status':
          const schedulerHealth = await api.getSchedulerHealth()
          response = [
            'Scheduler Status:',
            `  Status: ${schedulerHealth.status}`,
            `  Next Run: ${schedulerHealth.next_run_time || 'N/A'}`,
            `  Timezone: ${schedulerHealth.timezone || 'N/A'}`,
            ''
          ]
          break

        case 'health':
          const health = await api.getHealth()
          response = [`System Health: ${health.status}`, '']
          break

        case 'simulate':
          if (!args[0]) {
            response = ['Error: Admin key required', 'Usage: simulate <admin-key>', '']
          } else {
            const result = await api.simulateDay(args[0])
            response = [
              '✓ Simulation triggered successfully!',
              `  Day Index: ${result.day_index}`,
              `  Message: ${result.message}`,
              ''
            ]
          }
          break

        case 'reset':
          if (!args[0]) {
            response = ['Error: Admin key required', 'Usage: reset <admin-key>', '']
          } else {
            const result = await api.resetSimulation(args[0])
            response = [
              '✓ Simulation reset successfully!',
              `  Universe: ${result.universe_id}`,
              `  Message: ${result.message}`,
              '',
              '⚠ WARNING: All timeline data has been deleted!',
              ''
            ]
          }
          break

        default:
          response = null // Will be handled by sync commands
      }
    } catch (error) {
      response = [
        '✗ ERROR:',
        `  ${error.message}`,
        ''
      ]
    } finally {
      setIsLoading(false)
    }

    return response
  }

  // Handle all commands
  const handleCommand = async (cmd) => {
    if (!cmd.trim()) {
      setOutput([...output, '> ', ''])
      setInput('')
      return
    }

    const trimmedCmd = cmd.trim()
    const command = trimmedCmd.split(/\s+/)[0].toLowerCase()

    // Check if it's an async command
    const asyncCommands = ['timeline', 'latest', 'subtopics', 'proposals', 'judgements', 'status', 'health', 'simulate', 'reset']

    if (asyncCommands.includes(command)) {
      setOutput([...output, `> ${trimmedCmd}`, 'Loading...'])
      setInput('')

      const response = await handleAsyncCommand(trimmedCmd)
      if (response) {
        setOutput(prev => [...prev.slice(0, -1), ...response]) // Remove "Loading..." and add response
      } else {
        setOutput(prev => [...prev.slice(0, -1), `Command not found: ${command}`, 'Type "help" for available commands', ''])
      }
      return
    }

    // Handle sync commands
    let response = []

    switch (command) {
      case 'help':
        response = [
          'Available Commands:',
          '',
          '  help                    - Show this help message',
          '  clear                   - Clear the terminal',
          '  about                   - About this terminal',
          '  date                    - Show current date and time',
          '  info                    - Show admin key and usage',
          '',
          '  timeline [limit]        - Show recent timeline events (default: 10)',
          '  timeline day <number>   - Show specific day\'s event',
          '  latest                  - Show most recent event',
          '',
          '  status                  - Show scheduler status',
          '  health                  - Show system health',
          ''
        ]
        break

      case 'clear':
        setOutput([])
        setInput('')
        return

      case 'info':
        response = [
          'Admin Key Information:',
          '',
          'Your admin key is: secret-admin-key',
          '',
          'Usage:',
          '  simulate secret-admin-key    - Trigger daily simulation',
          '  reset secret-admin-key       - Reset universe (DESTRUCTIVE)',
          '',
          'Example:',
          '  > simulate secret-admin-key',
          ''
        ]
        break

      case 'about':
        response = [
          'ALTERNATE HISTORY ENGINE - TERMINAL v2.0',
          '',
          'An AI-powered engine for generating alternate history timelines.',
          '',
          'Current Universe: Cold War Without Apollo 11 Moon Landing',
          'Divergence Point: July 16, 1969',
          '',
          'Tech Stack:',
          '  Frontend: React 19 + Vite',
          '  Backend: FastAPI + MongoDB',
          '  AI Models: Qwen, Gemini, DeepSeek, Llama 3.3',
          '',
          'Built with ❤️ for exploring what-if scenarios',
          ''
        ]
        break

      case 'date':
        response = [new Date().toString(), '']
        break

      default:
        response = [`Command not found: ${command}`, 'Type "help" for available commands', '']
    }

    setOutput([...output, `> ${trimmedCmd}`, ...response])
    setInput('')
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleCommand(input)
    }
  }

  return (
    <div className="crt-container" onClick={() => inputRef.current?.focus()}>
      <div className="crt-content">
        <div className="terminal-output">
          {output.map((line, index) => (
            <div key={index} className={line.startsWith('>') ? "terminal-command" : "terminal-text"}>
              {line}
            </div>
          ))}
        </div>
        <div className="terminal-input-line">
          <span className="terminal-prompt"></span>
          <span className="input-text">{input}</span>
          <span className={isLoading ? "cursor loading" : "cursor"}></span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            className="terminal-input"
            ref={inputRef}
            autoFocus
            spellCheck="false"
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  )
}

export default App
