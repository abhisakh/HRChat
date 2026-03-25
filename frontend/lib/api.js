/**
 * frontend/lib/api.js
 * This file acts as the single point of contact between
 * our React Frontend and our FastAPI Backend.
 */

const BASE_URL = "http://localhost:8000";

/**
 * Sends credentials to the backend to get a user's session data.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<Object>} Returns {user_id, role, status}
 */
export const loginUser = async (username, password) => {
    try {
        const response = await fetch(`${BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error("Invalid username or password");
        }

        return await response.json();
    } catch (error) {
        console.error("Login Error:", error);
        throw error;
    }
};

/**
 * Sends a chat message to the LangGraph agent.
 * @param {string} userId - The unique ID of the logged-in user.
 * @param {string} message - The question asked by the user.
 * @returns {Promise<Object>} Returns {user_id, answer, source}
 */
export const sendChatMessage = async (userId, message) => {
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, message: message }),
        });

        if (!response.ok) {
            throw new Error("Failed to get response from AI");
        }

        return await response.json();
    } catch (error) {
        console.error("Chat Error:", error);
        throw error;
    }
};

/**
 * Registers a new employee in the system.
 * @param {Object} userData - Contains first_name, last_name, position, salary, etc.
 */
export const registerUser = async (userData) => {
    const response = await fetch(`${BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData),
    });
    return await response.json();
};