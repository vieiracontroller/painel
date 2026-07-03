import { cn } from "@/lib/utils"

const transactions = [
  { name: "Pagamento — Studio Alpha", date: "3 Jul, 14:22", amount: "+ R$ 12.400", type: "in" as const },
  { name: "Assinatura — Figma", date: "3 Jul, 09:10", amount: "- R$ 320", type: "out" as const },
  { name: "Pagamento — Loja Nova", date: "2 Jul, 18:45", amount: "+ R$ 8.900", type: "in" as const },
  { name: "Folha de pagamento", date: "1 Jul, 08:00", amount: "- R$ 42.000", type: "out" as const },
  { name: "Pagamento — Cliente Beta", date: "30 Jun, 16:30", amount: "+ R$ 5.600", type: "in" as const },
]

export function RecentTransactions() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-card-foreground">Transações recentes</h2>
          <p className="mt-1 text-sm text-muted-foreground">Últimas movimentações da conta</p>
        </div>
        <button className="text-sm font-medium text-primary hover:underline">Ver todas</button>
      </div>

      <div className="mt-4 divide-y divide-border">
        {transactions.map((tx) => (
          <div key={tx.name} className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium",
                  tx.type === "in" ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive",
                )}
              >
                {tx.type === "in" ? "↑" : "↓"}
              </span>
              <div>
                <p className="text-sm font-medium text-card-foreground">{tx.name}</p>
                <p className="text-xs text-muted-foreground">{tx.date}</p>
              </div>
            </div>
            <span
              className={cn(
                "text-sm font-medium",
                tx.type === "in" ? "text-primary" : "text-card-foreground",
              )}
            >
              {tx.amount}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
