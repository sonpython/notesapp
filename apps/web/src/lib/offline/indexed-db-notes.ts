// IndexedDB operations for notes store
import { getDB } from "./indexed-db-client";
import type { Note } from "@/lib/types";

export async function getAllNotes(): Promise<Note[]> {
  const db = await getDB();
  return db.getAll("notes");
}

export async function getNoteById(id: string): Promise<Note | undefined> {
  const db = await getDB();
  return db.get("notes", id);
}

export async function putNote(note: Note): Promise<void> {
  const db = await getDB();
  await db.put("notes", note);
}

export async function putManyNotes(notes: Note[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("notes", "readwrite");
  await Promise.all([
    ...notes.map((n) => tx.store.put(n)),
    tx.done,
  ]);
}

export async function deleteNoteLocal(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("notes", id);
}

export async function clearNotes(): Promise<void> {
  const db = await getDB();
  await db.clear("notes");
}
