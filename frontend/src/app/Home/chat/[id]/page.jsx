"use client";

import { getChatStatus, sendChatMessage, startChatJob } from "@/lib/api_call";
import { useParams } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { Send, Loader2, FileText } from "lucide-react";
import Button from "@/components/ui/Button";
import Link from "next/link";
export default function ChatPage() {
  const { id } = useParams();

  const [chatId, setChatId] = useState(null);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loadingChat, setLoadingChat] = useState(true);
  const [sending, setSending] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Start chat session
  useEffect(() => {
    if (!id) return;
    startChatJob(id).then((res) => setChatId(res.chat_session_id));
  }, [id]);

  // Poll for chat readiness
  useEffect(() => {
    if (!chatId) return;
    const interval = setInterval(async () => {
      const data = await getChatStatus(chatId);
      if (data.status === "done") {
        setLoadingChat(false);
        clearInterval(interval);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [chatId]);

  // Load PDF from sessionStorage
  useEffect(() => {
    const url = sessionStorage.getItem(`pdf:${id}`);
    if (url) setPdfUrl(url);
  }, [id]);

  const handleSend = async () => {
    if (!query.trim() || sending || loadingChat) return;

    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setSending(true);

    try {
      const res = await sendChatMessage(chatId, query);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
    } catch (error) {
      console.error("Chat error:", error);
    } finally {
      setSending(false);
    }
  };

  return (
    <div 
      className="flex h-screen w-screen flex-col md:flex-row bg-neutral-950 text-neutral-100" 
      style={{ overflow: 'hidden' }}
    >
      {/* PDF VIEWER - Fully isolated with reserved scrollbar space */}
      <div 
        className="relative flex-1 md:w-1/2 md:border-r md:border-neutral-800 bg-neutral-900 flex flex-col" 
        style={{ 
          overflow: 'hidden',
          scrollbarGutter: 'stable both-edges' // Reserves space for scrollbar, prevents shifts
        }}
      >
        <Link href="/Home/chat">
         <button>Back</button>
        </Link>
        <div className="bg-neutral-900/80 px-5 py-4 border-b border-neutral-800 flex items-center gap-3 flex-shrink-0">
          <FileText className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold">Document Viewer</h2>
        </div>
        <div 
          className="flex-1" 
          style={{ 
            overflowY: 'auto',
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(148, 163, 184, 0.5) transparent',
            scrollbarGutter: 'stable' // Extra reservation for PDF content
          }}
        >
          {pdfUrl ? (
            <iframe
              src={`${pdfUrl}#view=FitH`}
              className="w-full min-h-full border-none"
              title="PDF Viewer"
              style={{ 
                width: '100%',
                height: '100%',
                border: 'none',
                display: 'block'
              }}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-neutral-500 p-4">
              <div className="text-center">
                <Loader2 className="animate-spin w-8 h-8 mx-auto mb-3" />
                <p className="text-sm">Loading document...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CHAT PANEL - Fully isolated with reserved scrollbar space */}
      <div 
        className="flex flex-1 md:w-1/2 flex-col bg-neutral-950" 
        style={{ 
          overflow: 'hidden',
          scrollbarGutter: 'stable both-edges' // Reserves space for scrollbar, prevents shifts
        }}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-neutral-800 bg-neutral-900/50 flex-shrink-0">
          <h2 className="text-xl font-bold">Chat with Document</h2>
          <p className="text-sm text-neutral-400 mt-1">Ask questions about the paper</p>
        </div>

        {/* Messages Area - Independent scroll with reserved space */}
        <div 
          className="flex-1 px-6 py-6 space-y-6" 
          style={{ 
            overflowY: 'scroll', // Always shows scrollbar
            scrollbarWidth: 'thin',
            scrollbarColor: 'rgba(148, 163, 184, 0.5) transparent',
            scrollbarGutter: 'stable',
            paddingRight: '8px' // Reserves extra space to prevent width jumps on scrollbar appearance
          }}
        >
          {messages.length === 0 && !loadingChat && (
            <div className="h-full flex items-center justify-center text-center">
              <div>
                <div className="w-20 h-20 bg-neutral-800/50 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Send className="w-10 h-10 text-neutral-600" />
                </div>
                <p className="text-neutral-300 text-lg font-medium">Start a conversation</p>
                <p className="text-neutral-500 text-sm mt-2">
                  Ask me anything about this document
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed shadow-lg transition-all ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-neutral-800 text-neutral-100 rounded-bl-none"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="bg-neutral-800 rounded-2xl px-5 py-3 shadow-lg">
                <Loader2 className="animate-spin w-6 h-6 text-neutral-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area - Fixed and isolated */}
        <div className="px-6 py-5 border-t border-neutral-800 bg-neutral-900/80 flex-shrink-0" style={{ maxHeight: '140px' }}>
          <div className="flex items-end gap-3 h-full">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about the paper…"
              className="flex-1 bg-neutral-900 border border-neutral-700 rounded-2xl px-5 py-3 text-sm resize-none outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-neutral-500 min-h-[48px] max-h-[100px] overflow-y-auto"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              onClick={handleSend}
              disabled={sending || loadingChat || !query.trim()}
              className="h-12 w-12 flex items-center justify-center rounded-2xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-600/20 shrink-0"
            >
              {sending ? (
                <Loader2 className="animate-spin w-5 h-5" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          {loadingChat && (
            <div className="flex items-center justify-center gap-2 mt-4 text-neutral-500 text-sm">
              <Loader2 className="animate-spin w-4 h-4" />
              <span>Preparing chat session...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}