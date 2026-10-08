import DashboardPage, { type DashboardPageProps } from "../../../dashboard/page";

export const dynamic = "force-dynamic";

export default function WorkspaceDashboardPage({ searchParams }: DashboardPageProps) {
  return <DashboardPage searchParams={searchParams} pwaMode />;
}