import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { MetricCards } from "@/components/metric-cards"
import { PerformanceChart } from "@/components/performance-chart"
import { CategoryBreakdown } from "@/components/category-breakdown"
import { RecentTransactions } from "@/components/recent-transactions"

export default function DashboardPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-6">
            <MetricCards />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <PerformanceChart />
              </div>
              <div>
                <CategoryBreakdown />
              </div>
            </div>

            <RecentTransactions />
          </div>
        </main>
      </div>
    </div>
  )
}
