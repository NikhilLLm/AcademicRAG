import endpoint  from '@/utils/endpoint'
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