"use client"

import { useEffect, useState } from "react";
import NoteCard from "../components/NoteItem";

export default function Page() {
    const [notes,setNotes]=useState([])

    useEffect(()=>{
        const storedNotes=JSON.parse(localStorage.getItem("notesIndex"))

        if(storedNotes && storedNotes.length>0 ){
            setNotes(storedNotes)
        }
    },[])

    const deleteNote=(id)=>{
        setNotes((prev)=>prev.filter((note)=>note.id!=id))
    }

   

   return (<>
    {/* MAIN CONTENT ONLY — sidebar untouched */}
    <main className="flex-1 px-10 pt-1 pb-12">

      {/* Header pill */}
      <div className="flex justify-center mb-12">
        <div className="border border-gray-600 rounded-full px-10 py-2  text-white text-lg font-medium">
          Your Notes
        </div>
      </div>

      {/* Notes list container */}
      <div className="max-w-5xl mx-auto space-y-6">
        {notes.length === 0 ? (
          <p className="text-center text-gray-400">
            No notes generated yet.
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