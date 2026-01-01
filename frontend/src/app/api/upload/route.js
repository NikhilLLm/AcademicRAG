export async function POST(req) {
  const body = await req.formData();

  const response = await fetch("http://localhost:8000/upload", {
    method: "POST",
    body,
  });

  const data = await response.json();

  return new Response(JSON.stringify(data), {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
