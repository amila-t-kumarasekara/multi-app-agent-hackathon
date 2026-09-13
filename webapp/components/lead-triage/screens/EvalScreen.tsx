"use client";

import { api, type ApiEvalSummary } from "@/lib/api";
import { useApiData } from "../hooks/useApiData";
import { StatCard } from "../ui/StatCard";
import { StatusTag } from "../ui/StatusTag";

export function EvalScreen() {
  const { data, loading, error } = useApiData<ApiEvalSummary | null>(api.getEvalSummary, 10000);

  if (error) {
    return <div className="ltc-listcard"><div className="ltc-empty">Couldn&apos;t load eval results: {error}</div></div>;
  }
  if (loading && data === null) {
    return <div className="ltc-listcard"><div className="ltc-empty">Loading eval results…</div></div>;
  }
  if (!data) {
    return (
      <div className="ltc-listcard">
        <div className="ltc-empty">
          No eval runs recorded yet. Run <code>python -m evals.run_evals</code> on the server to populate this screen.
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="ltc-stats">
        {data.metrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            trend={metric.trend}
            up={metric.up}
            valueMarginTop
          />
        ))}
      </div>

      <div className="ltc-listcard ltc-tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>Test case</th>
              <th>Category</th>
              <th>Result</th>
              <th>Latency</th>
            </tr>
          </thead>
          <tbody>
            {data.cases.map((testCase) => (
              <tr key={testCase.name}>
                <td>{testCase.name}</td>
                <td className="text-muted">{testCase.category}</td>
                <td>
                  <StatusTag
                    label={testCase.result}
                    tagClass={
                      testCase.result === "Pass" ? "tag-accent-2" : "tag-outline"
                    }
                  />
                </td>
                <td className="text-muted">{testCase.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
