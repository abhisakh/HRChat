// //frontend/src/lib/api.js
// /**
//  * frontend/lib/api.js
//  * This file acts as the single point of contact between
//  * our React Frontend and our FastAPI Backend.
//  */

// const BASE_URL = "http://localhost:8000";

// /**
//  * Sends credentials to the backend to get a user's session data.
//  * @param {string} username
//  * @param {string} password
//  * @returns {Promise<Object>} Returns {user_id, role, status}
//  */
// export const loginUser = async (username, password) => {
//     try {
//         const response = await fetch(`${BASE_URL}/login`, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ username, password }),
//         });

//         if (!response.ok) {
//             throw new Error("Invalid username or password");
//         }

//         return await response.json();
//     } catch (error) {
//         console.error("Login Error:", error);
//         throw error;
//     }
// };

// /**
//  * Sends a chat message to the LangGraph agent.
//  * @param {string} userId - The unique ID of the logged-in user.
//  * @param {string} message - The question asked by the user.
//  * @returns {Promise<Object>} Returns {user_id, answer, source}
//  */
// export const sendChatMessage = async (userId, message) => {
//     try {
//         const response = await fetch(`${BASE_URL}/chat`, {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ user_id: userId, message: message }),
//         });

//         if (!response.ok) {
//             throw new Error("Failed to get response from AI");
//         }

//         return await response.json();
//     } catch (error) {
//         console.error("Chat Error:", error);
//         throw error;
//     }
// };

// /**
//  * Registers a new employee in the system.
//  * @param {Object} userData - Contains first_name, last_name, position, salary, etc.
//  */
// export const registerUser = async (userData) => {
//     const response = await fetch(`${BASE_URL}/register`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(userData),
//     });
//     return await response.json();
// };

/**
 * frontend/lib/api.js
 * The secure bridge between React and the FastAPI Backend.
 */

const BASE_URL = "http://localhost:8000";

/**
 * Helper: SHA-256 Hashing using native Web Crypto API.
 * Ensures plain-text passwords never leave the user's browser.
 */
async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * 1. LOGIN: Hashes password before transmission.
 */
export const loginUser = async (username, password) => {
    try {
        const hashedPassword = await hashPassword(password);

        const response = await fetch(`${BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: username,
                password: hashedPassword
            }),
        });

        if (!response.ok) {
            throw new Error("Unauthorized: Invalid credentials.");
        }

        return await response.json();
    } catch (error) {
        console.error("Login Error:", error);
        throw error;
    }
};

/**
 * 2. CHAT: Sends message + context + role to the LangGraph agent.
 */
export const sendChatMessage = async (userId, message, history, role) => {
    try {
        const response = await fetch(`${BASE_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                history: history, // Required for AI memory
                role: role        // Required for RBAC security
            }),
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
 * 3. HISTORY: Recovers conversation from the database.
 */
export const getChatHistory = async (userId) => {
    try {
        const response = await fetch(`${BASE_URL}/chat/history/${userId}`);
        if (!response.ok) throw new Error("History fetch failed");
        return await response.json();
    } catch (error) {
        console.error("History Recovery Error:", error);
        throw error;
    }
};

/**
 * 4. REGISTRATION: Adds new personnel records.
 */
export const registerUser = async (userData) => {
    try {
        const response = await fetch(`${BASE_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(userData),
        });
        return await response.json();
    } catch (error) {
        console.error("Registration Error:", error);
        throw error;
    }
};