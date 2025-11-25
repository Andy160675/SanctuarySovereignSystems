const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  searchTruth: (query) => ipcRenderer.invoke('search-truth', query),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  showSaveDialog: () => ipcRenderer.invoke('show-save-dialog'),
  
  // System info
  platform: process.platform,
  version: process.versions.electron
})