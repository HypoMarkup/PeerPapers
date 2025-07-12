export function isLocalStorageEmpty(key: string): boolean {
  return localStorage[key] === undefined || localStorage[key].length === 0;
}

export function resetClient() {
  localStorage.clear();
  location.reload();
}

export function getBase64(file: File) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
}
