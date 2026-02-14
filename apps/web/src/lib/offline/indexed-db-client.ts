// IndexedDB client for offline storage
import { openDB, type IDBPDatabase } from "idb";
import type { MetaEntry } from "./offline-types";

const DB_NAME = "notesapp-offline";
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase> | null = null;

export function getDB(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Notes store
        if (!db.objectStoreNames.contains("notes")) {
          const notesStore = db.createObjectStore("notes", { keyPath: "id" });
          notesStore.createIndex("updated_at", "updated_at");
          notesStore.createIndex("folder_id", "folder_id");
          notesStore.createIndex("is_archived", "is_archived");
        }

        // Todos store
        if (!db.objectStoreNames.contains("todos")) {
          const todosStore = db.createObjectStore("todos", { keyPath: "id" });
          todosStore.createIndex("updated_at", "updated_at");
          todosStore.createIndex("is_completed", "is_completed");
          todosStore.createIndex("parent_id", "parent_id");
        }

        // Folders store
        if (!db.objectStoreNames.contains("folders")) {
          const foldersStore = db.createObjectStore("folders", { keyPath: "id" });
          foldersStore.createIndex("updated_at", "updated_at");
          foldersStore.createIndex("parent_id", "parent_id");
        }

        // Sync queue
        if (!db.objectStoreNames.contains("sync-queue")) {
          const queueStore = db.createObjectStore("sync-queue", {
            keyPath: "id",
            autoIncrement: true,
          });
          queueStore.createIndex("timestamp", "timestamp");
          queueStore.createIndex("entity_type", "entity_type");
        }

        // Meta (last sync times, etc.)
        if (!db.objectStoreNames.contains("meta")) {
          db.createObjectStore("meta", { keyPath: "key" });
        }
      },
    });
  }
  return dbPromise;
}

export async function clearAllStores(): Promise<void> {
  const db = await getDB();
  const tx = db.transaction(
    ["notes", "todos", "folders", "sync-queue", "meta"],
    "readwrite"
  );
  await Promise.all([
    tx.objectStore("notes").clear(),
    tx.objectStore("todos").clear(),
    tx.objectStore("folders").clear(),
    tx.objectStore("sync-queue").clear(),
    tx.objectStore("meta").clear(),
    tx.done,
  ]);
}

// Meta helpers
export async function setMeta(key: string, value: string | number): Promise<void> {
  const db = await getDB();
  await db.put("meta", { key, value } as MetaEntry);
}

export async function getMeta(key: string): Promise<string | number | undefined> {
  const db = await getDB();
  const entry = await db.get("meta", key);
  return entry?.value;
}
