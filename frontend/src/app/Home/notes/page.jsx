"use client"

import { useEffect, useState } from "react";
import NoteCard from "../components/NoteItem";
import { getUserNotes } from "@/lib/api_call";

export default function Page() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchNotes() {
      try {
        setLoading(true);
        const userNotes = await getUserNotes();
        setNotes(userNotes);
      } catch (err) {
        console.error("Failed to fetch notes:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchNotes();
  }, []);

  const deleteNote = async (id) => {
    // TODO: Add backend DELETE endpoint
    const updatedNotes = notes.filter((note) => note.id !== id);
    setNotes(updatedNotes);
  };

  return (
    <>
      {/* MAIN CONTENT ONLY — sidebar untouched */}
      <main className="flex-1 px-10 pt-1 pb-12">
        {/* Header pill */}
        <div className="flex justify-center mb-12">
          <div className="border border-gray-600 rounded-full px-10 py-2 text-white text-lg font-medium">
            Your Notes
          </div>
        </div>

        {/* Notes list container */}
        <div className="max-w-5xl mx-auto space-y-6">
          {loading ? (
            <p className="text-center text-gray-400">Loading your notes...</p>
          ) : error ? (
            <p className="text-center text-red-400">Error: {error}</p>
          ) : notes.length === 0 ? (
            <p className="text-center text-gray-400">
              No notes found. Start by generating notes from the search page!
            </p>
          ) : (
            notes.map((note) => (
              <NoteCard
                key={note.id}
                note={note}
                onDelete={deleteNote}
              />
            ))
          )}
        </div>
      </main>
    </>
  );
}