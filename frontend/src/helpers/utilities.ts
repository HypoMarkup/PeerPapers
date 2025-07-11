export function isLocalStorageEmpty(key: string): boolean {
  return localStorage[key] === undefined || localStorage[key].length === 0;
}

export function resetClient() {
  localStorage.clear();
  location.reload();
}
