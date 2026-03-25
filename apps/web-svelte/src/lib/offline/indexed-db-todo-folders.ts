// IndexedDB operations for todo_folders store
import { getDB } from "./indexed-db-client";
import type { TodoFolder } from '$lib/types';

export async function getAllTodoFolders(): Promise<TodoFolder[]> {
  const db = await getDB();
  return db.getAll("todo_folders");
}

export async function getTodoFolderById(id: string): Promise<TodoFolder | undefined> {
  const db = await getDB();
  return db.get("todo_folders", id);
}

export async function putTodoFolder(folder: TodoFolder): Promise<void> {
  const db = await getDB();
  await db.put("todo_folders", folder);
}

export async function putManyTodoFolders(folders: TodoFolder[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("todo_folders", "readwrite");
  await Promise.all([
    ...folders.map((f) => tx.store.put(f)),
    tx.done,
  ]);
}

export async function deleteTodoFolderLocal(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("todo_folders", id);
}
