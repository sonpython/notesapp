// IndexedDB offline storage types

export type EntityType = "note" | "todo" | "folder";
export type SyncOperation = "create" | "update" | "delete";

export interface SyncQueueEntry {
  id?: number; // auto-incremented
  entity_type: EntityType;
  operation: SyncOperation;
  entity_id: string;
  payload: Record<string, unknown> | null;
  timestamp: number;
  retry_count: number;
}

export interface MetaEntry {
  key: string;
  value: string | number;
}
