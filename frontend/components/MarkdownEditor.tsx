'use client'

import { useState, useEffect, useRef } from 'react'
import { ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline'
import { extractVariables, validateVariables, AVAILABLE_VARIABLES } from '@/utils/promptVariables'

interface MarkdownEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
  className?: string
  readOnly?: boolean
}

export default function MarkdownEditor({ 
  content, 
  onChange, 
  placeholder = "Enter your content here...",
  className = "",
  readOnly = false
}: MarkdownEditorProps) {
  const [previewMode, setPreviewMode] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [internalContent, setInternalContent] = useState(content)
  const [fontSize, setFontSize] = useState<'sm' | 'base' | 'lg'>('lg')
  const [lineHeight, setLineHeight] = useState<'tight' | 'normal' | 'relaxed'>('relaxed')
  const [wordWrap, setWordWrap] = useState<boolean>(true)
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [syntaxHighlight, setSyntaxHighlight] = useState<boolean>(true)
  const [spellCheck, setSpellCheck] = useState<boolean>(true)
  const [autoComplete, setAutoComplete] = useState<boolean>(true)
  const [autoFocus, setAutoFocus] = useState<boolean>(true)
  const [autoResize, setAutoResize] = useState<boolean>(true)
  const [autoScroll, setAutoScroll] = useState<boolean>(true)
  const [showVariables, setShowVariables] = useState<boolean>(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sync internal content with prop content
  useEffect(() => {
    console.log('🔄 MarkdownEditor content sync:', { content, internalContent })
    setInternalContent(content)
  }, [content])

  // Function to highlight variables in content
  const highlightVariables = (text: string) => {
    if (!syntaxHighlight) return text
    
    const variables = extractVariables(text)
    let highlightedText = text
    
    variables.forEach(variable => {
      const regex = new RegExp(`\\{${variable}\\}`, 'g')
      highlightedText = highlightedText.replace(regex, `<span class="bg-blue-100 text-blue-800 px-1 py-0.5 rounded text-xs font-mono">{${variable}}</span>`)
    })
    
    return highlightedText
  }

  // Function to insert variable into content
  const insertVariable = (variable: string) => {
    const variableText = `{${variable}}`
    
    // Use ref to get textarea element
    if (textareaRef.current) {
      const textarea = textareaRef.current
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const beforeCursor = internalContent.substring(0, start)
      const afterCursor = internalContent.substring(end)
      const newContent = beforeCursor + variableText + afterCursor
      
      setInternalContent(newContent)
      onChange(newContent)
      
      // Set cursor position after the inserted variable
      setTimeout(() => {
        const newCursorPos = start + variableText.length
        textarea.setSelectionRange(newCursorPos, newCursorPos)
        textarea.focus()
      }, 0)
    } else {
      // Fallback: append to end if textarea not found
      const newContent = internalContent + variableText
      setInternalContent(newContent)
      onChange(newContent)
    }
    
    // Don't auto-close variables panel - let developer close manually
  }

  // Fullscreen keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F11') {
        e.preventDefault()
        setIsFullscreen(!isFullscreen)
      }
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isFullscreen])

  const markdownTips = [
    { syntax: '**bold**', description: 'Bold text' },
    { syntax: '*italic*', description: 'Italic text' },
    { syntax: '`code`', description: 'Inline code' },
    { syntax: '# Heading', description: 'Heading 1' },
    { syntax: '## Heading', description: 'Heading 2' },
    { syntax: '- List item', description: 'Bullet list' },
    { syntax: '1. Item', description: 'Numbered list' },
    { syntax: '> Quote', description: 'Blockquote' },
    { syntax: '```code```', description: 'Code block' },
    { syntax: '[Link](url)', description: 'Link' },
    { syntax: '![Image](url)', description: 'Image' },
    { syntax: '---', description: 'Horizontal rule' },
    { syntax: '- [ ] Task', description: 'Task list' },
    { syntax: '| Table |', description: 'Table' }
  ]

  const renderMarkdown = (text: string) => {
    // Simple markdown rendering with variable highlighting
    let rendered = text
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/`(.*)`/gim, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
      .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2">$1</a>')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/gim, '<img src="$2" alt="$1" />')
      .replace(/^---$/gim, '<hr />')
      .replace(/\n/g, '<br />')
    
    // Apply variable highlighting
    if (syntaxHighlight) {
      rendered = highlightVariables(rendered)
    }
    
    return rendered
  }

  return (
    <div className={`border border-gray-600 rounded-lg bg-gray-800 ${className}`}>
      {/* Toolbar */}
      {!readOnly && (
        <div className="border-b border-gray-600 p-3 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setPreviewMode(false)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                !previewMode 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => setPreviewMode(true)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                previewMode 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Preview
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => {
                console.log('🔧 Variables button clicked, current state:', showVariables)
                setShowVariables(!showVariables)
              }}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                showVariables
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              title="Insert Variables"
            >
              Variables
            </button>
            <button
              type="button"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="px-3 py-1 rounded text-sm transition-colors bg-gray-700 text-gray-300 hover:bg-gray-600"
              title="Toggle Fullscreen (F11)"
            >
              {isFullscreen ? <ArrowsPointingInIcon className="h-4 w-4" /> : <ArrowsPointingOutIcon className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}

      {/* Variables Panel - Show at top of editor content */}
      {!readOnly && showVariables && (
        <div className="border-b border-gray-600 p-4 bg-gray-900 max-h-64 overflow-y-auto">
          <div className="flex items-start space-x-2">
            <span className="text-blue-400 text-sm">🔧</span>
            <div className="text-xs text-gray-400">
              <p className="font-medium mb-2 text-gray-300">Available Variables:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.entries(AVAILABLE_VARIABLES).map(([key, variable]) => (
                  <div key={key} className="flex items-center space-x-2 p-2 bg-gray-800 rounded">
                    <button
                      type="button"
                      onClick={() => insertVariable(key)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                    >
                      Insert
                    </button>
                    <div className="flex-1">
                      <code className="bg-gray-700 px-1 rounded text-xs">{`{${key}}`}</code>
                      <p className="text-xs text-gray-500 mt-1">{variable.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-2 text-xs text-gray-500">
                Click "Insert" to add variables to your prompt. Variables will be replaced with actual values when the prompt is used.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Editor Content */}
      <div 
        className={`${isFullscreen ? 'fixed inset-0 z-50 bg-gray-900' : ''} min-h-[600px] flex flex-col`}
        onClick={(e) => e.stopPropagation()}
      >
        {isFullscreen && (
          <div className="absolute top-4 right-4 z-10">
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setIsFullscreen(false)
              }}
              className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
              title="Exit Fullscreen (Esc)"
            >
              <ArrowsPointingInIcon className="h-5 w-5" />
            </button>
          </div>
        )}

        {/* Editor/Preview Area */}
        <div className="flex-1 overflow-hidden">
          {previewMode ? (
            <div 
              className="p-6 w-full text-base bg-gray-800 rounded-lg text-gray-200 h-full overflow-y-auto cursor-default"
              dangerouslySetInnerHTML={{ 
                __html: renderMarkdown(internalContent || 'No content to preview') 
              }}
            />
          ) : (
            <div className="relative h-full w-full">
              {/* Preview-style background */}
              <div 
                className="p-6 w-full text-base bg-gray-800 rounded-lg h-full overflow-y-auto whitespace-pre-wrap text-gray-100 cursor-text"
                style={{
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                  lineHeight: '1.6'
                }}
              >
                {internalContent || placeholder}
              </div>
              
              {/* Invisible textarea overlay */}
              <textarea
                ref={textareaRef}
                value={internalContent}
                onChange={(e) => {
                  if (readOnly) return
                  const newContent = e.target.value
                  console.log('📝 MarkdownEditor onChange:', { newContent: newContent.substring(0, 100) + '...' })
                  setInternalContent(newContent)
                  onChange(newContent)
                }}
                placeholder={placeholder}
                readOnly={readOnly}
                className="absolute inset-0 w-full p-6 bg-transparent resize-none focus:outline-none text-transparent overflow-y-auto cursor-text"
                style={{ 
                  resize: 'none',
                  fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                  fontSize: '1rem',
                  lineHeight: '1.6',
                  caretColor: '#3b82f6' // Blue caret color
                }}
                spellCheck={spellCheck}
                autoComplete={autoComplete ? 'on' : 'off'}
                autoFocus={autoFocus}
              />
            </div>
          )}
        </div>

      </div>

      {/* Markdown Tips */}
      {!isFullscreen && (
        <div className="border-t border-gray-600 p-4 bg-gray-900">
          <div className="flex items-start space-x-2">
            <span className="text-yellow-400 text-sm">💡</span>
            <div className="text-xs text-gray-400">
              <p className="font-medium mb-2 text-gray-300">GitLab Flavored Markdown Tips:</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {markdownTips.map((tip, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <code className="bg-gray-700 px-1 py-0.5 rounded text-xs">{tip.syntax}</code>
                    <span className="text-xs text-gray-500">{tip.description}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}