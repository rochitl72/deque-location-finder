import axios from "axios";
import React, { useState } from "react";
import "./ChatBox.css";

const ChatBox = ({ latitude, longitude, onPlacesUpdate, onPlaceSelect }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [places, setPlaces] = useState([]); // Store suggested places

    const handleSend = async () => {
        if (!input.trim()) return;
        setLoading(true);

        const userMessage = { sender: "user", text: input };
        setMessages((prev) => [...prev, userMessage]);

        try {
            const response = await axios.post("http://127.0.0.1:8000/chatbot/query", {
                query: input,
                latitude,
                longitude,
                limit: 5,
            });

            const reply = response.data.reply || "No response from AI.";
            const aiMessage = { sender: "bot", text: reply };
            setMessages((prev) => [...prev, aiMessage]);

            const newPlaces = response.data.places?.results || [];
            setPlaces(newPlaces);

            // Notify App.js about new places
            if (onPlacesUpdate) onPlacesUpdate(newPlaces);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [
                ...prev,
                { sender: "bot", text: "Error fetching response." },
            ]);
        } finally {
            setInput("");
            setLoading(false);
        }
    };

    const handlePlaceSelect = (place) => {
        if (onPlaceSelect) onPlaceSelect(place);
    };

    return (
        <div className="chatbox-container">
            {/* Chat Messages */}
            <div className="chatbox-messages">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`chatbox-message ${msg.sender === "user" ? "user" : "bot"}`}
                    >
                        {msg.text}
                    </div>
                ))}
                {loading && <div className="chatbox-loading">Thinking...</div>}
            </div>

            {/* Suggested Places */}
            {places.length > 0 && (
                <div className="places-row">
                    {places.map((place, index) => (
                        <div key={place.fsq_id} className="place-card">
                            <img
                                src={`https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=${place.fsq_id}&key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}`}
                                alt={place.name}
                                className="place-image"
                                onError={(e) => (e.target.src = "/icons/heart.png")}
                            />
                            <p className="place-name">{index + 1}. {place.name}</p>
                            <button
                                className="get-directions-btn"
                                onClick={() => handlePlaceSelect(place)}
                            >
                                Get Directions
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Input Box */}
            <div className="chatbox-input">
                <input
                    type="text"
                    placeholder="Ask for nearby places (e.g., cozy cafes)..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                />
                <button onClick={handleSend} disabled={loading}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default ChatBox;