export const API_BASE = "http://localhost:8000";

export async function GET(request) {
    // Get token from the request's Authorization header
    const authHeader = request.headers.get('Authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return new Response(JSON.stringify({ error: "No authentication token found" }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
        });
    }

    // Forward the request to backend
    const res = await fetch(`${API_BASE}/notes`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Authorization": authHeader  // Pass the full "Bearer xxx" header
        },
    });

    const responseData = await res.json();

    return new Response(JSON.stringify(responseData), {
        status: res.status,
        headers: { "Content-Type": "application/json" },
    });
}
