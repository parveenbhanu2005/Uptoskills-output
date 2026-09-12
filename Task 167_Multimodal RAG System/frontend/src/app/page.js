"use client";
import { useState } from "react";

export default function Dashboard() {
  const [query, setQuery] = useState("");
  
  // Start with just a blank slate and a greeting
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello Technician. I am connected to the live database. What hardware issue can I help you troubleshoot today?" }
  ]);

  // Set the visualizer to empty state initially
  const [activeData, setActiveData] = useState({
    image: null,
    source: null,
    distance: null
  });
  
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userText = query;
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setIsLoading(true);
    setQuery("");

    try {
      // Send the real request to your Python server!
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userText }),
      });
      
      if (!res.ok) throw new Error("Server error");
      
      const data = await res.json();
      
      const newResponse = { 
        role: "ai", 
        text: data.text,
        image: data.image,
        source: data.source,
        distance: data.distance
      };
      
      setMessages((prev) => [...prev, newResponse]);
      setActiveData({
        image: newResponse.image,
        source: newResponse.source,
        distance: newResponse.distance
      });

    } catch (error) {
      setMessages((prev) => [...prev, { role: "ai", text: "⚠️ Error connecting to the RAG backend. Is your Python Uvicorn server running on port 8000?" }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 font-sans">
      
      {/* LEFT SIDE: Chat Interface */}
      <div className="w-1/2 flex flex-col border-r border-gray-700">
        <div className="p-5 bg-gray-800 border-b border-gray-700">
          <h1 className="text-xl font-bold text-blue-400">Multimodal RAG Assistant</h1>
          <p className="text-xs text-green-400 mt-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> 
            Live Connection: Gemini 3.5 & ChromaDB
          </p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-md p-4 rounded-lg shadow-md ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-200"}`}>
                <p className="whitespace-pre-line leading-relaxed">{msg.text}</p>
                
                {msg.role === "ai" && msg.image && (
                  <button 
                    onClick={() => setActiveData({ image: msg.image, source: msg.source, distance: msg.distance })}
                    className="mt-3 text-xs bg-gray-800 hover:bg-gray-900 border border-gray-600 px-3 py-1.5 rounded flex items-center gap-2 transition-colors w-full"
                  >
                    <span>🖼️</span> Reload Schematic
                  </button>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 text-gray-400 p-4 rounded-lg animate-pulse shadow-md border border-gray-600">
                Running vector search and generating response...
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSearch} className="p-4 bg-gray-800 border-t border-gray-700 flex gap-3">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a technical question..." 
            className="flex-1 bg-gray-900 border border-gray-600 rounded-md px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
          />
          <button 
            type="submit" 
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-md font-semibold transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>

      {/* RIGHT SIDE: Visual Grounding Viewer */}
      <div className="w-1/2 flex flex-col bg-gray-950">
         <div className="p-5 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-xl font-bold text-green-400">Visual Grounding Context</h2>
          {activeData.image && <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded border border-green-700">Live Data</span>}
        </div>
        
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          {activeData.image ? (
            <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300 w-full">
             {/* Smart logic: Check if the file is an image. If not, show a document icon */}
              {activeData.image && activeData.image.match(/\.(jpeg|jpg|png|webp)$/i) ? (
                <img 
                  src={activeData.image} 
                  alt="Retrieved Schematic" 
                  className="max-w-full max-h-[65vh] rounded-lg shadow-2xl border-2 border-gray-700 object-contain bg-white" 
                />
              ) : (
                <div className="flex flex-col items-center justify-center p-12 bg-gray-800 rounded-lg border-2 border-dashed border-gray-600 w-full max-w-md shadow-xl">
                  <span className="text-6xl mb-4">📄</span>
                  <p className="text-gray-300 font-medium text-lg">Text Reference Document</p>
                  <p className="text-gray-500 text-sm mt-2 text-center">The database retrieved a text snippet instead of a visual diagram for this specific query.</p>
                </div>
              )}
              <div className="mt-6 bg-gray-800 p-4 rounded-lg border border-gray-700 text-center w-full max-w-md shadow-xl">
                <p className="text-sm text-gray-300 font-mono break-all">Source: <span className="text-white">{activeData.source}</span></p>
                <p className="text-sm text-green-400 font-mono mt-2">Vector Distance: {activeData.distance}</p>
              </div>
            </div>
          ) : (
            <div className="text-center text-gray-500 border-2 border-dashed border-gray-700 p-16 rounded-2xl bg-gray-900/50">
              <p className="text-lg font-medium text-gray-400">Awaiting Live Database Query</p>
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
}