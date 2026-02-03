// app/api/auth/register/route.js
export const API_BASE = "http://localhost:8000"; // FastAPI URL

export async function POST(req) {
  const data = await req.json(); // get email/password from frontend
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  const responseData = await res.json();

  return new Response(JSON.stringify(responseData), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}