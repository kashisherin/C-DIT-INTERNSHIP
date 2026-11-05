import { useEffect, useRef, useState } from "react";
import { askQuestion } from "./api";
import ChatMessage, { TypingIndicator } from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import SourcesPanel from "./components/SourcesPanel";

const WELCOME = {
    role: "bot",
    text:
        "Hi! I answer questions using the web pages in my knowledge base. " +
        "What would you like to know?",
};

export default function App() {
    const [messages, setMessages] = useState([WELCOME]);
    const [loading, setLoading] = useState(false);

    const bottomRef = useRef(null);

    // Scroll to the newest message whenever the list changes
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    async function handleSend(question) {
        setMessages((prev) => [
            ...prev,
            { role: "user", text: question },
        ]);

        setLoading(true);

        try {
            const data = await askQuestion(question);

            const reply = {
                role: "bot",
                text: data.answer,
                sources: data.sources,
            };

            setMessages((prev) => [...prev, reply]);
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                { role: "error", text: error.message },
            ]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex h-screen flex-col bg-gray-100">
            {/* Header */}
            <header className="border-b border-gray-200 bg-white px-6 py-4">
                <h1 className="text-2xl font-bold text-gray-800">
                    Kerala Knowledge Bot
                </h1>

                <p className="text-sm text-gray-500">
                    RAG chatbot · FastAPI + Ollama + React
                </p>
            </header>

            {/* Main content */}
            <main className="flex flex-1 overflow-hidden">
                {/* Chat section */}
                <section className="flex flex-1 flex-col">
                    <div className="flex-1 space-y-4 overflow-y-auto p-6">
                        {messages.map((message, index) => (
                            <ChatMessage
                                key={index}
                                role={message.role}
                                text={message.text}
                                sources={message.sources || []}
                            />
                        ))}

                        {loading && <TypingIndicator />}

                        <div ref={bottomRef} />
                    </div>

                    <ChatInput
                        onSend={handleSend}
                        disabled={loading}
                    />
                </section>

                {/* Knowledge sources sidebar */}
                <aside className="hidden w-80 overflow-y-auto border-l
                    border-gray-200 bg-white p-5 lg:block">
                    <SourcesPanel />
                </aside>
            </main>
        </div>
    );
}