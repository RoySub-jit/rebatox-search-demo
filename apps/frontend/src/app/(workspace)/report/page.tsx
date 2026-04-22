import { ReportReviewWorkspace } from "@/components/report-review-workspace";
import { StatusBadge } from "@/components/status-badge";
import { ApiClientError, getProductReport } from "@/lib/api";
import { appConfig } from "@/lib/config";

type ReportPageProps = {
  searchParams?: Promise<{
    productId?: string | string[];
  }>;
};

function parseProductId(input: string | string[] | undefined): number {
  const value = Array.isArray(input) ? input[0] : input;
  const parsed = Number(value ?? "1");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : Number.NaN;
}

function describeLoadError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to load the report review workspace.";
}

export default async function ReportPage({ searchParams }: ReportPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const productId = parseProductId(resolvedSearchParams.productId);

  if (!Number.isFinite(productId)) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">RebaTox reviewer workspace</span>
              <h2>Invalid product id</h2>
            </div>
            <StatusBadge tone="danger">Input error</StatusBadge>
          </div>
          <p>
            Use a positive numeric <code>productId</code> query parameter, such as{" "}
            <code>/report?productId=1</code>.
          </p>
        </section>
      </div>
    );
  }

  try {
    const report = await getProductReport(appConfig.apiBaseUrl, productId);
    return <ReportReviewWorkspace productId={productId} report={report} />;
  } catch (error) {
    return (
      <div className="page-stack">
        <section className="card feedback-banner danger">
          <div className="card-heading">
            <div>
              <span className="section-kicker">RebaTox reviewer workspace</span>
              <h2>Report unavailable</h2>
            </div>
            <StatusBadge tone="danger">API issue</StatusBadge>
          </div>
          <p>{describeLoadError(error)}</p>
          <p>
            Confirm the backend is running and that product <code>{productId}</code>{" "}
            exists before reopening this page.
          </p>
        </section>
      </div>
    );
  }
}
