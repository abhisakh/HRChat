# HRChat_LLM (Context Aware Chat + Fine Tuning)

---
<a id="table"></a>
## 📖 Table of Contents
- [Introduction](#introduction)
- [Architecture and Workflow of HRChat](#archi1)
- [Tech Stack for HRChat](#tech-stack)
  - [Frontend](#frontend1)
  - [Backend](#backend1)
  - [Database](#database1)
  - [LLM](#llm1)
  - [Finetuning](#finetune1)
- [Design Overview](#design-overview)
  - [Backend enpoints](#backend-endpoints)
   - [User authentication](#user-authentication)
   - [User management](#user-management)
   - [Chat functionality](#chat-functionality)
   - [Additional feture](#additional-feature)
- Database Schema Design(#database-design)
  - - [User Table](#user-table)
  - - [Password Storage](#password-storage)
- [Architecture Overview](#architecture-overview)



---

# Introduction
<a id ="bridging"></a>
## 🧬 Bridging the Gap Between AI and Scientific Rigor
<-- [Back](#table)





<a id ="bridging"></a>
## Introduction
<-- [Back](#table)
In today’s dynamic and competitive business environment, effective human resource management is crucial for organizational success. 
The HRChat project aims to develop an intelligent, user-friendly chatbot that streamlines communication between employees and 
HR departments. By leveraging advanced artificial intelligence and natural language processing technologies, HRChat facilitates 
quick access to HR-related information, simplifies common queries, and enhances overall employee engagement. This project is 
significant because it addresses the growing need for efficient, 24/7 accessible HR support, reduces administrative workload, 
and improves response times. Ultimately, HRChat empowers organizations to foster a more responsive, transparent, and productive workplace culture.

<a id ="archi1"></a>
## Architecture and Workflow of HRChat
<-- [Back](#table)
The HRChat system is designed with a modular, scalable architecture that integrates a front-end user interface, a backend server, 
and multiple supporting services. The front end, typically a web or mobile application, facilitates user interactions such as 
querying HR policies, submitting leave requests, or accessing employee information. The backend server, built using a robust 
framework like Node.js or Django, processes incoming requests and communicates with various microservices, including natural 
language processing (NLP) modules, database management systems, and authentication services. The NLP component leverages machine l
earning models to interpret user queries and generate appropriate responses. Data flows seamlessly through this architecture, with 
user inputs routed to the NLP engine, which then interacts with the database to retrieve or update information. The workflow begins 
when a user submits a query via the chat interface, triggering the NLP module to analyze and understand the intent. The system then 
fetches or modifies data as needed and formulates a response, which is delivered back to the user through the interface. This 
architecture ensures a responsive, secure, and intelligent HR chatbot that streamlines HR interactions and improves employee engagement.

---
<a id ="tech-stack"></a>
## **Tech Stack for HRChat**
<-- [Back](#table)
<a id ="frontend1"></a>
**Frontend:**
- **Framework:** React.js or Vue.js for building an interactive and responsive user interface.
- **Styling:** CSS3, Sass, or Tailwind CSS for modern styling.
- **State Management:** Redux or Vuex to manage application state efficiently.
- **Communication:** Axios or Fetch API for API calls.
- **Deployment:** Hosted on platforms like Netlify, Vercel, or cloud services such as AWS Amplify.
<a id ="backend1"></a>
**Backend:**
- **Framework:** Node.js with Express.js or Python with FastAPI for handling API requests.
- **Authentication:** JWT (JSON Web Tokens) or OAuth2 for secure user authentication.
- **API Layer:** RESTful APIs or GraphQL to enable flexible data retrieval.
- **Hosting:** Cloud services like AWS, Azure, or Google Cloud Platform.
<a id ="database1"></a>
**Database:**
- **Type:** NoSQL (MongoDB) or SQL (PostgreSQL/MySQL) depending on data complexity.
- **Purpose:** Store user profiles, chat histories, and configuration settings.
- **Hosting:** Managed database services like MongoDB Atlas, AWS RDS, or Azure SQL.
<a id ="llm1"></a>
**Large Language Model (LLM):**
- **Model:** OpenAI GPT-4, GPT-3.5, or other suitable LLMs for natural language understanding and generation.
- **Access:** Via API calls to OpenAI or similar providers.
- **Hosting:** Cloud-based API access; local hosting if using open-source models like LLaMA or GPT-J.
<a id ="finetune1"></a>
**Finetuning:**
- **Data Preparation:** Curate HR-specific datasets, including common interview questions, policy documents, and organizational knowledge.
- **Training:** Use frameworks like OpenAI’s fine-tuning API, Hugging Face Transformers, or OpenLLM to adapt the base LLM.
- **Deployment:** Deploy finetuned models on cloud infrastructure, ensuring low latency and high availability.
- **Monitoring:** Track model performance and periodically update finetuning data as needed.

---
<a id ="design-overview"></a>
**Design Paragraph for HRChat**
<-- [Back](#table)
HRChat is designed as an intelligent, user-friendly chatbot tailored for human resource interactions. The frontend 
employs modern JavaScript frameworks such as React.js or Vue.js to deliver a seamless, responsive user experience, 
allowing users to interact effortlessly across devices. The backend, built with Node.js and Express.js or Python’s 
FastAPI, serves as the backbone for managing API requests, user authentication, and session management. A robust 
database solution like PostgreSQL or MongoDB stores user profiles, chat histories, and system configurations securely 
and efficiently. At its core, HRChat leverages advanced large language models such as GPT-4 through API integrations, 
providing natural language understanding and context-aware responses. To optimize domain-specific performance, the 
base LLM is finetuned using HR-related datasets, ensuring the chatbot delivers accurate and relevant assistance. This 
integrated stack ensures HRChat is scalable, secure, and capable of delivering personalized HR support, streamlining 
communication between employees and HR teams.

---
<a id ="backend-endpoints"></a>
## 1. Backend Endpoints
<-- [Back](#table)
<a id ="user-authentication"></a>
### 1.1 User Authentication

| Endpoint                 | Method  | Description                                           | Request Body / Params                                   | Response                                              |
|--------------------------|---------|-------------------------------------------------------|---------------------------------------------------------|--------------------------------------------------------|
| `/api/register`          | POST    | Register a new user (employee or HR)                  | `{ "username": "john_doe", "password": "pass123", "role": "employee" }` | Success message / error                                |
| `/api/login`             | POST    | Authenticate user and generate token                  | `{ "username": "john_doe", "password": "pass123" }`    | `{ "token": "JWT_TOKEN" }`                               |
| `/api/logout`            | POST    | Invalidate user session / token (if using token blacklist) | Authorization: Bearer JWT token                        | Success / error                                        |
<a id ="user-management"></a>
### 1.2 User Management

| Endpoint                | Method | Description                          | Request Body / Params                  | Response                                |
|-------------------------|--------|--------------------------------------|----------------------------------------|-----------------------------------------|
| `/api/users`           | GET    | Fetch list of users (admin only)     | Authorization header (JWT)             | List of user profiles                   |
| `/api/users/{id}`      | GET    | Get user details                     | Path param: user ID                    | User profile                            |
<a id ="chat-functionality"></a>
### 1.3 Chat Functionality

| Endpoint                   | Method | Description                                | Request Body / Params                          | Response                                   |
|----------------------------|--------|--------------------------------------------|------------------------------------------------|--------------------------------------------|
| `/api/chats`               | GET    | Retrieve chat history between users        | Query params: `userId1`, `userId2`            | List of chat messages                      |
| `/api/chats`               | POST   | Send a message                              | `{ "senderId": ..., "receiverId": ..., "message": "Hello" }` | Confirmation / new message object          |
| `/api/chats/{chatId}`      | GET    | Fetch specific chat thread                  | Path param: chat ID                            | Chat history details                      |
<a id ="additional-feature"></a>
### 1.4 Additional Features

| Endpoint                     | Method | Description                                                    | Request / Params                     | Response                        |
|------------------------------|--------|----------------------------------------------------------------|-------------------------------------|---------------------------------|
| `/api/notifications`        | GET    | Fetch notifications for the user                                | Authorization header (JWT)          | List of notifications           |

---
<a id ="database-design"></a>
## 2. Database Schema Design
<a id ="user-table"></a>
### 2.1 Users Table

| Column          | Type             | Constraints                          | Description                                     |
|-----------------|------------------|-------------------------------------|-------------------------------------------------|
| `id`          | UUID / SERIAL   | PRIMARY KEY                         | Unique user identifier                         |
| `username`    | VARCHAR(50)     | UNIQUE, NOT NULL                     | User login name                                |
| `password_hash` | VARCHAR(255)   | NOT NULL                            | Hashed password (bcrypt/scrypt)                |
| `role`        | ENUM('employee', 'HR', 'admin') | NOT NULL        | Defines user permissions                       |
| `created_at`  | TIMESTAMP       | DEFAULT CURRENT_TIMESTAMP           | Account creation timestamp                     |
| `updated_at`  | TIMESTAMP       | DEFAULT CURRENT_TIMESTAMP ON UPDATE | Last update timestamp                         |

**Reasoning:**  
- Using UUIDs or SERIAL for unique IDs ensures scalability and uniqueness.  
- Password hashes store securely using bcrypt or similar algorithms.  
- Role field manages access levels.  

---
<a id ="password-storage"></a>
### 2.2 Password Storage

- **Hashing Algorithm:** bcrypt (or scrypt/Argon2)  
- **Reasoning:** Bcrypt is industry-standard for secure password storage, resistant to brute-force attacks.  
- **Implementation:** When users register or change passwords, hash the plaintext password before storing.

---

### 2.3 Chat History Table

| Column          | Type            | Constraints                          | Description                                  |
|-----------------|-----------------|-------------------------------------|----------------------------------------------|
| `id`          | UUID / SERIAL  | PRIMARY KEY                        | Unique chat message ID                       |
| `sender_id`    | UUID / SERIAL  | FOREIGN KEY -> Users(id)           | Sender user ID                               |
| `receiver_id`  | UUID / SERIAL  | FOREIGN KEY -> Users(id)           | Receiver user ID                             |
| `message`      | TEXT           | NOT NULL                           | Text content of message                      |
| `timestamp`    | TIMESTAMP      | DEFAULT CURRENT_TIMESTAMP          | When message was sent                        |
| `chat_id`      | UUID / SERIAL  | (Optional) if grouping messages    | To group messages in a thread               |

**Reasoning:**  
- Storing sender and receiver IDs allows for efficient retrieval of conversation histories.  
- Timestamps enable chronological ordering.  
- Optional `chat_id` can be used for multi-message threads.

---

### 2.4 Chat Indexing

- Index on `(sender_id, receiver_id, timestamp)` for efficient retrieval of conversation history.  
- Consider composite indexes for common query patterns.

---

## 3. Rationale Behind Design Choices

### Security
- **Password Storage:** bcrypt hashing with salting to prevent password leaks.
- **JWT Tokens:** stateless authentication for scalability; tokens include user roles and expiration.
- **Secure Endpoints:** protected by middleware that verifies tokens and user permissions.

### Scalability & Performance
- Use of UUIDs for unique identifiers supports horizontal scaling.
- Indexes on frequently queried fields (user IDs, timestamps) optimize performance.
- RESTful endpoints facilitate clear separation of concerns and ease of integration.

### Flexibility
- Role-based access control via `role` field.
- Chat history stored with sender/receiver IDs for flexible retrieval.
- Modular API endpoints support future features (notifications, group chats).

---

## Summary

This design provides a secure, scalable, and maintainable foundation for HRChat:

- **Endpoints** facilitate registration, login, messaging, and user management.
- **Database schema** ensures data integrity, security (password hashing), and efficient querying.
- **Design choices** prioritize security, scalability, and flexibility for future feature expansion.

Let me know if you'd like further details or sample implementations!

---

## Planned File and Folder Architecture
```
HRChat/
│
├── README.md
├── .gitignore
├── package.json            # For JavaScript/Node.js projects
├── yarn.lock or package-lock.json
│
├── src/                    # Source files
│   ├── components/         # Reusable UI components
│   │   ├── ChatWindow/
│   │   │   ├── ChatWindow.jsx
│   │   │   └── ChatWindow.css
│   │   ├── Message/
│   │   │   ├── Message.jsx
│   │   │   └── Message.css
│   │   └── ...               # Other components
│   │
│   ├── pages/              # Page components
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   └── ...               # Other pages
│   │
│   ├── services/           # API calls and business logic
│   │   └── api.js
│   │
│   ├── utils/              # Utility functions
│   │   └── helpers.js
│   │
│   ├── assets/             # Images, fonts, etc.
│   │   └── ...
│   │
│   ├── App.jsx             # Main app component
│   ├── index.jsx           # Entry point
│   └── styles.css          # Global styles
│
├── public/                 # Static assets
│   ├── index.html
│   └── favicon.ico
│
├── backend/                # Backend server (if applicable)
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── config/
│   ├── app.js or server.js
│   └── package.json
│
├── config/                 # Configuration files
│   └── env.sample
│
├── tests/                  # Test files
│   ├── unit/
│   └── integration/
│
└── docker-compose.yml      # Docker configuration (if used)

```

```
HRChat/
├── backend/                # FastAPI + LangGraph "Brain"
│   ├── app/
│   │   ├── api/            # FastAPI routes (chat, health, auth)
│   │   ├── core/           # Config (env vars, constants)
│   │   ├── agent/          # THE CORE: LangGraph Logic
│   │   │   ├── graph.py    # StateGraph definition (nodes & edges)
│   │   │   ├── state.py    # Type definitions for the graph state
│   │   │   ├── nodes.py    # Functions for each step (retrieve, grade, generate)
│   │   │   └── tools/      # HRIS APIs, calculator tools, etc.
│   │   │       ├── retriever.py
│   │   │       └── sql_tool.py   <-- NEW: Helper to query SQLite
│   │   ├── db
│   │       ├── schemas           <-- NEW: Folder for .sql files
│   │       │   ├── employees.sql  <-- Structured employee data
│   │       │   └── audit_logs.sql <-- Chat history & metadata
│   │       ├── connection.py     <-- NEW: DB session/init logic
│   │       └── hr_database.db    <-- The actual SQLite file
│   ├── main.py             # Entry point for Uvicorn
│
│
│  
│
├── frontend/               # Next.js 15+ / React "Face"
│   ├── app/                # App Router (Layouts, Pages)
│   ├── components/         # Shadcn/UI + Chat components
│   │   ├── chat/           # ChatWindow, MessageBubble
│   │   └── ui/             # Buttons, Inputs, Cards
│   ├── hooks/              # useChat, useLangGraphStreaming
│   └── lib/                # API client (Axios/Fetch)
│
├── data/                   # Ingestion & Processing
│   ├── raw/                # Original HR PDFs/Docs
│   └── scripts/            # Python scripts to chunk & upload to Vector DB
│
├── docker-compose.yml      # Spin up Backend, Frontend, and Postgres
└── requirements.txt
└── .env                    # Keys for OpenAI, Pinecone, etc.
```

## Architectural Journey of the Backend

Think of the Backend as a high-end restaurant:

1. FastAPI (main.py): The Waiter (takes orders and gives answers).
2. LangGraph (agent/): The Head Chef (decides how to cook the order).
3. Tools (tools/): The Kitchen Appliances (SQL for facts, Vector for documents).
4. Database (db/): The Pantry (where all ingredients are stored).

### Module 1: The Foundation - The Database Layer (/db)
Before the AI can think, it needs data. We use **SQLite** because it is a "file-based" database (everything is stored in hr_database.db), which is perfect for development.

#### 1.1 The Schemas (/schemas)
Instead of creating tables manually, we use .sql files. This is your "Blueprint."
- employees.sql: Stores personal data (Salary, Supervisor).
- auth.sql: Stores credentials (Usernames, Hashed Passwords).
- chat_audit_logs.sql: Stores every question asked for security.

#### 1.2 The Connector (connection.py)
This file is the "Bridge." It contains the init_db() function, which reads those SQL blueprints and builds the actual database file. It also contains the save_to_audit_log() function, which acts as a "Black Box recorder" for the bot.

---

### Module 2: The Brain - The Agent Layer (/agent)
This is where the "Intelligence" lives. We use LangGraph, which treats a conversation like a flowchart (a Graph).

#### 2.1 State (state.py)
In a standard script, variables disappear when the function ends. In an AI agent, we need a "Short-term Memory."
- The AgentState is a Python dictionary that travels through the graph. It carries the messages (chat history) and the user_id.

#### 2.2 Nodes (nodes.py)
Nodes are the "Decision Stations."
**Router Node:** Looks at the question. Is it about salary? (Go to SQL). Is it about policy? (Go to Vector).
**Generate Node:** Takes the data found by the tools and writes a nice, human-sounding response.

#### 2.3 The Graph (graph.py)
This file connects the nodes together. It defines the flow:
**Start -> Router -> Tools -> Generator -> End**
- Memory Checkpoint: This is where SqliteSaver lives. It saves the state to checkpoints.sqlite so if the user comes back tomorrow, the "Chef" remembers what they ordered yesterday.

---

### Module 3: The Tools - Data Retrieval (/tools)
The AI doesn't actually "know" about the employer's personal information(e.g., salary, supervisor  name etc.) or anything about the company policies. It has to look it up using these specialized tools.

#### 3.1 SQL Tool (sql_tool.py)
- This is for Structured Data.
It takes a natural language question (e.g., "What is my pay?"), converts it into a SQL query (SELECT salary FROM employees...), and returns the number.

#### 3.2 Retriever (retriever.py)
- This is for Unstructured Data (The PDF).
It uses Vector Search. We turned the required PDF document into thousands of tiny mathematical "embeddings." This tool finds the paragraphs that "mathematically match" the user's question about the dress code or PTO.

---

### Module 4: The Gateway - The API (main.py)
This is the only part of the backend that "talks" to the outside world (the Frontend).
- Login Endpoint: Verifies the username and returns the user_id.
- Chat Endpoint: Receives a message, hands it to the LangGraph Agent, waits for the agent to finish "thinking," and sends the result back as JSON.

---

