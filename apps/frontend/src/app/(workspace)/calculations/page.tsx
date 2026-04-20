import { CalculationWorkbench } from "@/components/calculation-workbench";
import { PageIntro } from "@/components/page-intro";
import { appConfig } from "@/lib/config";

export default function CalculationsPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Quantitative workspace"
        title="Deterministic calculations"
        description="Run backend-backed dose conversions, margin of exposure calculations, and PDE/ADE shells with saved run outputs and structured warnings."
      />

      <CalculationWorkbench apiBaseUrl={appConfig.apiBaseUrl} />
    </div>
  );
}
