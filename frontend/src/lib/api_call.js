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


export async function getNotes( id) {
  const formData = new FormData();
  formData.append("vector_index", id);            // backend expects th

  const response = await fetch(`${endpoint}/notes/${id}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch notes: ${response.status}`);
  }

  return await response.json();
}
