import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { InvoiceUploadPage } from './InvoiceUploadPage'
import { setAuthToken } from '../services/api/client'

const account = { email: 'ana@example.com', profile: { company_name: 'Empresa Exemplo', distributor_id: 9, address_details: 'Rua da Energia, 10', substation_same_address: true } }
const distributors = [{ id: 9, name: 'ENEL SP', state: 'SP' }]
const savedInvoice = (month: string, warnings: string[] = []) => ({ id: Number(month.slice(5)), reference_month: month, consumer_unit: '123456789', total_paid: '1000.00', warnings, items: [], source_filename: `${month}.pdf` })
const session = (months: string[] = []) => ({ id: 12, status: 'draft', invoice_count: months.length, invoices: months.map((month) => savedInvoice(month)) })
const json = (status: number, payload: unknown) => new Response(JSON.stringify(payload), { status, headers: { 'Content-Type': 'application/json' } })
const pdf = (name: string) => new File(['%PDF-1.4\n/Type /Page'], name, { type: 'application/pdf' })

function setupFetch(handler?: (url: string, options?: RequestInit) => Response | Promise<Response>) {
  const fetchMock = vi.fn((url: string, options?: RequestInit) => {
    if (url.endsWith('/me')) return Promise.resolve(json(200, { data: account }))
    if (url.endsWith('/distributors')) return Promise.resolve(json(200, { data: distributors }))
    if (url.endsWith('/invoice-imports')) return Promise.resolve(json(201, { data: { id: 12, status: 'draft' } }))
    return Promise.resolve(handler?.(url, options) ?? json(500, { message: 'Resposta não configurada.' }))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

async function startImport() {
  render(<InvoiceUploadPage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Começar envio' }))
  return screen.findByLabelText(/Selecionar faturas/)
}

beforeEach(() => {
  window.localStorage.clear()
  window.history.replaceState({}, '', '/upload-faturas')
  setAuthToken('customer-token')
})
afterEach(() => {
  vi.unstubAllGlobals()
  setAuthToken(null)
  window.localStorage.clear()
})

describe('sequential invoice import', () => {
  it('keeps the import identifier when the review link requires login', async () => {
    setAuthToken(null)
    window.history.replaceState({}, '', '/upload-faturas?import=12')
    const fetchMock = setupFetch()
    render(<InvoiceUploadPage />)
    await waitFor(() => expect(window.location.pathname).toBe('/login'))
    expect(window.localStorage.getItem('ecowatt_invoice_import_id')).toBe('12')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('removes a draft invoice and updates the review table before allowing a replacement', async () => {
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    const fetchMock = setupFetch((url, options) => json(200, { data: session(url.endsWith('/invoices/3') && options?.method === 'DELETE' ? [] : ['2026-03']) }))
    render(<InvoiceUploadPage />)
    const summaryTable = await screen.findByRole('region', { name: 'Resumo das faturas salvas' })
    fireEvent.click(within(summaryTable).getByRole('button', { name: 'Remover fatura de 03/2026' }))
    await screen.findByText('0 de 12 faturas lidas e salvas')
    expect(screen.getByRole('button', { name: 'Envie ao menos uma fatura' })).toBeDisabled()
    expect(fetchMock.mock.calls.some(([url, options]) => url.endsWith('/invoices/3') && options?.method === 'DELETE')).toBe(true)
  })

  it('lists all twelve selected files immediately while the first invoice is still being read', async () => {
    let finishFirst!: (response: Response) => void
    const first = new Promise<Response>((resolve) => { finishFirst = resolve })
    const months = Array.from({ length: 12 }, (_, index) => `2026-${String(index + 1).padStart(2, '0')}`)
    let requests = 0
    setupFetch(() => ++requests === 1 ? first : json(201, { data: session(months.slice(0, requests)) }))
    const picker = await startImport()

    fireEvent.change(picker, { target: { files: months.map((month) => pdf(`${month}.pdf`)) } })

    const queue = await screen.findByRole('region', { name: 'Arquivos selecionados' })
    expect(within(queue).getAllByRole('listitem')).toHaveLength(12)
    expect(within(queue).getByRole('button', { name: 'Retirar 2026-01.pdf da seleção' })).toBeDisabled()
    expect(within(queue).getByRole('button', { name: 'Retirar 2026-12.pdf da seleção' })).toBeEnabled()
    expect(screen.queryByText(/Nenhuma fatura salva. Selecione/)).not.toBeInTheDocument()
    await waitFor(() => expect(requests).toBe(1))
    await act(async () => { finishFirst(json(201, { data: session([months[0]!]) })) })
    // Wait for the whole batch, including twelve FileReader callbacks and review-table renders.
    await screen.findByText('12 de 12 faturas lidas e salvas', {}, { timeout: 5000 })
    expect(screen.queryByRole('region', { name: 'Arquivos selecionados' })).not.toBeInTheDocument()
  })

  it('shows the cumulative summary when reopening a saved import without uploading again', async () => {
    const months = Array.from({ length: 12 }, (_, index) => `2026-${String(index + 1).padStart(2, '0')}`)
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    const fetchMock = setupFetch(() => json(200, { data: session(months) }))
    render(<InvoiceUploadPage />)

    await screen.findByText('Você já enviou 12 faturas no total. Todas foram lidas e salvas. A lista está organizada pelo mês da medição.')
    expect(fetchMock.mock.calls.filter(([url, options]) => url.endsWith('/invoices') && options?.method === 'POST')).toHaveLength(0)
  })

  it('reports all twelve saved invoices after adding six files to a resumed import', async () => {
    const months = Array.from({ length: 12 }, (_, index) => `2026-${String(index + 1).padStart(2, '0')}`)
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    let uploads = 0
    setupFetch((url) => url.endsWith('/invoices')
      ? json(201, { data: session(months.slice(0, 6 + ++uploads)) })
      : json(200, { data: session(months.slice(0, 6)) }))
    render(<InvoiceUploadPage />)
    const picker = await screen.findByLabelText(/Selecionar faturas/)
    await screen.findByText('6 de 12 faturas lidas e salvas')

    fireEvent.change(picker, { target: { files: months.slice(6).map((month) => pdf(`${month}.pdf`)) } })

    await screen.findByText('Você já enviou 12 faturas no total. Todas foram lidas e salvas. A lista está organizada pelo mês da medição.', {}, { timeout: 5000 })
    expect(uploads).toBe(6)
    expect(screen.getByText('12 de 12 faturas lidas e salvas')).toBeInTheDocument()
    expect(screen.queryByLabelText(/Selecionar faturas/)).not.toBeInTheDocument()
  })

  it('counts only saved invoices in the total when an additional file is rejected', async () => {
    const months = Array.from({ length: 7 }, (_, index) => `2026-${String(index + 1).padStart(2, '0')}`)
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    let uploads = 0
    setupFetch((url) => {
      if (!url.endsWith('/invoices')) return json(200, { data: session(months.slice(0, 6)) })
      uploads++
      return uploads === 1
        ? json(422, { message: 'Fatura repetida.', errors: { invoice: ['Esta fatura já foi enviada.'] } })
        : json(201, { data: session(months) })
    })
    render(<InvoiceUploadPage />)
    const picker = await screen.findByLabelText(/Selecionar faturas/)

    fireEvent.change(picker, { target: { files: [pdf('duplicate.pdf'), pdf('july.pdf')] } })

    await screen.findByText('Você já enviou 7 faturas no total. Todas foram lidas e salvas. A lista está organizada pelo mês da medição.')
    expect(uploads).toBe(2)
    expect(screen.getByText('7 de 12 faturas lidas e salvas')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('duplicate.pdf: Esta fatura já foi enviada.')
  })

  it('does not upload a pending file removed while another file is being read', async () => {
    let finishFirst!: (response: Response) => void
    const first = new Promise<Response>((resolve) => { finishFirst = resolve })
    let requests = 0
    const fetchMock = setupFetch(() => ++requests === 1 ? first : json(201, { data: session(['2026-01', '2026-03']) }))
    const picker = await startImport()
    fireEvent.change(picker, { target: { files: [pdf('january.pdf'), pdf('february.pdf'), pdf('march.pdf')] } })
    await waitFor(() => expect(requests).toBe(1))

    fireEvent.click(screen.getByRole('button', { name: 'Retirar february.pdf da seleção' }))
    await act(async () => { finishFirst(json(201, { data: session(['2026-01']) })) })

    await screen.findByText('2 de 12 faturas lidas e salvas')
    const uploads = fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))
    expect(uploads.map(([, options]) => ((options?.body as FormData).get('invoice') as File).name)).toEqual(['january.pdf', 'march.pdf'])
  })

  it('sends one PDF per request and waits for each invoice to be saved before sending the next', async () => {
    let finishFirst!: (response: Response) => void
    const first = new Promise<Response>((resolve) => { finishFirst = resolve })
    let finishSecond!: (response: Response) => void
    const second = new Promise<Response>((resolve) => { finishSecond = resolve })
    let requests = 0
    const fetchMock = setupFetch((url) => {
      if (url.endsWith('/invoices')) {
        requests++
        return requests === 1 ? first : second
      }
      return json(500, {})
    })
    const picker = await startImport()
    expect(picker).toHaveAttribute('multiple')
    fireEvent.change(picker, { target: { files: [pdf('april.pdf'), pdf('march.pdf')] } })
    await waitFor(() => expect(requests).toBe(1))
    expect(screen.getByRole('button', { name: 'Aguarde…' })).toBeDisabled()
    await act(async () => { finishFirst(json(201, { data: session(['2026-04']) })) })
    await screen.findByText('1 de 12 faturas lidas e salvas')
    expect(within(screen.getByRole('region', { name: 'Resumo das faturas salvas' })).getByText('2026-04.pdf')).toBeInTheDocument()
    await waitFor(() => expect(requests).toBe(2))
    await act(async () => { finishSecond(json(201, { data: session(['2026-03', '2026-04']) })) })
    await screen.findByText('2 de 12 faturas lidas e salvas')
    const uploads = fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))
    expect(uploads).toHaveLength(2)
    expect(uploads.map(([, options]) => (options?.body as FormData).getAll('invoice').length)).toEqual([1, 1])
    expect(uploads.map(([, options]) => ((options?.body as FormData).get('invoice') as File).name)).toEqual(['april.pdf', 'march.pdf'])
    const rows = within(screen.getByRole('table', { name: 'Faturas em ordem do mês da medição' })).getAllByRole('row')
    expect(rows[1]).toHaveTextContent('03/2026')
    expect(rows[2]).toHaveTextContent('04/2026')
  })

  it('continues with the next file after a duplicate is rejected and keeps the saved table', async () => {
    let requests = 0
    let finishSecond!: (response: Response) => void
    const second = new Promise<Response>((resolve) => { finishSecond = resolve })
    setupFetch(() => ++requests === 1
      ? json(422, { message: 'Fatura repetida.', errors: { invoice: ['Esta fatura já foi enviada.'] } })
      : second)
    const picker = await startImport()
    fireEvent.change(picker, { target: { files: [pdf('duplicate.pdf'), pdf('april.pdf')] } })
    expect(await screen.findByRole('alert')).toHaveTextContent('duplicate.pdf: Esta fatura já foi enviada.')
    expect(screen.getByText('0 de 12 faturas lidas e salvas')).toBeInTheDocument()
    await waitFor(() => expect(requests).toBe(2))
    await act(async () => { finishSecond(json(201, { data: session(['2026-04']) })) })
    await screen.findByText('1 de 12 faturas lidas e salvas')
    expect(screen.getByRole('alert')).toHaveTextContent('duplicate.pdf: Esta fatura já foi enviada.')
    expect(screen.getByRole('status')).toHaveTextContent('Você já enviou 1 fatura no total. Ela foi lida e salva.')
    expect(screen.getByRole('button', { name: 'Simular relatório' })).toBeEnabled()
  })

  it('blocks calculation before the first invoice and starts it only after a saved invoice', async () => {
    const fetchMock = setupFetch((url) => url.endsWith('/invoices')
      ? json(201, { data: session(['2026-03']) })
      : json(url.endsWith('/complete') ? 202 : 200, { data: { id: 12, status: 'completed', processing_errors: null } }))
    const picker = await startImport()
    expect(screen.getByRole('button', { name: 'Envie ao menos uma fatura' })).toBeDisabled()
    fireEvent.change(picker, { target: { files: [pdf('march.pdf')] } })
    fireEvent.click(await screen.findByRole('button', { name: 'Simular relatório' }))
    expect(await screen.findByRole('link', { name: 'Ver relatório completo' })).toHaveAttribute('href', '/simulations/12/report')
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/complete'))).toHaveLength(1)
  })

  it('restores a saved draft from its link and blocks a table whose items do not reconcile', async () => {
    window.history.replaceState({}, '', '/upload-faturas?import=12')
    setupFetch(() => json(200, { data: { ...session(['2026-03']), invoices: [savedInvoice('2026-03', ['invoice_billing_total_mismatch'])] } }))
    render(<InvoiceUploadPage />)
    expect(await screen.findByRole('button', { name: 'Simular relatório' })).toBeDisabled()
    expect(screen.getByRole('alert')).toHaveTextContent('A leitura precisa ser revisada')
    expect(screen.getByRole('alert')).toHaveTextContent('03/2026 · 2026-03.pdf')
    expect(screen.getByRole('alert')).toHaveTextContent('Encargos de bandeira tarifária ou outros ajustes podem explicar a diferença')
    expect(window.localStorage.getItem('ecowatt_invoice_import_id')).toBe('12')
  })

  it('limits a resumed import to twelve saved invoices', async () => {
    const months = Array.from({ length: 11 }, (_, index) => `2026-${String(index + 1).padStart(2, '0')}`)
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    const fetchMock = setupFetch((url) => json(url.endsWith('/invoices') ? 201 : 200, { data: session(url.endsWith('/invoices') ? [...months, '2026-12'] : months) }))
    render(<InvoiceUploadPage />)
    fireEvent.change(await screen.findByLabelText(/Selecionar faturas/), { target: { files: [pdf('december.pdf'), pdf('extra.pdf')] } })
    await screen.findByText('12 de 12 faturas lidas e salvas')
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))).toHaveLength(1)
    expect(screen.queryByLabelText(/Selecionar faturas/)).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('O limite é de 12 faturas')
  })

  it.each([
    [new File(['text'], 'invalid.txt', { type: 'text/plain' }), 'selecione um arquivo PDF'],
    [new File(['text'], 'invalid.pdf', { type: 'application/pdf' }), 'o conteúdo não é um PDF, PNG ou JPEG válido'],
    [new File([new Uint8Array(20 * 1024 * 1024 + 1)], 'large.pdf', { type: 'application/pdf' }), 'cada fatura pode ter no máximo 20 MB'],
  ])('rejects invalid uploads without sending them: %s', async (file, message) => {
    const fetchMock = setupFetch()
    const picker = await startImport()
    fireEvent.change(picker, { target: { files: [file] } })
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))).toHaveLength(0)
  })

  it.each([
    ['invoice.png', 'image/png', new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10])],
    ['invoice.jpeg', 'image/jpeg', new Uint8Array([255, 216, 255, 224])],
  ])('sends supported image %s for backend validation and OCR', async (name, type, bytes) => {
    const fetchMock = setupFetch(() => json(201, { data: session(['2026-01']) }))
    const picker = await startImport()
    expect(picker).toHaveAttribute('accept', 'application/pdf,image/png,image/jpeg,.pdf,.png,.jpg,.jpeg')
    fireEvent.change(picker, { target: { files: [new File([bytes], name, { type })] } })
    await screen.findByText('1 de 12 faturas lidas e salvas')
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))).toHaveLength(1)
  })

  it('keeps the current draft when the file picker is canceled', async () => {
    const fetchMock = setupFetch()
    const picker = await startImport()
    fireEvent.change(picker, { target: { files: [] } })
    expect(screen.getByText('0 de 12 faturas lidas e salvas')).toBeInTheDocument()
    expect(fetchMock.mock.calls.filter(([url]) => url.endsWith('/invoices'))).toHaveLength(0)
  })

  it('shows asynchronous processing failures', async () => {
    window.localStorage.setItem('ecowatt_invoice_import_id', '12')
    setupFetch((url) => json(200, { data: url.endsWith('/status')
      ? { id: 12, status: 'failed', processing_errors: [{ file: 'simulação', code: 'FAILED', errors: { message: 'Falha no cálculo.' } }] }
      : { ...session(['2026-03']), status: 'queued' } }))
    render(<InvoiceUploadPage />)
    await screen.findByRole('heading', { name: 'A análise precisa de atenção' })
    expect(await screen.findByText('Falha no cálculo.')).toBeInTheDocument()
  })

  it('registers interest in an unsupported distributor', async () => {
    const fetchMock = setupFetch(() => json(201, {}))
    render(<InvoiceUploadPage />)
    fireEvent.change(await screen.findByLabelText('Distribuidora'), { target: { value: 'other' } })
    fireEvent.change(screen.getByLabelText('Nome da distribuidora'), { target: { value: 'Nova Distribuidora' } })
    fireEvent.click(screen.getByRole('button', { name: 'Registrar meu interesse' }))
    await screen.findByText(/Interesse registrado/)
    expect(fetchMock.mock.calls.some(([url]) => url.endsWith('/leads'))).toBe(true)
  })
})
