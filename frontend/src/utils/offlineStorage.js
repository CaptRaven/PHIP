import { openDB } from 'idb';

const DB_NAME = 'phip-offline-db';
const STORE_NAME = 'pending-reports';

const dbPromise = openDB(DB_NAME, 1, {
  upgrade(db) {
    db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
  },
});

export const offlineStorage = {
  async saveReport(report) {
    const db = await dbPromise;
    return db.add(STORE_NAME, {
      ...report,
      createdAt: new Date().toISOString(),
      status: 'pending'
    });
  },

  async getPendingReports() {
    const db = await dbPromise;
    return db.getAll(STORE_NAME);
  },

  async deleteReport(id) {
    const db = await dbPromise;
    return db.delete(STORE_NAME, id);
  },

  async clearReports() {
    const db = await dbPromise;
    return db.clear(STORE_NAME);
  }
};
