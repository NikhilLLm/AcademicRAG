"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function AuthGuard({ children }) {
    const router = useRouter();
    const [authorized, setAuthorized] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem("auth_token");
        if (!token) {
            router.push("/login");
        } else {
            setAuthorized(true);
        }
    }, [router]);

    if (!authorized) {
        return null; // or a loading spinner
    }

    return <>{children}</>;
}
