import { Bell, Search, Plus } from "lucide-react"

export function Header() {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-background/80 px-4 backdrop-blur md:px-8">
      <div>
        <h1 className="text-base font-semibold tracking-tight text-foreground md:text-lg">Visão geral</h1>
        <p className="hidden text-xs text-muted-foreground sm:block">Bem-vindo de volta, Rafael</p>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        <div className="relative hidden lg:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar..."
            className="h-9 w-56 rounded-lg border border-border bg-card pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
          />
        </div>

        <button
          aria-label="Notificações"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground transition-colors hover:text-foreground"
        >
          <Bell className="h-[18px] w-[18px]" />
          <span className="absolute right-2.5 top-2.5 h-1.5 w-1.5 rounded-full bg-primary" />
        </button>

        <button className="flex h-9 items-center gap-2 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90">
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Nova transação</span>
        </button>
      </div>
    </header>
  )
}
