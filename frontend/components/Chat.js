'use client'

import { useState, useRef, useEffect } from 'react'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setIsLoading(true)

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Update conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      // Add assistant message to chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response 
      }])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(e)
    }
  }

  const clearChat = () => {
    setMessages([])
    setConversationId(null)
    inputRef.current?.focus()
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-7xl w-full mx-auto bg-white/95 backdrop-blur-sm shadow-2xl rounded-2xl overflow-hidden border border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 via-primary-500 to-primary-400 text-white px-6 py-4 shadow-lg flex-shrink-0">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Konecto</h1>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-md rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Clear Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-8 bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50 flex flex-col gap-6 chat-scrollbar min-h-0">
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <div className="bg-white rounded-2xl p-10 shadow-lg border border-gray-200 max-w-2xl mx-auto transform hover:scale-105 transition-transform duration-300">
              <div className="text-center mb-6">
                <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h2 className="text-3xl font-bold text-gray-800 mb-3">Welcome! 👋</h2>
                <p className="text-gray-600 text-lg">I'm your Series 76 Electric Actuators assistant</p>
              </div>
              
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-4 border border-primary-100">
                  <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-primary-500 text-white rounded-full flex items-center justify-center text-sm">1</span>
                    Search by Part Number
                  </h3>
                  <p className="text-gray-600 text-sm ml-8">Example: "763A00-11330C00/A"</p>
                </div>
                
                <div className="bg-gradient-to-r from-accent-50 to-orange-50 rounded-xl p-4 border border-accent-100">
                  <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-accent-500 text-white rounded-full flex items-center justify-center text-sm">2</span>
                    Find by Requirements
                  </h3>
                  <p className="text-gray-600 text-sm ml-8">Example: "110 V single phase" or "high torque actuator"</p>
                </div>
                
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4 border border-green-100">
                  <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm">3</span>
                    Get Technical Specs
                  </h3>
                  <p className="text-gray-600 text-sm ml-8">Ask about torque, speed, power, or any specification</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
          >
            <div className={`max-w-[75%] rounded-2xl px-5 py-4 shadow-md ${
              message.role === 'user' 
                ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white rounded-br-md' 
                : 'bg-white text-gray-800 rounded-bl-md border border-gray-200'
            }`}>
              {message.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200">
                  <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium text-gray-600">AI Assistant</span>
                </div>
              )}
              <div className="whitespace-pre-wrap break-words leading-relaxed">
                {message.content.split('\n').map((line, i) => (
                  <p key={i} className={i > 0 ? 'mt-2' : ''}>{line || '\u00A0'}</p>
                ))}
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-white rounded-2xl rounded-bl-md px-5 py-4 shadow-md border border-gray-200">
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 bg-primary-500 rounded-full typing-dot"></span>
                  <span className="w-2.5 h-2.5 bg-primary-500 rounded-full typing-dot"></span>
                  <span className="w-2.5 h-2.5 bg-primary-500 rounded-full typing-dot"></span>
                </div>
                <span className="text-sm text-gray-500">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Input Form */}
      <div className="bg-white border-t border-gray-200 px-6 py-6 shadow-lg flex-shrink-0">
        <form 
          onSubmit={handleSend}
          className="flex gap-3 max-w-4xl mx-auto"
        >
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about actuators, part numbers, or technical requirements..."
              disabled={isLoading}
              className="w-full px-6 py-4 border-2 border-gray-300 rounded-2xl text-base focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-100 disabled:bg-gray-100 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 text-white flex items-center justify-center transition-all duration-200 hover:scale-105 hover:shadow-xl hover:from-primary-600 hover:to-primary-700 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:from-gray-400 disabled:to-gray-500 shadow-lg"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </form>
        <p className="text-center text-xs text-gray-500 mt-4">
          Powered by AI • Series 76 Electric Actuators Database
        </p>
      </div>
    </div>
  )
}
