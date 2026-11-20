import { beforeEach, expect, it } from 'vitest'
import { migrateLegacyBrowserStorage } from './browserStorage'

beforeEach(() => window.localStorage.clear())

it('preserves the theme and unfinished invoice import when upgrading to EcoWatt', () => {
  window.localStorage.setItem('enerdiag-theme', 'dark')
  window.localStorage.setItem('enerdiag_invoice_import_id', '12')

  migrateLegacyBrowserStorage()
  migrateLegacyBrowserStorage()

  expect(window.localStorage.getItem('ecowatt-theme')).toBe('dark')
  expect(window.localStorage.getItem('ecowatt_invoice_import_id')).toBe('12')
  expect(window.localStorage.getItem('enerdiag-theme')).toBeNull()
  expect(window.localStorage.getItem('enerdiag_invoice_import_id')).toBeNull()
})

it('keeps newer EcoWatt values and removes legacy values so deleted imports cannot return', () => {
  window.localStorage.setItem('enerdiag-theme', 'dark')
  window.localStorage.setItem('ecowatt-theme', 'light')
  window.localStorage.setItem('enerdiag_invoice_import_id', '12')
  window.localStorage.setItem('ecowatt_invoice_import_id', '19')

  migrateLegacyBrowserStorage()

  expect(window.localStorage.getItem('ecowatt-theme')).toBe('light')
  expect(window.localStorage.getItem('ecowatt_invoice_import_id')).toBe('19')
  window.localStorage.removeItem('ecowatt_invoice_import_id')
  migrateLegacyBrowserStorage()
  expect(window.localStorage.getItem('ecowatt_invoice_import_id')).toBeNull()
})
