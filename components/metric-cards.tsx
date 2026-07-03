import { ArrowDownRight, ArrowUpRight, DollarSign, CreditCard, Users, Activity } from "lucide-react"
import { cn } from "@/lib/utils"

const metrics = [
  {
    label: "Receita total",
    value: "R$ 284.560",
    change: "+12,5%",
    trend: "up" as const,
    icon: DollarSign,
  },
  {
    label: "Despesas",
    value: "R$ 96.240",
    change: "-3,2%",
    trend: "down" as const,
    icon: CreditCard,
  },
  {
    label: "Novos clientes",
    value: "1.284",
    change: "+8,1%",
    trend: "up" as const,
    icon: Users,
  },
  {
    label: "Taxa de conversão",
    value: "24,8%",
    change: "+2,4%",
    trend: "up" as const,
    icon: Activity,
  },
]

export function MetricCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon
        const positive = metric.trend === "up"
        return (
          <div
            key={metric.label}
            className="rounded-xl border border-border bg-card p-5 transition-colors hover:border-primary/40"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
                <Icon className="h-5 w-5" />
              </div>
              <span
                className={cn(
                  "flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium",
                  positive ? "bg-primary/10 text-primary" : "bg-destructive/10 text-destructive",
                )}
              >
                {positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                {metric.change}
              </span>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">{metric.label}</p>
            <p className="mt-1 text-2xl font-semibold tracking-tight text-card-foreground">{metric.value}</p>
          </div>
        )
      })}
    </div>
  )
}
