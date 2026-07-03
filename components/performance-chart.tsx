"use client"

import { useState } from "react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { cn } from "@/lib/utils"

const data = [
  { month: "Jan", receita: 42000, despesa: 24000 },
  { month: "Fev", receita: 38000, despesa: 21000 },
  { month: "Mar", receita: 51000, despesa: 28000 },
  { month: "Abr", receita: 47000, despesa: 26000 },
  { month: "Mai", receita: 62000, despesa: 31000 },
  { month: "Jun", receita: 58000, despesa: 29000 },
  { month: "Jul", receita: 71000, despesa: 34000 },
  { month: "Ago", receita: 69000, despesa: 33000 },
  { month: "Set", receita: 78000, despesa: 38000 },
  { month: "Out", receita: 84000, despesa: 41000 },
  { month: "Nov", receita: 91000, despesa: 44000 },
  { month: "Dez", receita: 98000, despesa: 47000 },
]

const ranges = ["30 dias", "6 meses", "12 meses"]

function formatBRL(value: number) {
  return `R$ ${(value / 1000).toFixed(0)}k`
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-border bg-popover p-3 shadow-xl">
      <p className="mb-2 text-xs font-medium text-muted-foreground">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="capitalize text-popover-foreground">{entry.dataKey}:</span>
          <span className="font-medium text-popover-foreground">
            R$ {entry.value.toLocaleString("pt-BR")}
          </span>
        </div>
      ))}
    </div>
  )
}

export function PerformanceChart() {
  const [range, setRange] = useState("12 meses")

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-card-foreground">Desempenho financeiro</h2>
          <p className="mt-1 text-sm text-muted-foreground">Receita e despesas ao longo do período</p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-border bg-secondary p-1">
          {ranges.map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                range === r
                  ? "bg-card text-card-foreground shadow-sm"
                  : "text-muted-foreground hover:text-card-foreground",
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-chart-1" />
          <span className="text-sm text-muted-foreground">Receita</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-chart-2" />
          <span className="text-sm text-muted-foreground">Despesas</span>
        </div>
      </div>

      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 8, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="fillReceita" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.35} />
                <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="fillDespesa" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--chart-2)" stopOpacity={0.25} />
                <stop offset="95%" stopColor="var(--chart-2)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="month"
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="var(--muted-foreground)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatBRL}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "var(--border)" }} />
            <Area
              type="monotone"
              dataKey="receita"
              stroke="var(--chart-1)"
              strokeWidth={2}
              fill="url(#fillReceita)"
            />
            <Area
              type="monotone"
              dataKey="despesa"
              stroke="var(--chart-2)"
              strokeWidth={2}
              fill="url(#fillDespesa)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
