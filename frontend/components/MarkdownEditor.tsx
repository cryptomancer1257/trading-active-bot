'use client'

import { useState, useEffect } from 'react'
import { ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/react/24/outline'

interface MarkdownEditorProps {
  content: string
  onChange: (content: string) => void
  placeholder?: string
  className?: string
}

export default function MarkdownEditor({ 
  content, 
  onChange, 
  placeholder = "Enter your content here...",
  className = ""
}: MarkdownEditorProps) {
  const [previewMode, setPreviewMode] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [internalContent, setInternalContent] = useState(content)

  // Sync internal content with prop content
  useEffect(() => {
    setInternalContent(content)
  }, [content])

  // Keyboard shortcut for fullscreen (F11 or Ctrl+Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F11' || (e.ctrlKey && e.key === 'Enter')) {
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
    // Simple markdown rendering
    return text
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/`(.*)`/gim, '<code>$1</code>')
      .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2">$1</a>')
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/gim, '<img src="$2" alt="$1" />')
      .replace(/^---$/gim, '<hr />')
      .replace(/\n/g, '<br />')
  }

  return (
    <div className={`border border-gray-600 rounded-lg bg-gray-800 ${className}`}>
      {/* Toolbar */}
      <div className="border-b border-gray-600 p-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPreviewMode(false)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              !previewMode 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Edit
          </button>
          <button
            onClick={() => setPreviewMode(true)}
            className={`px-3 py-1 rounded text-sm transition-colors ${
              previewMode 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Preview
          </button>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-xs text-gray-500">
            GitLab Flavored Markdown
          </span>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 rounded hover:bg-gray-700 transition-colors text-gray-400 hover:text-white"
            title={isFullscreen ? "Exit fullscreen (F11, Ctrl+Enter, or Esc)" : "Enter fullscreen (F11 or Ctrl+Enter)"}
          >
            {isFullscreen ? (
              <ArrowsPointingInIcon className="h-4 w-4" />
            ) : (
              <ArrowsPointingOutIcon className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Editor Content */}
      <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-gray-900' : ''} min-h-[300px]`}>
        {isFullscreen && (
          <div className="absolute top-4 right-4 z-10">
            <button
              onClick={() => setIsFullscreen(false)}
              className="p-2 rounded bg-gray-800 hover:bg-gray-700 transition-colors text-gray-400 hover:text-white border border-gray-600"
              title="Exit fullscreen"
            >
              <ArrowsPointingInIcon className="h-5 w-5" />
            </button>
          </div>
        )}
        
        {previewMode ? (
          <div className={`p-4 ${isFullscreen ? 'h-screen overflow-auto' : ''}`}>
            <div 
              className="prose prose-invert max-w-none"
              dangerouslySetInnerHTML={{ 
                __html: renderMarkdown(internalContent || 'No content to preview') 
              }}
            />
          </div>
        ) : (
          <textarea
            value={internalContent}
            onChange={(e) => {
              const newContent = e.target.value
              setInternalContent(newContent)
              onChange(newContent)
            }}
            placeholder={placeholder}
            className={`w-full p-4 bg-transparent text-white font-mono text-sm leading-relaxed resize-none focus:outline-none ${
              isFullscreen ? 'h-screen' : 'h-80'
            }`}
          />
        )}
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
                  <code className="bg-gray-700 px-1 rounded text-xs">{tip.syntax}</code>
                  <span className="text-xs text-gray-500">{tip.description}</span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Supports: <strong>Bold</strong>, <em>Italic</em>, <code>Code</code>, Headings, Lists, Links, Images, Tables, Task Lists, Blockquotes, and more!
            </p>
          </div>
        </div>
        </div>
      )}
    </div>
  )
}
