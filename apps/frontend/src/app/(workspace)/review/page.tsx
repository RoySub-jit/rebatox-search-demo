import { CitationPanel } from "@/components/citation-panel";
import { InfoTable } from "@/components/info-table";
import { PageIntro } from "@/components/page-intro";
import { StatCard } from "@/components/stat-card";
import { StatusBadge } from "@/components/status-badge";
import {
  reviewCitations,
  reviewMetrics,
  reviewRows,
  reviewTasks,
} from "@/lib/demo-data";

const reviewColumns = [
  { key: "item", label: "Review item" },
  { key: "owner", label: "Owner" },
  { key: "decision", label: "Decision" },
  { key: "date", label: "Updated", align: "right" as const },
];

export default function ReviewPage() {
  return (
    <div className="page-stack">
      <PageIntro
        eyebrow="Expert review"
        title="Clinical, tox, and regulatory sign-off"
        description="Track open review tasks, current dispositions, and the exact evidence excerpts being used to support approval-facing judgments."
      />

      <section className="metric-grid">
        {reviewMetrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            hint={metric.hint}
            tone={metric.tone}
          />
        ))}
      </section>

      <section className="content-grid">
        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Decision board</span>
              <h2>Current review positions</h2>
            </div>
            <StatusBadge tone="success">2 of 3 leads aligned</StatusBadge>
          </div>
          <InfoTable columns={reviewColumns} rows={reviewRows} />
        </article>

        <article className="card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">Open work</span>
              <h2>Reviewer task list</h2>
            </div>
            <StatusBadge tone="warning">1 blocker</StatusBadge>
          </div>
          <div className="task-list">
            {reviewTasks.map((task) => (
              <div className="task-item" key={task.title}>
                <div className="task-item-top">
                  <h3>{task.title}</h3>
                  <StatusBadge tone={task.tone}>{task.badge}</StatusBadge>
                </div>
                <p>{task.body}</p>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">Supporting excerpts</span>
            <h2>Reviewer-ready citation packets</h2>
          </div>
          <StatusBadge tone="info">Expandable for meeting prep</StatusBadge>
        </div>
        <div className="citation-stack">
          {reviewCitations.map((citation) => (
            <CitationPanel key={citation.id} citation={citation} />
          ))}
        </div>
      </section>
    </div>
  );
}
