
export async function POST(req, { params }) {
  const { id } = await params;//this is most important whenever getting data from params always use the await 

  const formData = new FormData();
  formData.append("vector_index", id);

  const response = await fetch("http://localhost:8000/get_short_notes", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  return new Response(JSON.stringify(data), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  })
}
