// IndexedDB operations for todos store
import { getDB } from "./indexed-db-client";
import type { Todo } from '$lib/types';

export async function getAllTodos(): Promise<Todo[]> {
  const db = await getDB();
  return db.getAll("todos");
}

export async function getTodoById(id: string): Promise<Todo | undefined> {
  const db = await getDB();
  return db.get("todos", id);
}

export async function putTodo(todo: Todo): Promise<void> {
  const db = await getDB();
  await db.put("todos", todo);
}

export async function putManyTodos(todos: Todo[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("todos", "readwrite");
  await Promise.all([
    ...todos.map((t) => tx.store.put(t)),
    tx.done,
  ]);
}

export async function deleteTodoLocal(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("todos", id);
}

export async function clearTodos(): Promise<void> {
  const db = await getDB();
  await db.clear("todos");
}
