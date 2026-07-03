"use client"

import { useState } from "react"
import {
  LayoutDashboard,
  Wallet,
  ArrowLeftRight,
  PieChart,
  Receipt,
  Users,
  Settings,
  LifeBuoy,
  TrendingUp,
} from "lucide-react"
import { cn } from "@/lib/utils"

const mainNav = [
  { label: "Visão geral", icon: LayoutDashboard, active: true },
  { label: "Carteiras", icon: Wallet },
  { label: "Transações", icon: ArrowLeftRight },
  { label: "Relatórios", icon: PieChart },
  { label: "Faturas", icon: Receipt },
  { label: "Clientes", icon: Users },
]

const secondaryNav = [
  { label: "Configurações", icon: Settings },
  { label: "Suporte", icon: LifeBuoy },
]

export function Sidebar() {
  const [active, setActive] = useState("Visão geral")

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <TrendingUp className="h-5 w-5" />
        </div>
        <span className="text-lg font-semibold tracking-tight text-sidebar-foreground">Vieira</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-4">
        <p className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Menu</p>
        {mainNav.map((item) => {
          const Icon = item.icon
          const isActive = active === item.label
          return (
            <button
              key={item.label}
              onClick={() => setActive(item.label)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {item.label}
            </button>
          )
        })}

        <p className="mt-4 px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Sistema</p>
        {secondaryNav.map((item) => {
          const Icon = item.icon
          const isActive = active === item.label
          return (
            <button
              key={item.label}
              onClick={() => setActive(item.label)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {item.label}
            </button>
          )
        })}
      </nav>

      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary text-sm font-medium text-secondary-foreground">
            RV
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-sidebar-foreground">Rafael Vieira</p>
            <p className="truncate text-xs text-muted-foreground">admin@vieira.com</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
