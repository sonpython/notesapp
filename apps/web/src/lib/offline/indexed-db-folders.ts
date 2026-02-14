// IndexedDB operations for folders store
import { getDB } from "./indexed-db-client";
import type { Folder } from "@/lib/types";

export async function getAllFolders(): Promise<Folder[]> {
  const db = await getDB();
  return db.getAll("folders");
}

export async function getFolderById(id: string): Promise<Folder | undefined> {
  const db = await getDB();
  return db.get("folders", id);
}

export async function putFolder(folder: Folder): Promise<void> {
  const db = await getDB();
  await db.put("folders", folder);
}

export async function putManyFolders(folders: Folder[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction("folders", "readwrite");
  await Promise.all([
    ...folders.map((f) => tx.store.put(f)),
    tx.done,
  ]);
}

export async function deleteFolderLocal(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("folders", id);
}

export async function clearFolders(): Promise<void> {
  const db = await getDB();
  await db.clear("folders");
}
