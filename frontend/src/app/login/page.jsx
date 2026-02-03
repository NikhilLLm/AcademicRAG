"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api_call";
import { useNotification } from "@/components/Notification";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const router = useRouter();
    const { showNotification } = useNotification();
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await login({
                email,
                password,
            });
            showNotification("Login successful!", "success");
            router.push("/Home");
        } catch (error) {
            showNotification(error.message || "Login failed", "error");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#0B0E1A] p-4 text-white">
            <div className="w-full max-w-md p-8 rounded-2xl bg-[#121524] border border-white/5 shadow-2xl space-y-8">
                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-bold tracking-tight">Welcome Back</h1>
                    <p className="text-gray-400">Sign in to your PaperSemantic account</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <label htmlFor="email" className="text-sm font-medium text-gray-300 ml-1">
                            Email Address
                        </label>
                        <input
                            type="email"
                            id="email"
                            placeholder="name@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full px-5 py-3 rounded-lg bg-[#0B0E1A] border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors placeholder:text-gray-600 text-white"
                        />
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="password" className="text-sm font-medium text-gray-300 ml-1">
                            Password
                        </label>
                        <input
                            type="password"
                            id="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full px-5 py-3 rounded-lg bg-[#0B0E1A] border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors placeholder:text-gray-600 text-white"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full py-4 rounded-lg font-bold bg-blue-600 hover:bg-blue-700 text-white transition-all transform active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
                    >
                        {isLoading ? "Signing In..." : "Sign In"}
                    </button>
                </form>

                <p className="text-center text-gray-400">
                    Don't have an account?{" "}
                    <Link href="/register" className="text-blue-500 font-bold hover:text-blue-400 transition-colors">
                        Create account
                    </Link>
                </p>
            </div>
        </div>
    );
}
