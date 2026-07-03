"use client"

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"

const data = [
  { name: "Operacional", value: 42, color: "var(--chart-1)" },
  { name: "Marketing", value: 24, color: "var(--chart-2)" },
  { name: "Folha", value: 20, color: "var(--chart-3)" },
  { name: "Outros", value: 14, color: "var(--chart-5)" },
]

export function CategoryBreakdown() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="text-lg font-semibold tracking-tight text-card-foreground">Despesas por categoria</h2>
      <p className="mt-1 text-sm text-muted-foreground">Distribuição do mês atual</p>

      <div className="relative mx-auto mt-4 h-44 w-44">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={58}
              outerRadius={80}
              paddingAngle={3}
              strokeWidth={0}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold text-card-foreground">R$ 96k</span>
          <span className="text-xs text-muted-foreground">Total</span>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {data.map((item) => (
          <div key={item.name} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.color }} />
              <span className="text-muted-foreground">{item.name}</span>
            </div>
            <span className="font-medium text-card-foreground">{item.value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
