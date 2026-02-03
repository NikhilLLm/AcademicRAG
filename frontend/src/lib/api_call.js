import endpoint from '@/utils/endpoint'

//------------------------------
//  SEARCH QUERY
//------------------------------
// Updated: Now uses JSON instead of FormData
export async function getSearchResult(query) {
  const headers = {
    "Content-Type": "application/json"
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${endpoint}/search_text`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ query }),
  });

  return await response.json();
}
//--------------------------------
// UPLOAD QUERY
//--------------------------------
export async function getUploadResult(file) {
  const token = localStorage.getItem('auth_token');
  const formData = new FormData()
  formData.append("file", file);
  const response = await fetch(`${endpoint}/upload`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`
    },
    body: formData,
  });
  if (!response.ok) {
    throw new Error(response.status);
  }
  console.log(response);
  return await response.json();

}
//------------------------------------
// NOTES
//-------------------------------------
// Updated: Now uses JSON instead of FormData
//------------------------------------
// NOTES
//-------------------------------------
// Updated: Now uses JSON instead of FormData
//------------------------------------
// NOTES
//-------------------------------------
// Updated: Now uses JSON instead of FormData
export async function startNotesJob(id) {
  const headers = {
    "Content-Type": "application/json"
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${endpoint}/notes/start/${id}`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ vector_index: id }),
  });

  if (!res.ok) {
    throw new Error("Failed to start notes job");
  }

  return res.json(); // { job_id }
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${endpoint}/notes/status/${jobId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch job status");
  }

  return res.json(); // { status, result }
}


// ---------------------------------
// CHAT
// ---------------------------------

// 1️⃣ Start chat preparation (embedding check / creation)
// Updated: Now uses JSON instead of FormData
export async function startChatJob(vectorIndex) {
  const headers = {
    "Content-Type": "application/json"
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${endpoint}/chat/chat_start/${vectorIndex}`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ vector_index: vectorIndex }),
  });

  if (!res.ok) {
    throw new Error("Failed to start chat job");
  }

  return res.json(); // { chat_session_id }
}

// 2️⃣ Poll chat job status
export async function getChatStatus(chatSessionId) {
  const res = await fetch(`${endpoint}/chat/chat_status/${chatSessionId}`);
  console.log(chatSessionId)
  if (!res.ok) {
    throw new Error("Failed to fetch chat status");
  }

  return res.json(); // { status, pdf_id }
}

// 3️⃣ Send chat message (non-streaming for now)
export async function sendChatMessage(chatSessionId, message) {
  const headers = {
    "Content-Type": "application/json"
  };
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${endpoint}/chat/stream/${chatSessionId}`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to send chat message");
  }

  const text = await res.text(); // 👈 IMPORTANT
  return { answer: text };
}

//ChatSessions
export async function getChatSession(){
  const token=localStorage.getItem('auth_token');
  const res=await fetch(`${endpoint}/chat/get_chats`,{
    method:"GET",
    headers:{
      "Content-Type":"application/json",
      "Authorization":`Bearer ${token}`
    },
  });
  if(!res.ok){
    throw new Error("Failed to fetch chat session");
  }
  return res.json();
}

// Register



export async function register(data) {
  const res = await fetch(`${endpoint}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  const result = await res.json();

  if (!res.ok) {
    throw new Error(result.detail || "Registration failed");
  }

  // Save token to localStorage if registration successful
  if (result.access_token) {
    localStorage.setItem('auth_token', result.access_token);
  }

  return result;
}

// Login

export async function login(data) {
  const res = await fetch(`${endpoint}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  const result = await res.json();

  if (!res.ok) {
    throw new Error(result.detail || "Login failed");
  }

  // Save token to localStorage if login successful
  if (result.access_token) {
    localStorage.setItem('auth_token', result.access_token);
  }
  console.log(result)
  return result;
}


//user-verification

export async function getUserInfo() {
  // Get token from localStorage
  const token = localStorage.getItem('auth_token');

  if (!token) {
    throw new Error("No authentication token found");
  }

  const res = await fetch(`${endpoint}/auth/user`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to get user info: ${res.status}`);
  }
  const data = await res.json()
  console.log(data);
  return data;
}

// Get user's saved notes/papers
export async function getUserNotes() {
  const token = localStorage.getItem('auth_token');

  if (!token) {
    throw new Error("No authentication token found");
  }

  // Call the Next.js API route (which forwards to backend)
  const res = await fetch(`/api/notes/get_notes`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to get notes: ${res.status}`);
  }

  return res.json();
}

// Get user's search history
export async function getSearchHistory() {
  const token = localStorage.getItem('auth_token');

  if (!token) {
    throw new Error("No authentication token found");
  }

  const res = await fetch(`${endpoint}/search_history`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to get search history: ${res.status}`);
  }

  return res.json();
}
