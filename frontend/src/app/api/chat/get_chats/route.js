import { NextResponse } from "next/server";

export async function GET(req){
    const auth_header=req.headers.get("Authorization");
    const res = await fetch("http://localhost:8000/recent_messages", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Authorization": auth_header
        },
    });
    const data = await res.json();
    return NextResponse.json(data);
}