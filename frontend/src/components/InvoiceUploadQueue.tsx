export type QueuedInvoice = {
  id: number
  file: File
  status: 'pending' | 'reading' | 'error'
  error?: string
}

export function InvoiceUploadQueue({ entries, onRemove }: { entries: QueuedInvoice[]; onRemove: (id: number) => void }) {
  if (entries.length === 0) return null

  return <section className="invoice-upload-queue" aria-labelledby="invoice-upload-queue-title">
    <h2 id="invoice-upload-queue-title">Arquivos selecionados</h2>
    <p>As faturas salvas aparecem na tabela de conferência. Você pode retirar os arquivos que ainda aguardam leitura.</p>
    <ul aria-label="Andamento dos arquivos selecionados">
      {entries.map((entry) => <li key={entry.id}>
        <div className="invoice-upload-file"><strong>{entry.file.name}</strong><span className={entry.status === 'error' ? 'field-error' : 'invoice-upload-status'}>{entry.status === 'pending' ? 'Aguardando leitura' : entry.status === 'reading' ? 'Lendo e salvando…' : 'Não foi salva'}</span></div>
        <button className="invoice-remove-button" type="button" disabled={entry.status === 'reading'} onClick={() => onRemove(entry.id)} aria-label={`Retirar ${entry.file.name} da seleção`}>Retirar arquivo</button>
        {entry.error && <p className="field-error" role="alert">{entry.file.name}: {entry.error}</p>}
      </li>)}
    </ul>
  </section>
}
