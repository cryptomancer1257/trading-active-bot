'use client'

import { useState, useEffect, useRef } from 'react'
import { ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline'
import { extractVariables, validateVariables, AVAILABLE_VARIABLES } from '@/utils/promptVariables'
import dynamic from 'next/dynamic'
import type { Monaco } from '@monaco-editor/react'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { 
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-900 rounded">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
        <p className="text-gray-400 text-sm">Loading Editor...</p>
      </div>
    </div>
  )
})

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
  const [wordWrap, setWordWrap] = useState<boolean>(true)
  const [syntaxHighlight, setSyntaxHighlight] = useState<boolean>(true)
  const [autoFocus, setAutoFocus] = useState<boolean>(true)
  const [showVariables, setShowVariables] = useState<boolean>(false)
  const editorRef = useRef<any>(null)

  // Sync internal content with prop content
  useEffect(() => {
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
    
    // Use Monaco editor instance to insert variable at cursor position
    if (editorRef.current) {
      const editor = editorRef.current
      const selection = editor.getSelection()
      const range = {
        startLineNumber: selection.startLineNumber,
        startColumn: selection.startColumn,
        endLineNumber: selection.endLineNumber,
        endColumn: selection.endColumn
      }
      
      // Insert variable at cursor position
      editor.executeEdits('', [{
        range: range,
        text: variableText,
        forceMoveMarkers: true
      }])
      
      // Focus editor and move cursor after inserted text
      editor.focus()
    } else {
      // Fallback: append to end if editor not found
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
    <div className={`border border-gray-600 rounded-lg bg-gray-900 overflow-hidden ${className}`}>
      {/* Toolbar */}
      {!readOnly && !isFullscreen && (
        <div className="border-b border-gray-600 p-3 flex items-center justify-between bg-gray-800">
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
              onClick={() => setShowVariables(!showVariables)}
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
      {!readOnly && !isFullscreen && showVariables && (
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
        className={`${isFullscreen ? 'fixed inset-0 z-50 bg-[#1e1e1e] flex flex-col' : 'flex flex-col'}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Fullscreen Toolbar */}
        {isFullscreen && !readOnly && (
          <div className="border-b border-gray-700 p-3 bg-gray-900 flex items-center justify-between">
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
                onClick={() => setShowVariables(!showVariables)}
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
          </div>
        )}

        {/* Variables Panel in Fullscreen */}
        {isFullscreen && !readOnly && showVariables && (
          <div className="border-b border-gray-700 p-4 bg-gray-800 max-h-64 overflow-y-auto">
            <div className="flex items-start space-x-2">
              <span className="text-blue-400 text-sm">🔧</span>
              <div className="text-xs text-gray-400">
                <p className="font-medium mb-2 text-gray-300">Available Variables:</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {Object.entries(AVAILABLE_VARIABLES).map(([key, variable]) => (
                    <div key={key} className="flex items-center space-x-2 p-2 bg-gray-900 rounded">
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

        {/* Editor/Preview Area */}
        <div className="flex-1 overflow-hidden">
          {previewMode ? (
            <div 
              className="p-6 w-full text-base bg-gray-800 text-gray-200 overflow-y-auto cursor-default"
              style={{ height: isFullscreen ? 'calc(100vh - 64px)' : '600px' }}
              dangerouslySetInnerHTML={{ 
                __html: renderMarkdown(internalContent || 'No content to preview') 
              }}
            />
          ) : (
            <div className="w-full relative" style={{ height: isFullscreen ? 'calc(100vh - 64px)' : '600px' }}>
              <MonacoEditor
                height={isFullscreen ? 'calc(100vh - 64px)' : '600px'}
                defaultLanguage="markdown"
                theme="vs-dark"
                value={internalContent}
                onChange={(value) => {
                  if (readOnly) return
                  const newContent = value || ''
                  setInternalContent(newContent)
                  onChange(newContent)
                }}
                options={{
                  readOnly: readOnly,
                  minimap: { enabled: true },
                  fontSize: 14,
                  lineNumbers: 'on',
                  wordWrap: wordWrap ? 'on' : 'off',
                  automaticLayout: true,
                  scrollBeyondLastLine: false,
                  renderWhitespace: 'selection',
                  cursorBlinking: 'smooth',
                  cursorStyle: 'line',
                  lineHeight: 22,
                  padding: { top: 16, bottom: 16 },
                  folding: true,
                  foldingStrategy: 'indentation',
                  showFoldingControls: 'always',
                  smoothScrolling: true,
                  quickSuggestions: true,
                  suggestOnTriggerCharacters: true,
                  acceptSuggestionOnEnter: 'on',
                  tabCompletion: 'on',
                  wordBasedSuggestions: 'allDocuments',
                  bracketPairColorization: {
                    enabled: true
                  },
                  guides: {
                    indentation: true,
                    bracketPairs: true
                  },
                  formatOnPaste: true,
                  formatOnType: true
                }}
                onMount={(editor, monaco) => {
                  // Store editor instance
                  editorRef.current = editor

                  // Configure markdown language features
                  monaco.languages.setLanguageConfiguration('markdown', {
                    wordPattern: /(-?\d*\.\d\w*)|([^\`\~\!\@\#\%\^\&\*\(\)\-\=\+\[\{\]\}\\\|\;\:\'\"\,\.\<\>\/\?\s]+)/g,
                  })

                  // Add custom variable highlighting and autocomplete
                  monaco.languages.registerCompletionItemProvider('markdown', {
                    provideCompletionItems: (model, position) => {
                      const word = model.getWordUntilPosition(position)
                      const suggestions = Object.entries(AVAILABLE_VARIABLES).map(([key, variable]) => ({
                        label: `{${key}}`,
                        kind: monaco.languages.CompletionItemKind.Variable,
                        documentation: variable.description,
                        insertText: `{${key}}`,
                        range: {
                          startLineNumber: position.lineNumber,
                          endLineNumber: position.lineNumber,
                          startColumn: word.startColumn,
                          endColumn: word.endColumn
                        }
                      }))
                      return { suggestions }
                    },
                    triggerCharacters: ['{']
                  })

                  // Focus editor if autoFocus is true
                  if (autoFocus && !readOnly) {
                    editor.focus()
                  }
                }}
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
              <p className="font-medium mb-2 text-gray-300">Editor Flavored Markdown Tips:</p>
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