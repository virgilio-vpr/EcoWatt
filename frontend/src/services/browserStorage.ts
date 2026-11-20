export function migrateLegacyBrowserStorage() {
  const keys = [
    ['enerdiag-theme', 'ecowatt-theme'],
    ['enerdiag_invoice_import_id', 'ecowatt_invoice_import_id'],
  ] as const

  for (const [legacyKey, currentKey] of keys) {
    const legacyValue = window.localStorage.getItem(legacyKey)
    if (legacyValue === null) continue
    if (window.localStorage.getItem(currentKey) === null) {
      window.localStorage.setItem(currentKey, legacyValue)
    }
    window.localStorage.removeItem(legacyKey)
  }
}
