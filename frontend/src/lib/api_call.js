import endpoint  from '@/utils/endpoint'

//------------------------------
//  SEARCH QUERY
//------------------------------
export async function getSearchResult(query) {
  const formData = new FormData();
  formData.append("query", query);

  const response = await fetch(`${endpoint}/search_text`, {
    method: "POST",
    body: formData,
  });
  // console.log(response);
  return await response.json();
  
}
//--------------------------------
// UPLOAD QUERY
//--------------------------------
export async function getUploadResult(file) {
    const formData=new FormData()
    formData.append("file",file);
     const response = await fetch(`${endpoint}/upload`, {
    method: "POST",
    body: formData,
     });
     if(!response.ok){
        throw new Error(response.status);
     }
    console.log(response);
    return await response.json();
    
}
//------------------------------------
// NOTES
//-------------------------------------
export async function startNotesJob(id) {
  const formData = new FormData();
  formData.append("vector_index", id);

  const res = await fetch(`/api/notes/start/${id}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to start notes job");
  }

  return res.json(); // { job_id }
}

export async function getJobStatus(jobId) {
  const res = await fetch(`/api/notes/status/${jobId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch job status");
  }

  return res.json(); // { status, result }
}


// ---------------------------------
// CHAT
// ---------------------------------

// 1️⃣ Start chat preparation (embedding check / creation)
export async function startChatJob(vectorIndex) {
  const formData = new FormData();
  formData.append("vector_index", vectorIndex);

  const res = await fetch(`/api/chat/chat_start/${vectorIndex}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Failed to start chat job");
  }

  return res.json(); // { chat_session_id }
}

// 2️⃣ Poll chat job status
export async function getChatStatus(chatSessionId) {
  const res = await fetch(`/api/chat/chat_status/${chatSessionId}`);
  console.log(chatSessionId)
  if (!res.ok) {
    throw new Error("Failed to fetch chat status");
  }

  return res.json(); // { status, pdf_id }
}

// 3️⃣ Send chat message (non-streaming for now)
export async function sendChatMessage(chatSessionId, message) {
  const res = await fetch(`/api/chat/stream/${chatSessionId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "Failed to send chat message");
  }

  const text = await res.text(); // 👈 IMPORTANT
  return { answer: text };
}
