export async function POST(req) {
  const { query } = await req.json();

  const response = await fetch("http://localhost:8000/search_text", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  const data = await response.json();

  if (!response.ok) {
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { "Content-Type": "application/json" }
    });
  }

  return Response.json(data);
}
