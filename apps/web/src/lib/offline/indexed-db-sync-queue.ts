// IndexedDB operations for sync queue store
import { getDB } from "./indexed-db-client";
import type { SyncQueueEntry } from "./offline-types";

export async function enqueue(entry: Omit<SyncQueueEntry, "id">): Promise<void> {
  const db = await getDB();
  await db.add("sync-queue", entry);
}

export async function getAllPending(): Promise<SyncQueueEntry[]> {
  const db = await getDB();
  return db.getAllFromIndex("sync-queue", "timestamp");
}

export async function dequeue(id: number): Promise<void> {
  const db = await getDB();
  await db.delete("sync-queue", id);
}

export async function updateRetryCount(
  id: number,
  count: number
): Promise<void> {
  const db = await getDB();
  const entry = await db.get("sync-queue", id);
  if (entry) {
    entry.retry_count = count;
    await db.put("sync-queue", entry);
  }
}

export async function clearQueue(): Promise<void> {
  const db = await getDB();
  await db.clear("sync-queue");
}
