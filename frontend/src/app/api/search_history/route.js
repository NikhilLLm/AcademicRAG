import { NextResponse } from "next/server";

export async function GET(request) {
    try {
        const authHeader = request.headers.get("authorization");
        
        const response = await fetch("http://localhost:8000/search_history", {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                // Forward the header if present, or handle missing
                ...(authHeader && { "Authorization": authHeader }), 
            },
        });
        
        if (!response.ok) {
             // propagate error status
             return NextResponse.json({ error: "Backend error" }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error("Error fetching search history:", error);
        return NextResponse.json({ error: "Failed to fetch search history" }, { status: 500 });
    }
}